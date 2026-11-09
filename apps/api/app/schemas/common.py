from datetime import UTC, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class MetaEnvelope(BaseModel):
    request_id: str = Field(description="Unique correlation ID for the request")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of response generation",
    )


class ErrorDetail(BaseModel):
    field: str | None = Field(default=None, description="Request field that caused the error")
    issue: str = Field(description="Human-readable description of the validation issue")


class ErrorInfo(BaseModel):
    code: str = Field(description="Stable machine-readable error code")
    message: str = Field(description="Human-readable summary of the error")
    details: list[ErrorDetail] | None = Field(
        default=None, description="Detailed field-level errors"
    )
    request_id: str | None = Field(default=None, description="Correlation ID for troubleshooting")


class ResponseEnvelope(BaseModel, Generic[T]):
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
