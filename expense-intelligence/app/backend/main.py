"""
FastAPI application factory and entry point.

Phase 1: Clean API foundation with structured routing, versioning, centralized
exception handling, configurable CORS, and Pydantic configuration.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.api.router import api_router
from app.backend.core.config import Settings, get_settings
from app.backend.core.handlers import register_exception_handlers
from app.backend.core.logging import setup_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct and configure the FastAPI application."""
    app_settings = settings or get_settings()

    # Configure structured logging
    setup_logging(app_settings.log_level)

    app = FastAPI(
        title=app_settings.app_name,
        description=app_settings.app_tagline,
        version=app_settings.app_version,
        docs_url="/docs" if app_settings.is_development else None,
        redoc_url="/redoc" if app_settings.is_development else None,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Restrictive and configurable via environment variables / settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
    )

    # ── Centralized Exception Handlers ────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(api_router)

    return app


# Module-level app instance consumed by uvicorn
app: FastAPI = create_app()
