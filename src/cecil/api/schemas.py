"""API request and response schemas.

Defines Pydantic v2 models used by FastAPI endpoints for request
validation and response serialization.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response from the /health endpoint."""

    status: str = Field(description="Server status indicator")
    version: str = Field(description="Cecil version string")


class ErrorResponse(BaseModel):
    """Consistent error response format for all API endpoints."""

    error: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, str] | None = Field(
        default=None,
        description="Additional context about the error",
    )
