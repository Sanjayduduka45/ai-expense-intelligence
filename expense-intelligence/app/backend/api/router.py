"""
Top-level API router registering all API versions and core endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.backend.api.v1.router import v1_router
from app.backend.schemas.health import HealthResponse
from app.backend.services.health_service import health_service

api_router = APIRouter()

# Mount API versions
api_router.include_router(v1_router)


# Root-level health endpoint alias (delegates to the same HealthService)
@api_router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root Health Check",
    include_in_schema=False,
)
async def root_health() -> HealthResponse:
    """Root level health alias for backward compatibility and basic liveness probes."""
    return health_service.get_health_status()
