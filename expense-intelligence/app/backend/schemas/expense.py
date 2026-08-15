"""
Pydantic schemas for expense ingestion, normalization, and validation responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.backend.schemas.common import BaseSchema


class NormalizedExpense(BaseSchema):
    """Canonical normalized expense record."""

    date: str = Field(description="Normalized ISO date (YYYY-MM-DD)")
    description: str = Field(description="Cleaned, sanitized description or merchant name")
    category: str = Field(default="Other", description="Expense category")
    amount: float = Field(gt=0, description="Positive transaction amount")


class DateRange(BaseSchema):
    """Earliest and latest dates in the validated dataset."""

    start_date: str = Field(description="Earliest transaction date (YYYY-MM-DD)")
    end_date: str = Field(description="Latest transaction date (YYYY-MM-DD)")


class RowValidationError(BaseSchema):
    """Details for a single rejected or invalid row."""

    row_index: int = Field(description="1-based original row index in the uploaded file")
    field: str | None = Field(default=None, description="Problematic column/field name")
    reason: str = Field(description="Human-readable reason for invalidity")


class ExpenseIngestionResponse(BaseModel):
    """Complete summary and dataset returned after file validation."""

    filename: str = Field(description="Original uploaded filename")
    total_rows: int = Field(description="Total rows parsed from the file")
    valid_rows: int = Field(description="Number of validly normalized expense rows")
    invalid_rows: int = Field(description="Number of discarded/invalid rows")
    duplicate_rows: int = Field(description="Number of duplicate rows identified")
    date_range: DateRange | None = Field(
        default=None, description="Date span of valid transactions"
    )
    total_spending: float = Field(default=0.0, description="Sum of all valid expense amounts")
    status: str = Field(
        description="Overall ingestion outcome: 'success', 'partial', or 'failed'"
    )
    errors: list[RowValidationError] = Field(
        default_factory=list, description="List of row validation issues encountered"
    )
    data: list[NormalizedExpense] = Field(
        default_factory=list, description="Canonical normalized expense items"
    )
