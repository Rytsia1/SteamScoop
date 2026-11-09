import re
from typing import Any

# Regex to scrub sensitive API keys from logged URLs and query strings
_SENSITIVE_KEY_PATTERN = re.compile(r"([?&]key=)[^&]+", re.IGNORECASE)


def sanitize_url(url: str) -> str:
    """Mask sensitive query parameters (e.g. key) in URL strings for safe logging."""
    return _SENSITIVE_KEY_PATTERN.sub(r"\1[REDACTED]", url)


class SteamIntegrationError(Exception):
    """Base exception for all external Steam API integration errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SteamRateLimitError(SteamIntegrationError):
    """Raised when Steam responds with HTTP 429 Too Many Requests."""

    def __init__(
        self,
        message: str = "Steam API rate limit exceeded (HTTP 429).",
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class SteamTemporaryServerError(SteamIntegrationError):
    """Raised when Steam experiences a temporary server error (HTTP 5xx, timeout, connect error)."""

    def __init__(
        self,
        message: str = "Steam API temporary upstream failure.",
        status_code: int | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code)


class SteamClientError(SteamIntegrationError):
    """Raised when Steam responds with a non-recoverable 4xx client error (e.g. 400 Bad Request)."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message, status_code=status_code)


class SteamAuthenticationError(SteamIntegrationError):
    """Raised when Steam credentials/key are rejected (HTTP 401 Unauthorized or 403 Forbidden)."""

    def __init__(
        self,
        message: str = "Steam API key is invalid or unauthorized.",
        status_code: int = 403,
    ) -> None:
        super().__init__(message, status_code=status_code)


class SteamGameUnavailableError(SteamIntegrationError):
    """Raised when a Steam game App ID does not exist, was delisted, or returned no data."""

    def __init__(self, steam_app_id: int, message: str | None = None) -> None:
        msg = message or f"Steam game {steam_app_id} is unavailable, delisted, or invalid."
        super().__init__(msg, status_code=404)
        self.steam_app_id = steam_app_id


class SteamMalformedResponseError(SteamIntegrationError):
    """Raised when Steam returns a non-JSON, incomplete, or contract-violating payload."""

    def __init__(
        self,
        message: str = "Steam API response was malformed or failed schema validation.",
        details: Any = None,
    ) -> None:
        super().__init__(message, status_code=502)
        self.details = details

