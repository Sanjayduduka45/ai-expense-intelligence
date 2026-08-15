"""
API v1 router aggregator.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.backend.api.v1.ai import router as ai_router
from app.backend.api.v1.expenses import router as expenses_router
from app.backend.api.v1.health import router as health_router

v1_router = APIRouter(prefix="/api/v1")

# Include v1 sub-routers
v1_router.include_router(health_router)
v1_router.include_router(expenses_router)
v1_router.include_router(ai_router)
