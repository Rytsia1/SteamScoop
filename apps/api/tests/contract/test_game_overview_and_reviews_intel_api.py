"""API contract tests for game overview and multi-task review intelligence."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.game import GameOverviewData
from app.schemas.review import ReviewIntelligenceData


def test_get_game_overview_contract(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game_id = sample_catalog["game1"].id
    custom_id = "test-overview-req-001"
    response = client.get(f"/api/v1/games/{game_id}/overview", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id

    data = response.json()
    validated = ResponseEnvelope[GameOverviewData].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert validated.data.game_id == game_id
    assert validated.data.review_count >= 0
    assert validated.data.steam_recommendation.recommended_count >= 0
    assert validated.data.model_sentiment.model_version != ""
    assert validated.data.coverage.sampled is True


def test_get_game_overview_not_found(client: TestClient) -> None:
    missing_id = uuid.uuid4()
    response = client.get(f"/api/v1/games/{missing_id}/overview")

    assert response.status_code == 404
    data = response.json()
    assert data["data"] is None
    assert data["error"]["code"] == "GAME_NOT_FOUND"


def test_get_review_intelligence_contract(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    review_id = sample_catalog["review1"].id
    custom_id = "test-intel-req-001"
    response = client.get(
        f"/api/v1/reviews/{review_id}/intelligence", headers={"X-Request-ID": custom_id}
    )

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id

    data = response.json()
    validated = ResponseEnvelope[ReviewIntelligenceData].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert validated.data.review_id == review_id
    assert validated.data.sentiment is not None
    assert validated.data.sentiment.label in ("positive", "negative", "neutral")


def test_get_review_intelligence_not_found(client: TestClient) -> None:
    missing_id = uuid.uuid4()
    response = client.get(f"/api/v1/reviews/{missing_id}/intelligence")

    assert response.status_code == 404
    data = response.json()
    assert data["data"] is None
    assert data["error"]["code"] == "REVIEW_NOT_FOUND"
