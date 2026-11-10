"""API contract tests for multi-game analytical comparisons."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.comparison import ComparisonResponseData


def test_compare_games_success(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game1_id = str(sample_catalog["game1"].id)
    game2_id = str(sample_catalog["game2"].id)

    payload = {
        "game_ids": [game1_id, game2_id],
        "metrics": ["model_sentiment", "aspect_sentiment", "review_volume"],
        "period": {"from": "2026-01-01", "to": "2026-11-01"},
        "model_version": "baseline",
    }
    custom_id = "test-comp-req-001"
    response = client.post("/api/v1/comparisons", json=payload, headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id

    data = response.json()
    validated = ResponseEnvelope[ComparisonResponseData].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert len(validated.data.games) == 2
    comp_game_ids = [str(g.game_id) for g in validated.data.games]
    assert game1_id in comp_game_ids
    assert game2_id in comp_game_ids


def test_compare_games_fewer_than_two(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game1_id = str(sample_catalog["game1"].id)
    payload = {
        "game_ids": [game1_id],
        "metrics": ["sentiment"],
    }
    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_compare_games_duplicate_ids(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game1_id = str(sample_catalog["game1"].id)
    payload = {
        "game_ids": [game1_id, game1_id],
        "metrics": ["sentiment"],
    }
    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_compare_games_invalid_metric(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game1_id = str(sample_catalog["game1"].id)
    game2_id = str(sample_catalog["game2"].id)
    payload = {
        "game_ids": [game1_id, game2_id],
        "metrics": ["sentiment", "unsupported_metric_xyz"],
    }
    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_compare_games_missing_game_id(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game1_id = str(sample_catalog["game1"].id)
    missing_id = str(uuid.uuid4())
    payload = {
        "game_ids": [game1_id, missing_id],
        "metrics": ["model_sentiment"],
    }
    response = client.post("/api/v1/comparisons", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "GAME_NOT_FOUND"
