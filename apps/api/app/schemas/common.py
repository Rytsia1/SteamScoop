from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Cursor or offset pagination metadata."""

    limit: int = Field(description="Number of items requested or returned per page")
    has_more: bool = Field(description="Whether more records exist past the current cursor")
    next_cursor: str | None = Field(
        default=None, description="Opaque cursor token to fetch the subsequent page"
    )


class MetaEnvelope(BaseModel):
    """Standard response metadata envelope."""

    request_id: str = Field(description="Unique correlation ID for the request")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )
    pagination: PaginationMeta | None = Field(
        default=None, description="Pagination metadata when returning collections"
    )


class ErrorDetail(BaseModel):
    """Granular detail for a validation or field-level issue."""

    field: str | None = Field(default=None, description="Request field that caused the error")
    issue: str = Field(description="Human-readable description of the validation issue")


class ErrorInfo(BaseModel):
    """Standardized error envelope payload."""

    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable summary of the error")
    details: list[ErrorDetail] | list[dict[str, Any]] | None = Field(
        default=None, description="Detailed field-level errors"
    )
    request_id: str | None = Field(default=None, description="Correlation ID for troubleshooting")


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard SteamScoop response envelope for single resources and collections."""

    data: T | None = Field(default=None, description="Primary payload data")
    error: ErrorInfo | None = Field(default=None, description="Error information if request failed")
    meta: MetaEnvelope = Field(description="Response metadata envelope")


class DependencyStatus(BaseModel):
    database: str = Field(description="Database connectivity status (connected | unreachable)")
    redis: str = Field(
        description="Redis cache and broker connectivity status (connected | unreachable)"
    )


class HealthData(BaseModel):
    status: str = Field(
        default="healthy",
        description="Application health status (healthy | degraded | unhealthy)",
    )
    version: str = Field(description="Application semantic version")
    app_env: str = Field(description="Runtime environment name")
    timestamp: str = Field(description="Current server timestamp in UTC")
    dependencies: DependencyStatus | None = Field(
        default=None, description="Subsystem dependency statuses"
    )
