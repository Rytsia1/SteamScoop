"""API contract tests for methodology, model cards, and dataset documentation."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.methodology import DatasetDocumentationItem, MethodologyResponse, ModelCardItem


def test_get_methodology_contract(client: TestClient) -> None:
    custom_id = "test-methodology-req-001"
    response = client.get("/api/v1/methodology", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id

    data = response.json()
    validated = ResponseEnvelope[MethodologyResponse].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert validated.meta.request_id == custom_id
    assert validated.data.version == "1.0.0"
    assert "historical" in validated.data.collection_policy.method
    assert "polarity" in validated.data.definitions.model_sentiment


def test_list_model_cards_contract(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    response = client.get("/api/v1/methodology/models")

    assert response.status_code == 200
    data = response.json()
    validated = ResponseEnvelope[list[ModelCardItem]].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert len(validated.data) >= 1

    first = validated.data[0]
    assert first.task == "sentiment"
    assert first.status == "active"


def test_list_datasets_contract(client: TestClient) -> None:
    response = client.get("/api/v1/methodology/datasets")

    assert response.status_code == 200
    data = response.json()
    validated = ResponseEnvelope[list[DatasetDocumentationItem]].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert len(validated.data) >= 1
    dataset = validated.data[0]
    assert dataset.dataset_version == "steam-reviews-eval-v1.0"
    assert dataset.sampling_policy != ""
