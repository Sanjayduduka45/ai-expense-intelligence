"""
Backend configuration loaded from environment variables.

All values are read at import time.  Never access os.environ directly
elsewhere in the backend — always import from this module.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings resolved from .env / environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Server ────────────────────────────────────────────────────────────────
    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8000)

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # ── AI (placeholder — not used in Phase 0) ────────────────────────────────
    gemini_api_key: str = Field(default="", repr=False)  # never logged

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


# Singleton — import this everywhere in the backend
settings = Settings()
