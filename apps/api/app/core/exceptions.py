from typing import Any


class DomainError(Exception):
    """Base class for all application domain exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        status_code: int = 400,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


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
        identifier: str | int,
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
        review_id: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=f"Review '{review_id}' was not found.",
            code="REVIEW_NOT_FOUND",
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


class ValidationDomainError(DomainError):
    """Raised when domain business rules fail input validation."""

    def __init__(
        self,
        message: str = "The request contains invalid fields.",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )

