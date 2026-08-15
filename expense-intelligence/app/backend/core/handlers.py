"""
Centralized exception handlers for FastAPI.

Translates internal and standard exceptions into consistent JSON error responses.
Ensures internal error details and secrets are never leaked to API clients.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.backend.core.exceptions import AppException
from app.backend.core.logging import get_logger
from app.backend.schemas.common import ErrorDetail, ErrorResponse

logger = get_logger("app.backend.handlers")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all centralized exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application exception [%s] on %s %s: %s",
            exc.error_code,
            request.method,
            request.url.path,
            exc.message,
        )
        response_model = ErrorResponse(
            success=False,
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.message,
                details=exc.details if exc.details else None,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response_model.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "Validation error on %s %s: %d error(s)",
            request.method,
            request.url.path,
            len(exc.errors()),
        )
        # Format field validation errors cleanly
        formatted_errors: list[dict[str, Any]] = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            formatted_errors.append(
                {
                    "location": loc,
                    "message": err.get("msg", "Invalid value"),
                    "type": err.get("type", "value_error"),
                }
            )

        response_model = ErrorResponse(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request validation failed. Please check your parameters and payload.",
                details=formatted_errors,
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response_model.model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        logger.info(
            "HTTP %d on %s %s: %s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )
        response_model = ErrorResponse(
            success=False,
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                details=None,
            ),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=response_model.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log full stack trace internally, never leak to client
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True,
        )
        response_model = ErrorResponse(
            success=False,
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal error occurred. Please try again later.",
                details=None,
            ),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response_model.model_dump(),
        )
