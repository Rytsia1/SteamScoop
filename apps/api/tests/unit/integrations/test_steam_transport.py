import logging

import httpx
import pytest

from app.integrations.steam.exceptions import (
    SteamAuthenticationError,
    SteamClientError,
    SteamMalformedResponseError,
    SteamRateLimitError,
    SteamTemporaryServerError,
    sanitize_url,
)
from app.integrations.steam.transport import SteamTransport, parse_retry_after


def test_sanitize_url() -> None:
    raw_url = "https://api.steampowered.com/Reviews?key=SECRET_TOKEN_12345&appid=1145360"
    sanitized = sanitize_url(raw_url)
    assert "SECRET_TOKEN_12345" not in sanitized
    assert "key=[REDACTED]" in sanitized
    assert "appid=1145360" in sanitized


def test_parse_retry_after() -> None:
    assert parse_retry_after("15") == 15.0
    assert parse_retry_after("0") == 0.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("invalid-header") is None


def test_transport_success_get_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/test"
        return httpx.Response(200, json={"status": "ok", "count": 42})

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(client=mock_client)

    data = transport.get_json("https://api.steampowered.com/test")
    assert data == {"status": "ok", "count": 42}


def test_transport_redacts_api_key_in_logs() -> None:
    captured_messages: list[str] = []

    class TestCaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured_messages.append(record.getMessage())

    handler_inst = TestCaptureHandler()
    target_logger = logging.getLogger("steamscoop.integrations.steam.transport")
    target_logger.setLevel(logging.INFO)
    target_logger.addHandler(handler_inst)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": 1})

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    transport = SteamTransport(api_key="SUPER_SECRET_KEY_XYZ", client=mock_client)

    try:
        transport.get_json("https://api.steampowered.com/endpoint", include_api_key=True)
        log_text = " ".join(captured_messages)
        assert "SUPER_SECRET_KEY_XYZ" not in log_text
        assert "key=[REDACTED]" in log_text
    finally:
        target_logger.removeHandler(handler_inst)


def test_transport_handles_429_retry_after_and_succeeds() -> None:
    calls = 0
    slept_durations: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "2"}, text="Too Many Requests")
        return httpx.Response(200, json={"success": 1})

    def fake_sleep(duration: float) -> None:
        slept_durations.append(duration)

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(
        client=mock_client,
        max_retries=2,
        sleep_fn=fake_sleep,
    )

    data = transport.get_json("https://api.steampowered.com/reviews")
    assert data == {"success": 1}
    assert calls == 2
    assert len(slept_durations) == 1
    assert slept_durations[0] >= 2.0


def test_transport_raises_rate_limit_when_exceeded() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "100"}, text="Rate limited")

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(
        client=mock_client,
        max_retries=1,
        max_retry_after_seconds=30.0,
    )

    with pytest.raises(SteamRateLimitError) as exc_info:
        transport.get_json("https://api.steampowered.com/reviews")

    assert exc_info.value.status_code == 429
    assert exc_info.value.retry_after == 100.0


def test_transport_temporary_5xx_retries_and_succeeds() -> None:
    calls = 0
    slept_durations: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(502, text="Bad Gateway")
        return httpx.Response(200, json={"recovered": True})

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(
        client=mock_client,
        max_retries=3,
        base_backoff_seconds=0.01,
        sleep_fn=slept_durations.append,
    )

    data = transport.get_json("https://api.steampowered.com/test")
    assert data == {"recovered": True}
    assert calls == 3
    assert len(slept_durations) == 2


def test_transport_temporary_5xx_exhaustion_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(
        client=mock_client,
        max_retries=2,
        base_backoff_seconds=0.01,
        sleep_fn=lambda _: None,
    )

    with pytest.raises(SteamTemporaryServerError) as exc_info:
        transport.get_json("https://api.steampowered.com/test")

    assert exc_info.value.status_code == 503


def test_transport_handles_network_timeout() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ReadTimeout("Timeout reading socket")
        return httpx.Response(200, json={"ok": True})

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(
        client=mock_client,
        max_retries=2,
        base_backoff_seconds=0.01,
        sleep_fn=lambda _: None,
    )

    data = transport.get_json("https://api.steampowered.com/test")
    assert data == {"ok": True}
    assert calls == 2


def test_transport_authentication_error_no_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(403, text="Forbidden")

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(
        client=mock_client,
        max_retries=3,
    )

    with pytest.raises(SteamAuthenticationError) as exc_info:
        transport.get_json("https://api.steampowered.com/test")

    assert exc_info.value.status_code == 403
    assert calls == 1  # 403 must not trigger retry loops


def test_transport_client_error_400() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="Bad Request")

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(client=mock_client)

    with pytest.raises(SteamClientError) as exc_info:
        transport.get_json("https://api.steampowered.com/test")

    assert exc_info.value.status_code == 400


def test_transport_malformed_non_json_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>502 Cloudflare Gateway</body></html>")

    mock_client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = SteamTransport(client=mock_client)

    with pytest.raises(SteamMalformedResponseError):
        transport.get_json("https://api.steampowered.com/test")
