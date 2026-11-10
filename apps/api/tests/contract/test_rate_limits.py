"""Tests verifying rate limiting behavior and 429 response structure per API_SPECIFICATION.md Section 13."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.core.rate_limit import InMemoryRateLimiter, RateLimitDependency
from app.main import app

test_rate_router = APIRouter()


@test_rate_router.get(
    "/test-rate-limited",
    dependencies=[Depends(RateLimitDependency(limit=3, window_seconds=60, bucket="test_bucket"))],
)
def rate_limited_endpoint() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(test_rate_router)


def test_rate_limiting_enforcement(client: TestClient) -> None:
    # Reset limiter for test determinism
    limiter = InMemoryRateLimiter.get_limiter("test_bucket", limit=3, window_seconds=60)
    limiter.reset()

    # Requests 1 to 3 should succeed
    for i in range(1, 4):
        res = client.get("/test-rate-limited")
        assert res.status_code == 200
        assert res.headers.get("RateLimit-Limit") == "3"
        assert res.headers.get("RateLimit-Remaining") == str(3 - i)

    # 4th request must be rejected with 429 RATE_LIMITED
    excess_res = client.get("/test-rate-limited")
    assert excess_res.status_code == 429
    assert "Retry-After" in excess_res.headers
    retry_after = int(excess_res.headers["Retry-After"])
    assert retry_after >= 1

    body = excess_res.json()
    assert body["data"] is None
    assert body["error"]["code"] == "RATE_LIMITED"
    assert "Rate limit exceeded" in body["error"]["message"]

