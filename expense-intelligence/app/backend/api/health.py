"""
Health-check router.

Mounted at /health on the root application.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """
    Returns the current health status of the backend service.

    This endpoint is intentionally lightweight — no DB, no AI calls.
    """
    from app.backend.core.config import settings
    from app.shared.constants import APP_VERSION

    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        environment=settings.app_env,
    )
