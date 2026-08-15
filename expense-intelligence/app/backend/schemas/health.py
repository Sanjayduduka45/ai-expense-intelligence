"""
Health-check response schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = Field(default="ok", description="Service operational status")
    version: str = Field(description="Application version")
    environment: str = Field(description="Current deployment environment")
    timestamp: str = Field(description="ISO 8601 UTC timestamp of the health check")
