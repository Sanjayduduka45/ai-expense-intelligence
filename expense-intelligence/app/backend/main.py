"""
FastAPI application factory and entry point.

Phase 0: bare application with a single /health endpoint.
No business logic is wired here yet.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.backend.api.health import router as health_router
from app.backend.core.config import settings
from app.shared.constants import APP_NAME, APP_TAGLINE, APP_VERSION


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""

    app = FastAPI(
        title=APP_NAME,
        description=APP_TAGLINE,
        version=APP_VERSION,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Restrict to the Streamlit dev origin; tighten for production.
    origins = [
        f"http://{settings.backend_host}:{settings.backend_port}",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)

    return app


# Module-level app instance consumed by uvicorn.
app: FastAPI = create_app()
