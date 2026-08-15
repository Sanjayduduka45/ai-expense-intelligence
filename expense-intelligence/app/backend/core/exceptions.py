"""
Custom application exception hierarchy.

Centralizes backend error definitions with HTTP status codes and machine-readable error codes.
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """
    Base application exception.
    
    All custom exceptions thrown across the backend service layer should inherit from this.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: str = "BAD_REQUEST",
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(AppException):
    """Raised when critical configuration is missing or invalid."""

    def __init__(
        self,
        message: str,
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details=details,
        )


class ValidationError(AppException):
    """Raised when business validation rules fail."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class ServiceUnavailableError(AppException):
    """Raised when an external or downstream dependency is unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: list[dict[str, Any]] | dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            details=details,
        )
