from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_health_probe() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_health_envelope() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert "data" in payload
    assert "error" in payload
    assert "meta" in payload

    assert payload["error"] is None

    data = payload["data"]
    assert data["status"] in ("healthy", "degraded")
    assert data["version"] == "0.1.0"
    assert "app_env" in data
    assert "timestamp" in data
    assert "dependencies" in data
    assert "database" in data["dependencies"]
    assert "redis" in data["dependencies"]

    meta = payload["meta"]
    assert "request_id" in meta
    assert "timestamp" in meta
    assert response.headers.get("X-Request-ID") == meta["request_id"]


def test_api_v1_health_custom_request_id() -> None:
    custom_id = "req_custom_test_123"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200

    payload = response.json()
    assert payload["meta"]["request_id"] == custom_id
    assert response.headers.get("X-Request-ID") == custom_id


def test_api_v1_health_liveness() -> None:
    response = client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_health_readiness_healthy() -> None:
    with (
        patch("app.api.v1.endpoints.health.check_database_connection", return_value=True),
        patch("app.api.v1.endpoints.health.check_redis_connection", return_value=True),
    ):
        response = client.get("/api/v1/health/readiness")
        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["status"] == "healthy"
        assert payload["data"]["dependencies"]["database"] == "connected"
        assert payload["data"]["dependencies"]["redis"] == "connected"
        assert payload["error"] is None


def test_api_v1_health_readiness_unhealthy() -> None:
    with (
        patch("app.api.v1.endpoints.health.check_database_connection", return_value=False),
        patch("app.api.v1.endpoints.health.check_redis_connection", return_value=True),
    ):
        response = client.get("/api/v1/health/readiness")
        assert response.status_code == 503
        payload = response.json()
        assert payload["data"]["status"] == "unhealthy"
        assert payload["data"]["dependencies"]["database"] == "unreachable"
        assert payload["error"]["code"] == "SERVICE_UNAVAILABLE"
