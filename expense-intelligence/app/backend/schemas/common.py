"""
Shared Pydantic schemas and error envelope definitions.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with strict default configurations."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )


class ErrorDetail(BaseModel):
    """Detailed error payload."""

    code: str = Field(description="Machine-readable error identifier")
    message: str = Field(description="Human-readable error explanation")
    details: list[dict[str, Any]] | dict[str, Any] | None = Field(
        default=None,
        description="Optional field-level or contextual error details",
    )


class ErrorResponse(BaseModel):
    """Standardized error envelope returned for all non-2xx responses."""

    success: bool = Field(default=False, description="Always false for error responses")
    error: ErrorDetail = Field(description="Error information")
