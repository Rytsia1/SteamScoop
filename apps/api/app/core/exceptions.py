from __future__ import annotations

import uuid
from typing import Any


class DomainError(Exception):
    """Base class for all application domain exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        self.headers = headers or {}


class ResourceNotFoundError(DomainError):
    """Raised when an expected resource is not found in the catalog or system."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        code: str = "RESOURCE_NOT_FOUND",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            details=details,
        )


class GameNotFoundError(ResourceNotFoundError):
    """Raised when a public game cannot be located by ID or Steam App ID."""

    def __init__(
        self,
        identifier: str | int | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Game '{identifier}' was not found or is not currently indexed.",
            code="GAME_NOT_FOUND",
            details=details,
        )


class ReviewNotFoundError(ResourceNotFoundError):
    """Raised when a review cannot be located by ID."""

    def __init__(
        self,
        review_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Review '{review_id}' was not found.",
            code="REVIEW_NOT_FOUND",
            details=details,
        )


class ProjectNotFoundError(ResourceNotFoundError):
    """Raised when a research project is not found or is hidden."""

    def __init__(
        self,
        project_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Project '{project_id}' was not found.",
            code="PROJECT_NOT_FOUND",
            details=details,
        )


class AnalysisNotFoundError(ResourceNotFoundError):
    """Raised when a saved analysis is not found."""

    def __init__(
        self,
        analysis_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Analysis '{analysis_id}' was not found.",
            code="ANALYSIS_NOT_FOUND",
            details=details,
        )


class ExportNotFoundError(ResourceNotFoundError):
    """Raised when an export job is not found."""

    def __init__(
        self,
        export_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Export '{export_id}' was not found.",
            code="EXPORT_NOT_FOUND",
            details=details,
        )


class UserNotFoundError(ResourceNotFoundError):
    """Raised when an account cannot be located by email or ID."""

    def __init__(
        self,
        identifier: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"User '{identifier}' was not found.",
            code="USER_NOT_FOUND",
            details=details,
        )


class ModelNotFoundError(ResourceNotFoundError):
    """Raised when an ML model is not found in the model registry."""

    def __init__(
        self,
        model_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Model '{model_id}' was not found.",
            code="MODEL_NOT_FOUND",
            details=details,
        )


class InvalidCursorError(DomainError):
    """Raised when an opaque pagination cursor is unparseable or tampered with."""

    def __init__(
        self,
        message: str = "The provided pagination cursor is invalid or malformed.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INVALID_CURSOR",
            status_code=400,
            details=details,
        )


class ConflictError(DomainError):
    """Raised when a resource state or duplicate identity conflict occurs."""

    def __init__(
        self,
        message: str = "A conflicting resource already exists.",
        code: str = "RESOURCE_ALREADY_EXISTS",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            details=details,
        )


class ActiveJobExistsError(ConflictError):
    """Raised when an active ingestion job already exists for a game."""

    def __init__(
        self,
        message: str = "An active collection job already exists for this game.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="ACTIVE_JOB_EXISTS",
            details=details,
        )


class InvalidStateTransitionError(ConflictError):
    """Raised when an operation is invalid in the entity's current lifecycle state."""

    def __init__(
        self,
        message: str = "Operation not allowed in current state.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="INVALID_STATE_TRANSITION",
            details=details,
        )


class ValidationDomainError(DomainError):
    """Raised when domain business rules fail input validation."""

    def __init__(
        self,
        message: str = "The request contains invalid fields.",
        details: list[dict[str, Any]] | None = None,
        field: str | None = None,
        issue: str | None = None,
    ) -> None:
        merged_details = list(details or [])
        if field or issue:
            merged_details.append({"field": field, "issue": issue or message})
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=merged_details if merged_details else None,
        )


ValidationException = ValidationDomainError


class IngestionJobNotFoundError(ResourceNotFoundError):
    """Raised when an ingestion job cannot be located by ID."""

    def __init__(
        self,
        job_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Ingestion job '{job_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            details=details,
        )


class PipelineRunNotFoundError(ResourceNotFoundError):
    """Raised when an ML/Analytics pipeline run cannot be located by ID."""

    def __init__(
        self,
        run_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Pipeline run '{run_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            details=details,
        )


class UnauthorizedError(DomainError):
    """Raised when an authentication session or bearer token is missing or invalid."""

    def __init__(
        self,
        message: str = "Authentication is required to access this resource.",
        code: str = "UNAUTHORIZED",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=401,
            details=details,
        )


class ForbiddenError(DomainError):
    """Raised when an authenticated user lacks necessary role or resource permissions."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        code: str = "FORBIDDEN",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=403,
            details=details,
        )


class RateLimitExceededError(DomainError):
    """Raised when a client request quota is exceeded."""

    def __init__(
        self,
        retry_after: int = 60,
        message: str = "Client request quota exceeded. Please wait before retrying.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=429,
            details=details,
            headers={"Retry-After": str(retry_after)},
        )
        self.retry_after = retry_after


class ExportExpiredError(DomainError):
    """Raised when an export artifact is past its expiration cutoff."""

    def __init__(
        self,
        export_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Export artifact '{export_id}' has expired.",
            code="EXPORT_EXPIRED",
            status_code=410,
            details=details,
        )


class ExportNotReadyError(DomainError):
    """Raised when download is attempted while an export job is still queued or running."""

    def __init__(
        self,
        export_id: str | uuid.UUID,
        status: str = "processing",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Export '{export_id}' is not ready for download (current status: {status}).",
            code="EXPORT_NOT_READY",
            status_code=409,
            details=details,
        )


class ExportCancelledError(DomainError):
    """Raised when download is attempted for a cancelled export."""

    def __init__(
        self,
        export_id: str | uuid.UUID,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Export '{export_id}' has been cancelled.",
            code="EXPORT_CANCELLED",
            status_code=409,
            details=details,
        )


class ExportFailedError(DomainError):
    """Raised when download is attempted for a failed export."""

    def __init__(
        self,
        export_id: str | uuid.UUID,
        error_code: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        reason = f" ({error_code})" if error_code else ""
        super().__init__(
            message=f"Export '{export_id}' failed during generation{reason}.",
            code="EXPORT_FAILED",
            status_code=409,
            details=details,
        )


class ExportLimitExceededError(DomainError):
    """Raised when export configuration exceeds allowed row or size quota (HTTP 413)."""

    def __init__(
        self,
        reason: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Export request exceeds allowed capacity: {reason}.",
            code="EXPORT_LIMIT_EXCEEDED",
            status_code=413,
            details=details,
        )


class ExportConcurrencyLimitError(DomainError):
    """Raised when a user exceeds the maximum allowed concurrent export jobs (HTTP 429)."""

    def __init__(
        self,
        active_count: int,
        limit: int,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=(
                f"You already have {active_count} active export jobs "
                f"(maximum allowed: {limit}). Please wait for them to complete."
            ),
            code="EXPORT_CONCURRENCY_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class FeatureDisabledError(DomainError):
    """Raised when an optional feature is disabled by platform policy."""

    def __init__(
        self,
        feature_name: str = "The requested feature",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"{feature_name} is currently disabled.",
            code="FEATURE_DISABLED",
            status_code=404,
            details=details,
        )
