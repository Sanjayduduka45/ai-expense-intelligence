"""
Health service encapsulating system status business logic.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.backend.core.config import Settings, get_settings
from app.backend.schemas.health import HealthResponse


class HealthService:
    """Service responsible for evaluating system health and diagnostics."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def get_health_status(self) -> HealthResponse:
        """
        Evaluate and return the system health status.
        
        Keeps route handlers free of business/diagnostic evaluation logic.
        """
        now_utc = datetime.now(timezone.utc).isoformat()

        return HealthResponse(
            status="ok",
            version=self._settings.app_version,
            environment=self._settings.app_env,
            timestamp=now_utc,
        )


# Default singleton service instance
health_service = HealthService()
