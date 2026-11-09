import email.utils
import logging
import random
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import get_settings
from app.integrations.steam.exceptions import (
    SteamAuthenticationError,
    SteamClientError,
    SteamIntegrationError,
    SteamMalformedResponseError,
    SteamRateLimitError,
    SteamTemporaryServerError,
    sanitize_url,
)

logger = logging.getLogger("steamscoop.integrations.steam.transport")
# Suppress default HTTPX request logging to prevent credential leakage in logs
logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_retry_after(header_val: str | None) -> float | None:
    """Parse HTTP Retry-After header as either seconds or an RFC 2822 datetime."""
    if not header_val:
        return None
    val = header_val.strip()
    try:
        return max(0.0, float(val))
    except ValueError:
        pass

    try:
        dt = email.utils.parsedate_to_datetime(val)
        now = datetime.now(UTC)
        return max(0.0, (dt - now).total_seconds())
    except Exception:
        return None


class SteamTransport:
    """Isolated, resilient HTTP transport for communicating with Steam endpoints.

    Features:
    - Configurable connection, read, and pool timeouts.
    - Bounded exponential backoff retry logic.
    - Handling for HTTP 429 and Retry-After headers.
    - Recovery from transient 5xx server errors and network interruptions.
    - Strict redaction of Steam API keys from all log statements and errors.
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        connect_timeout_seconds: float = 5.0,
        max_retries: int | None = None,
        base_backoff_seconds: float = 0.5,
        max_retry_after_seconds: float = 30.0,
        client: httpx.Client | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.STEAM_API_KEY
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else float(settings.STEAM_API_TIMEOUT_SECONDS)
        )
        self.connect_timeout_seconds = connect_timeout_seconds
        self.max_retries = (
            max_retries if max_retries is not None else settings.STEAM_API_MAX_RETRIES
        )
        self.base_backoff_seconds = base_backoff_seconds
        self.max_retry_after_seconds = max_retry_after_seconds
        self.sleep_fn = sleep_fn

        self._timeouts = httpx.Timeout(
            connect=self.connect_timeout_seconds,
            read=self.timeout_seconds,
            write=5.0,
            pool=5.0,
        )
        self._client = client or httpx.Client(timeout=self._timeouts)
        self._owns_client = client is None

    def close(self) -> None:
        """Close underlying HTTP client if owned by this transport instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "SteamTransport":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        include_api_key: bool = False,
    ) -> dict[str, Any]:
        """Execute a GET request with bounded retries, returning parsed JSON response.

        Guarantees that credentials are not logged or leaked in exceptions.
        """
        req_params: dict[str, Any] = dict(params or {})
        if include_api_key and self.api_key:
            req_params["key"] = self.api_key

        req_headers = {
            "Accept": "application/json",
            "User-Agent": "SteamScoop/0.1.0 (Research & Analytics; contact@steamscoop.local)",
            **(headers or {}),
        }

        # Safe URL for logging without revealing secret key
        safe_url = sanitize_url(str(httpx.URL(url, params=req_params)))

        attempt = 0
        while True:
            attempt += 1
            try:
                logger.info(
                    "Executing Steam GET request [attempt=%d/%d]: %s",
                    attempt,
                    self.max_retries + 1,
                    safe_url,
                )
                response = self._client.get(url, params=req_params, headers=req_headers)

                # 1. Success (200 OK)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if not isinstance(data, dict):
                            raise SteamMalformedResponseError(
                                f"Expected JSON object from Steam but got {type(data).__name__}."
                            )
                        return data
                    except Exception as json_err:
                        logger.warning(
                            "Malformed JSON response from Steam [url=%s]: %s",
                            safe_url,
                            str(json_err),
                        )
                        raise SteamMalformedResponseError(
                            "Steam returned a response that could not be parsed as valid JSON."
                        ) from json_err

                # 2. Rate Limit (429 Too Many Requests)
                if response.status_code == 429:
                    retry_after = parse_retry_after(response.headers.get("Retry-After"))
                    logger.warning(
                        "Steam API rate limit encountered (429) "
                        "[attempt=%d, retry_after=%s, url=%s]",
                        attempt,
                        retry_after,
                        safe_url,
                    )

                    if attempt <= self.max_retries:
                        backoff = (
                            retry_after
                            if retry_after is not None
                            else self.base_backoff_seconds * (2 ** (attempt - 1))
                        )
                        backoff += random.uniform(0.05, 0.2)
                        if backoff <= self.max_retry_after_seconds:
                            logger.info("Applying rate-limit backoff of %.2fs", backoff)
                            self.sleep_fn(backoff)
                            continue

                    raise SteamRateLimitError(
                        "Steam API rate limit exceeded.", retry_after=retry_after
                    )

                # 3. Authentication & Authorization Errors (401, 403)
                if response.status_code in (401, 403):
                    logger.error(
                        "Steam authentication failed [status=%d, url=%s]",
                        response.status_code,
                        safe_url,
                    )
                    raise SteamAuthenticationError(
                        "Steam API key is missing, unauthorized, or invalid.",
                        status_code=response.status_code,
                    )

                # 4. Other Client Errors (400, 404, etc.)
                if 400 <= response.status_code < 500:
                    logger.warning(
                        "Steam client error [status=%d, url=%s]",
                        response.status_code,
                        safe_url,
                    )
                    raise SteamClientError(
                        f"Steam API returned client error HTTP {response.status_code}.",
                        status_code=response.status_code,
                    )

                # 5. Temporary Upstream Server Errors (500, 502, 503, 504)
                if 500 <= response.status_code < 600:
                    logger.warning(
                        "Steam upstream server error [status=%d, attempt=%d/%d, url=%s]",
                        response.status_code,
                        attempt,
                        self.max_retries + 1,
                        safe_url,
                    )
                    if attempt <= self.max_retries:
                        backoff = self.base_backoff_seconds * (2 ** (attempt - 1))
                        backoff += random.uniform(0.05, 0.2)
                        self.sleep_fn(backoff)
                        continue

                    raise SteamTemporaryServerError(
                        f"Steam server error HTTP {response.status_code} after retries.",
                        status_code=response.status_code,
                    )

                # Unrecognized HTTP Status Code
                raise SteamIntegrationError(
                    f"Unexpected HTTP status {response.status_code} received from Steam.",
                    status_code=response.status_code,
                )

            except (httpx.ConnectTimeout, httpx.ReadTimeout) as timeout_err:
                logger.warning(
                    "Steam network timeout [attempt=%d/%d, url=%s]: %s",
                    attempt,
                    self.max_retries + 1,
                    safe_url,
                    type(timeout_err).__name__,
                )
                if attempt <= self.max_retries:
                    backoff = self.base_backoff_seconds * (2 ** (attempt - 1))
                    backoff += random.uniform(0.05, 0.2)
                    self.sleep_fn(backoff)
                    continue
                raise SteamTemporaryServerError(
                    "Timed out communicating with Steam after maximum retries."
                ) from timeout_err

            except (httpx.ConnectError, httpx.RemoteProtocolError) as net_err:
                logger.warning(
                    "Steam connection error [attempt=%d/%d, url=%s]: %s",
                    attempt,
                    self.max_retries + 1,
                    safe_url,
                    type(net_err).__name__,
                )
                if attempt <= self.max_retries:
                    backoff = self.base_backoff_seconds * (2 ** (attempt - 1))
                    backoff += random.uniform(0.05, 0.2)
                    self.sleep_fn(backoff)
                    continue
                raise SteamTemporaryServerError(
                    "Network error connecting to Steam after maximum retries."
                ) from net_err
