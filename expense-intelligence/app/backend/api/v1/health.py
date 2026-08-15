"""
Health check route handler for API v1.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.backend.schemas.health import HealthResponse
from app.backend.services.health_service import HealthService, health_service

router = APIRouter(prefix="/health", tags=["Health"])


def get_health_service() -> HealthService:
    """Dependency provider for HealthService."""
    return health_service


@router.get(
    "",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Returns the operational status, version, and environment of the API service.",
)
async def check_health(
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    """
    Check system health.
    
    Delegates entirely to HealthService to ensure no business logic resides in route handlers.
    """
    return service.get_health_status()
