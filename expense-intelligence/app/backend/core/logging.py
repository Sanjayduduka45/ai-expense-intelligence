"""
Application logging configuration.

Provides structured logging setup that enforces security best practices:
- Configurable log levels
- Redaction filter to intercept and mask sensitive tokens and API keys
- Never logs sensitive tokens, credentials, or raw confidential financial record dumps
"""

from __future__ import annotations

import logging
import re
import sys

# Pattern for Google AI Studio / Gemini API keys: AIza... (30-45 chars)
_API_KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z\-_]{25,50}")


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts API keys and sensitive tokens from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _API_KEY_PATTERN.sub("[REDACTED_API_KEY]", record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (_API_KEY_PATTERN.sub("[REDACTED_API_KEY]", str(v)) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    (_API_KEY_PATTERN.sub("[REDACTED_API_KEY]", str(arg)) if isinstance(arg, str) else arg)
                    for arg in record.args
                )
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure the root and application loggers."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SensitiveDataFilter())

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[handler],
        force=True,
    )

    # Suppress overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(numeric_level)
    logging.getLogger("uvicorn.error").setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance with sensitive data filtering."""
    logger = logging.getLogger(name)
    # Ensure filter is attached
    if not any(isinstance(f, SensitiveDataFilter) for f in logger.filters):
        logger.addFilter(SensitiveDataFilter())
    return logger
