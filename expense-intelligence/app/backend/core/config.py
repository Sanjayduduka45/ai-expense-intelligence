"""
Backend configuration loaded from environment variables.

All values are read using Pydantic Settings. Never access os.environ directly
elsewhere in the backend — always import settings from this module.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Union

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.shared.constants import APP_NAME, APP_TAGLINE, APP_VERSION, MAX_UPLOAD_SIZE_BYTES


class Settings(BaseSettings):
    """Application settings resolved from .env / environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application Metadata ──────────────────────────────────────────────────
    app_name: str = Field(default=APP_NAME)
    app_tagline: str = Field(default=APP_TAGLINE)
    app_version: str = Field(default=APP_VERSION)

    # ── Application Environment ───────────────────────────────────────────────
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # ── Server ────────────────────────────────────────────────────────────────
    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("backend_port", "port"),
    )

    # ── Upload Limits & Ingestion Security ────────────────────────────────────
    max_upload_size_bytes: int = Field(default=MAX_UPLOAD_SIZE_BYTES)
    max_upload_rows: int = Field(default=10000)
    allowed_upload_extensions: list[str] = Field(default_factory=lambda: [".csv"])

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Union[list[str], str] prevents pydantic_settings from failing with JSONDecodeError on comma-separated strings
    cors_origins: Union[list[str], str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:8501",
            "http://localhost:8501",
        ]
    )

    # ── AI Credentials (placeholder for future phases — never logged) ────────
    gemini_api_key: str = Field(default="", repr=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Allow CORS origins to be provided as a comma-separated string or list."""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("[") and value.endswith("]"):
                import json
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, origins: Any, info: Any) -> list[str]:
        """Disallow wildcard CORS in production mode."""
        data = info.data
        app_env = str(data.get("app_env", "development")).lower()
        origin_list = origins if isinstance(origins, list) else [origins]
        if app_env == "production" and "*" in origin_list:
            raise ValueError("Wildcard CORS ('*') is strictly forbidden in production mode.")
        return origin_list

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() == "test" or self.app_env.lower() == "testing"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Singleton instance for direct import
settings: Settings = get_settings()
