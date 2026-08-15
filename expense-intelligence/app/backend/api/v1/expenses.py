"""
Expense management API routes for v1.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.backend.core.config import Settings, get_settings
from app.backend.core.exceptions import ValidationError
from app.backend.schemas.analytics import ExpenseAnalysisRequest, ExpenseAnalyticsReport
from app.backend.schemas.expense import ExpenseIngestionResponse
from app.backend.services.analytics_service import (
    ExpenseAnalyticsService,
    analytics_service,
)
from app.backend.services.ingestion_service import (
    ExpenseIngestionService,
    ingestion_service,
)

router = APIRouter(prefix="/expenses", tags=["Expenses"])


def get_ingestion_service() -> ExpenseIngestionService:
    """Dependency provider for ExpenseIngestionService."""
    return ingestion_service


def get_analytics_service() -> ExpenseAnalyticsService:
    """Dependency provider for ExpenseAnalyticsService."""
    return analytics_service


@router.post(
    "/upload",
    response_model=ExpenseIngestionResponse,
    summary="Upload and Validate Expense CSV",
    description="Upload a CSV file of expenses for parsing, normalization, and validation.",
)
async def upload_expenses(
    file: UploadFile = File(..., description="Expense CSV file"),
    service: ExpenseIngestionService = Depends(get_ingestion_service),
    settings: Settings = Depends(get_settings),
) -> ExpenseIngestionResponse:
    """
    Ingest and normalize an untrusted expense CSV dataset.

    Validates file extension, structure, headers, date and numeric integrity.
    Protects against path traversal by sanitizing the uploaded filename.
    """
    raw_filename = file.filename or "expenses.csv"
    safe_filename = Path(raw_filename).name or "expenses.csv"
    ext = Path(safe_filename).suffix.lower()

    if ext not in settings.allowed_upload_extensions:
        allowed_list = ", ".join(settings.allowed_upload_extensions)
        raise ValidationError(
            f"Unsupported file format '{ext}'. Only {allowed_list} files are allowed."
        )

    # Read uploaded file content
    content = await file.read()

    return service.process_csv_bytes(content=content, filename=safe_filename)


@router.post(
    "/analyze",
    response_model=ExpenseAnalyticsReport,
    summary="Deterministic Expense Analytics",
    description="Calculate factual metrics and rule-based heuristic insights for normalized expenses.",
)
async def analyze_expenses(
    request: ExpenseAnalysisRequest,
    service: ExpenseAnalyticsService = Depends(get_analytics_service),
) -> ExpenseAnalyticsReport:
    """
    Generate deterministic financial analytics and heuristic insights.

    Separates mathematical facts from rule-based estimates.
    Delegates all computational logic to ExpenseAnalyticsService.
    """
    return service.analyze(request.expenses)
