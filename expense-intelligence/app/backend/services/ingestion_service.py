"""
Secure expense ingestion and validation service.

Parses, sanitizes, and normalizes untrusted expense CSV data into a canonical structure.
Never logs raw transaction records or executes untrusted payload content.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
import re
from datetime import date, datetime
from typing import Any

from app.backend.core.config import Settings, get_settings
from app.backend.core.exceptions import ValidationError
from app.backend.core.logging import get_logger
from app.backend.schemas.expense import (
    DateRange,
    ExpenseIngestionResponse,
    NormalizedExpense,
    RowValidationError,
)

logger = get_logger("app.backend.services.ingestion")

# ── Explicit Column Mapping Definitions ────────────────────────────────────────
# Maps canonical names to sets of known acceptable column header aliases.
CANONICAL_COLUMN_ALIASES: dict[str, set[str]] = {
    "date": {
        "date",
        "transaction_date",
        "tx_date",
        "posted_date",
        "trans_date",
        "timestamp",
        "date_time",
        "posting_date",
        "txn_date",
    },
    "description": {
        "description",
        "desc",
        "merchant",
        "merchant_details",
        "details",
        "narrative",
        "memo",
        "name",
        "payee",
        "transaction_details",
        "vendor",
        "particulars",
    },
    "amount": {
        "amount",
        "cost",
        "price",
        "debit",
        "debit_amount",
        "spend",
        "spent",
        "total",
        "value",
        "charge",
    },
    "category": {
        "category",
        "tag",
        "type",
        "group",
        "classification",
        "expense_type",
        "category_name",
    },
}

REQUIRED_COLUMNS: set[str] = {"date", "description", "amount"}

# Common date formats for robust multi-format parsing
DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%m-%d-%Y",
    "%d.%m.%Y",
    "%Y.%m.%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
)


class ExpenseIngestionService:
    """Service handling file validation, CSV decoding, column mapping, and row normalization."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def process_csv_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> ExpenseIngestionResponse:
        """
        Process, validate, and normalize raw uploaded CSV bytes.
        """
        # Sanitize filename against path traversal and dangerous characters
        safe_filename = self._sanitize_filename(filename)

        # 1. Check file size limit
        if len(content) > self._settings.max_upload_size_bytes:
            max_mb = self._settings.max_upload_size_bytes / (1024 * 1024)
            raise ValidationError(
                f"File size exceeds maximum allowed limit of {max_mb:.1f} MB."
            )

        # 2. Empty-file detection
        if not content or len(content.strip()) == 0:
            raise ValidationError("The uploaded CSV file is empty.")

        # 3. Safe decoding (UTF-8 with BOM handling, fallback to latin-1)
        text = self._decode_bytes(content)

        # 4. Parse CSV text safely
        rows, headers = self._parse_csv_text(text)

        if not headers:
            raise ValidationError("CSV file must contain a valid header row.")

        if not rows:
            raise ValidationError("CSV file contains headers but has no data rows.")

        # Check row count limit
        if len(rows) > self._settings.max_upload_rows:
            raise ValidationError(
                f"File contains {len(rows)} rows, which exceeds the maximum limit of {self._settings.max_upload_rows}."
            )

        # 5. Map headers to canonical columns
        column_mapping = self._resolve_column_mapping(headers)

        # 6. Validate and normalize rows
        valid_items: list[NormalizedExpense] = []
        row_errors: list[RowValidationError] = []
        seen_keys: set[tuple[str, str, float]] = set()
        duplicate_count = 0

        for row_idx, row in enumerate(rows, start=1):
            normalized, error, is_dup = self._normalize_row(
                row, row_idx, column_mapping, seen_keys
            )
            if error:
                row_errors.append(error)
            elif normalized:
                valid_items.append(normalized)
                if is_dup:
                    duplicate_count += 1

        total_rows = len(rows)
        valid_rows = len(valid_items)
        invalid_rows = len(row_errors)

        # Compute summary metrics
        total_spending = round(sum(item.amount for item in valid_items), 2)
        date_range = self._calculate_date_range(valid_items)

        if valid_rows == 0:
            status = "failed"
        elif invalid_rows > 0:
            status = "partial"
        else:
            status = "success"

        logger.info(
            "Expense ingestion complete for file '%s': %d total, %d valid, %d invalid, %d duplicates",
            safe_filename,
            total_rows,
            valid_rows,
            invalid_rows,
            duplicate_count,
        )

        return ExpenseIngestionResponse(
            filename=safe_filename,
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            duplicate_rows=duplicate_count,
            date_range=date_range,
            total_spending=total_spending,
            status=status,
            errors=row_errors,
            data=valid_items,
        )

    def _sanitize_filename(self, filename: str) -> str:
        """Strip directory paths, null bytes, and non-printable chars from filename."""
        clean = Path(filename).name
        clean = "".join(ch for ch in clean if ch.isprintable() and ch not in "\0/\\")
        return clean.strip() or "expenses.csv"

    def _decode_bytes(self, content: bytes) -> str:
        """Safely decode bytes to string handling BOM and encodings."""
        try:
            return content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                return content.decode("latin-1")
            except Exception as exc:
                raise ValidationError(f"Failed to decode file contents: {exc}")

    def _parse_csv_text(self, text: str) -> tuple[list[dict[str, str]], list[str]]:
        """Parse raw CSV text safely handling dialects and malformed lines."""
        # Strip null bytes
        clean_text = text.replace("\0", "")
        sample = clean_text[:4096]
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",\t;|")
        except Exception:
            dialect = csv.excel

        stream = io.StringIO(clean_text)
        try:
            reader = csv.reader(stream, dialect=dialect)
            header_row = next(reader, None)
            if not header_row:
                return [], []

            clean_headers = [h.strip() for h in header_row if h is not None]
            if not any(clean_headers):
                return [], []

            dict_reader = csv.DictReader(stream, fieldnames=header_row, dialect=dialect)
            rows: list[dict[str, str]] = []
            for row in dict_reader:
                # Discard completely empty lines
                if any(val and val.strip() for val in row.values() if val):
                    rows.append({k.strip(): (v.strip() if v else "") for k, v in row.items() if k})

            return rows, clean_headers
        except (csv.Error, Exception) as exc:
            raise ValidationError(f"Malformed or unparseable CSV structure: {exc}")

    def _resolve_column_mapping(self, headers: list[str]) -> dict[str, str]:
        """
        Map file headers to canonical column names using explicit alias sets.
        Raises ValidationError if any required canonical column is missing.
        """
        mapping: dict[str, str] = {}
        normalized_headers = {
            re.sub(r"[^a-z0-9]", "_", h.lower().strip()): h for h in headers if h
        }

        for canonical_name, aliases in CANONICAL_COLUMN_ALIASES.items():
            matched_header = None
            # Check for exact matches in aliases
            for alias in aliases:
                norm_alias = re.sub(r"[^a-z0-9]", "_", alias.lower().strip())
                if norm_alias in normalized_headers:
                    matched_header = normalized_headers[norm_alias]
                    break
            if matched_header:
                mapping[canonical_name] = matched_header

        missing = REQUIRED_COLUMNS - set(mapping.keys())
        if missing:
            raise ValidationError(
                f"Missing required expense column(s): {', '.join(sorted(missing))}. "
                f"Found headers: {', '.join(headers)}"
            )

        return mapping

    def _normalize_row(
        self,
        row: dict[str, str],
        row_idx: int,
        mapping: dict[str, str],
        seen_keys: set[tuple[str, str, float]],
    ) -> tuple[NormalizedExpense | None, RowValidationError | None, bool]:
        """Validate and normalize an individual row."""
        # 1. Parse Date
        date_raw = row.get(mapping["date"], "").strip()
        if not date_raw:
            return None, RowValidationError(
                row_index=row_idx, field="date", reason="Date is missing or empty."
            ), False

        parsed_date = self._parse_date(date_raw)
        if not parsed_date:
            return None, RowValidationError(
                row_index=row_idx,
                field="date",
                reason=f"Invalid date format '{date_raw}'. Expected standard formats like YYYY-MM-DD or MM/DD/YYYY.",
            ), False

        # 2. Parse Description
        desc_raw = row.get(mapping["description"], "").strip()
        if not desc_raw:
            return None, RowValidationError(
                row_index=row_idx, field="description", reason="Description is missing or empty."
            ), False

        # Sanitize against CSV formula injection
        cleaned_desc = self._sanitize_text(desc_raw)

        # 3. Parse Amount
        amount_raw = row.get(mapping["amount"], "").strip()
        if not amount_raw:
            return None, RowValidationError(
                row_index=row_idx, field="amount", reason="Amount is missing or empty."
            ), False

        parsed_amount = self._parse_amount(amount_raw)
        if parsed_amount is None:
            return None, RowValidationError(
                row_index=row_idx,
                field="amount",
                reason=f"Invalid numeric amount '{amount_raw}'.",
            ), False

        if parsed_amount <= 0:
            return None, RowValidationError(
                row_index=row_idx,
                field="amount",
                reason="Amount must be a positive number greater than 0.",
            ), False

        # 4. Parse Category (optional, default to 'Other')
        category_header = mapping.get("category")
        category_raw = row.get(category_header, "").strip() if category_header else ""
        cleaned_category = self._sanitize_text(category_raw) if category_raw else "Other"
        if not cleaned_category:
            cleaned_category = "Other"

        # Check duplicates
        dup_key = (parsed_date, cleaned_desc.lower(), parsed_amount)
        is_duplicate = dup_key in seen_keys
        seen_keys.add(dup_key)

        return (
            NormalizedExpense(
                date=parsed_date,
                description=cleaned_desc,
                category=cleaned_category,
                amount=parsed_amount,
            ),
            None,
            is_duplicate,
        )

    def _parse_date(self, raw: str) -> str | None:
        """Parse various date formats into standard YYYY-MM-DD ISO string."""
        raw = raw.strip()
        # Fast path for ISO standard
        if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
            try:
                d = datetime.strptime(raw, "%Y-%m-%d").date()
                if 1990 <= d.year <= 2100:
                    return d.isoformat()
            except ValueError:
                return None

        for fmt in DATE_FORMATS:
            try:
                d = datetime.strptime(raw, fmt).date()
                if 1990 <= d.year <= 2100:
                    return d.isoformat()
            except ValueError:
                continue

        return None

    def _parse_amount(self, raw: str) -> float | None:
        """Parse monetary amount string removing currency signs and commas."""
        clean = raw.strip()
        # Handle parentheses format for negative amounts: (12.34) -> -12.34
        if clean.startswith("(") and clean.endswith(")"):
            clean = "-" + clean[1:-1].strip()

        # Remove currency symbols ($ € £ ₹ ¥) and commas/spaces
        clean = re.sub(r"[\$€£₹¥,\s]", "", clean)
        try:
            val = float(clean)
            if not (val != val or val == float("inf") or val == float("-inf")):  # check NaN/inf
                return round(val, 2)
        except ValueError:
            return None
        return None

    def _sanitize_text(self, text: str) -> str:
        """Strip dangerous formula prefixes and non-printable control characters."""
        # Remove control characters except normal whitespace
        sanitized = "".join(ch for ch in text if ch.isprintable() or ch in " \t\n")
        sanitized = sanitized.strip()
        # If starts with CSV formula triggers (=, +, -, @), prefix with quote for safety
        if sanitized and sanitized[0] in ("=", "+", "-", "@", "\t", "\r"):
            sanitized = "'" + sanitized
        return sanitized

    def _calculate_date_range(self, items: list[NormalizedExpense]) -> DateRange | None:
        """Calculate start and end dates from normalized items."""
        if not items:
            return None
        dates = [item.date for item in items]
        return DateRange(start_date=min(dates), end_date=max(dates))


# Singleton instance
ingestion_service = ExpenseIngestionService()
