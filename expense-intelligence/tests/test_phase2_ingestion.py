"""
Phase 2: Secure expense ingestion and validation tests.

Tests:
1. Valid CSV ingestion, canonical normalization, and summary calculation.
2. Missing required columns error handling.
3. Invalid amounts (non-numeric, negative, zero, formatted with currency symbols).
4. Invalid dates (bad strings, unparseable formats).
5. Empty file (0 bytes).
6. Oversized input (exceeding max size / max rows).
7. Malformed CSV structure.
8. Additional security checks: CSV formula injection sanitization, extension gating, log privacy.
"""

from __future__ import annotations

import io
import logging
import pytest
from fastapi.testclient import TestClient

from app.backend.core.config import Settings
from app.backend.main import app
from app.backend.schemas.expense import ExpenseIngestionResponse
from app.backend.services.ingestion_service import ExpenseIngestionService


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Synchronous test client for the FastAPI backend."""
    return TestClient(app)


class TestValidCsvIngestion:
    """1. Valid CSV tests."""

    def test_valid_csv_canonical_headers(self, client: TestClient) -> None:
        csv_content = (
            "date,description,category,amount\n"
            "2025-01-15,Whole Foods,Groceries,85.50\n"
            "2025-01-16,Shell Gas,Transportation,45.00\n"
            "2025-01-17,Netflix Subscription,Entertainment,19.99\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("expenses.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        result = ExpenseIngestionResponse(**data)

        assert result.status == "success"
        assert result.filename == "expenses.csv"
        assert result.total_rows == 3
        assert result.valid_rows == 3
        assert result.invalid_rows == 0
        assert result.total_spending == 150.49
        assert result.date_range is not None
        assert result.date_range.start_date == "2025-01-15"
        assert result.date_range.end_date == "2025-01-17"
        assert len(result.data) == 3

    def test_valid_csv_flexible_column_mapping(self, client: TestClient) -> None:
        """Test aliases: tx_date -> date, merchant -> description, debit -> amount, tag -> category."""
        csv_content = (
            "Tx_Date,Merchant,Tag,Debit\n"
            "01/10/2025,Starbucks,Coffee,$5.75\n"
            "01/12/2025,Apple Store,Electronics,\"1,299.00\"\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("bank_export.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid_rows"] == 2
        assert data["total_spending"] == 1304.75
        assert data["data"][0]["date"] == "2025-01-10"
        assert data["data"][0]["description"] == "Starbucks"
        assert data["data"][0]["category"] == "Coffee"
        assert data["data"][0]["amount"] == 5.75
        assert data["data"][1]["amount"] == 1299.00

    def test_missing_optional_category_defaults_to_other(self, client: TestClient) -> None:
        """Category column is optional; defaults to 'Other' when missing."""
        csv_content = (
            "date,description,amount\n"
            "2025-02-01,Uber Ride,32.50\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("no_cat.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid_rows"] == 1
        assert data["data"][0]["category"] == "Other"


class TestMissingRequiredColumns:
    """2. Missing required columns tests."""

    def test_missing_amount_column(self, client: TestClient) -> None:
        csv_content = (
            "date,description,category\n"
            "2025-01-15,Whole Foods,Groceries\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("missing_amount.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Missing required expense column(s)" in data["error"]["message"]
        assert "amount" in data["error"]["message"]

    def test_missing_date_column(self, client: TestClient) -> None:
        csv_content = (
            "description,category,amount\n"
            "Whole Foods,Groceries,85.50\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("missing_date.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 422
        data = response.json()
        assert "date" in data["error"]["message"]


class TestInvalidAmounts:
    """3. Invalid amounts tests."""

    def test_non_numeric_and_negative_amounts(self, client: TestClient) -> None:
        csv_content = (
            "date,description,category,amount\n"
            "2025-01-01,Valid Coffee,Food,4.50\n"
            "2025-01-02,Text Amount,Food,FREE\n"
            "2025-01-03,Negative Amount,Refund,-50.00\n"
            "2025-01-04,Zero Amount,Food,0.00\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("invalid_amounts.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "partial"
        assert data["total_rows"] == 4
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 3
        assert len(data["errors"]) == 3
        assert data["total_spending"] == 4.50


class TestInvalidDates:
    """4. Invalid dates tests."""

    def test_unparseable_date_formats(self, client: TestClient) -> None:
        csv_content = (
            "date,description,category,amount\n"
            "not-a-real-date,Item 1,Other,25.00\n"
            "2025-01-20,Item 2,Other,30.00\n"
            "9999-99-99,Item 3,Other,15.00\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("invalid_dates.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 2
        assert data["errors"][0]["field"] == "date"


class TestEmptyFile:
    """5. Empty file tests."""

    def test_zero_byte_file(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert response.status_code == 422
        data = response.json()
        assert "empty" in data["error"]["message"].lower()

    def test_header_only_file(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("headers_only.csv", b"date,description,amount\n", "text/csv")},
        )
        assert response.status_code == 422
        data = response.json()
        assert "no data rows" in data["error"]["message"].lower()


class TestOversizedInput:
    """6. Oversized input tests."""

    def test_oversized_file_size(self) -> None:
        service = ExpenseIngestionService(settings=Settings(max_upload_size_bytes=100))
        oversized_bytes = b"date,description,amount\n" + b"2025-01-01,Test,10.00\n" * 10
        with pytest.raises(Exception) as exc_info:
            service.process_csv_bytes(oversized_bytes, "big.csv")
        assert "exceeds maximum allowed limit" in str(exc_info.value)

    def test_oversized_row_count(self) -> None:
        service = ExpenseIngestionService(settings=Settings(max_upload_rows=2))
        csv_bytes = (
            "date,description,amount\n"
            "2025-01-01,Item 1,10.00\n"
            "2025-01-02,Item 2,20.00\n"
            "2025-01-03,Item 3,30.00\n"
        ).encode("utf-8")
        with pytest.raises(Exception) as exc_info:
            service.process_csv_bytes(csv_bytes, "many_rows.csv")
        assert "exceeds the maximum limit" in str(exc_info.value)


class TestMalformedCsv:
    """7. Malformed CSV structure tests."""

    def test_unsupported_file_extension(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("malicious.exe", b"fake binary data", "application/octet-stream")},
        )
        assert response.status_code == 422
        data = response.json()
        assert "Unsupported file format" in data["error"]["message"]


class TestSecurityAndDataQuality:
    """8. Security and edge cases."""

    def test_formula_injection_sanitization(self, client: TestClient) -> None:
        """Prevent CSV formula injection (=, +, -, @)."""
        csv_content = (
            "date,description,amount\n"
            "2025-01-01,=SUM(A1:A10),50.00\n"
            "2025-01-02,+cmd|' /C calc'!A0,60.00\n"
            "2025-01-03,@something,70.00\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("formulas.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid_rows"] == 3
        # Descriptions must be escaped with leading quote
        for item in data["data"]:
            assert item["description"].startswith("'")

    def test_duplicate_row_detection(self, client: TestClient) -> None:
        csv_content = (
            "date,description,amount\n"
            "2025-01-01,Coffee,5.00\n"
            "2025-01-01,Coffee,5.00\n"
            "2025-01-02,Tea,4.00\n"
        ).encode("utf-8")

        response = client.post(
            "/api/v1/expenses/upload",
            files={"file": ("duplicates.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid_rows"] == 3
        assert data["duplicate_rows"] == 1

    def test_logs_do_not_contain_raw_financial_records(
        self, client: TestClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verify that logging only captures summary metrics, not raw transaction rows."""
        caplog.set_level(logging.INFO)
        csv_content = (
            "date,description,amount\n"
            "2025-01-01,UltraSecretFinancialData,987654.32\n"
        ).encode("utf-8")

        client.post(
            "/api/v1/expenses/upload",
            files={"file": ("confidential.csv", csv_content, "text/csv")},
        )

        all_logs = caplog.text
        assert "UltraSecretFinancialData" not in all_logs
        assert "987654.32" not in all_logs
