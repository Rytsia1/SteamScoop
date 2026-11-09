import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.review import ReviewDetail


def test_get_review_detail_contract(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    review_id = str(sample_catalog["review1"].id)
    game_id = str(sample_catalog["game1"].id)

    custom_req_id = "test-review-req-001"
    response = client.get(f"/api/v1/reviews/{review_id}", headers={"X-Request-ID": custom_req_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_req_id

    data = response.json()
    validated = ResponseEnvelope[ReviewDetail].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert str(validated.data.id) == review_id
    assert validated.data.game_id == uuid.UUID(game_id)
    assert validated.data.review_text != ""
    assert isinstance(validated.data.voted_up, bool)

    # Privacy constraint: verify no author identity or profile data is leaked
    raw_text = response.text.lower()
    assert "steamid" not in raw_text
    assert "author_id" not in raw_text
    assert "avatar" not in raw_text
    assert "profileurl" not in raw_text


def test_get_review_detail_not_found(client: TestClient) -> None:
    unknown_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/reviews/{unknown_id}")
    assert response.status_code == 404

    data = response.json()
    assert data["data"] is None
    assert data["error"]["code"] == "REVIEW_NOT_FOUND"
    assert unknown_id in data["error"]["message"]


def test_get_review_invalid_uuid(client: TestClient) -> None:
    response = client.get("/api/v1/reviews/not-a-valid-uuid")
    assert response.status_code == 422

    data = response.json()
    assert data["data"] is None
    assert data["error"]["code"] == "VALIDATION_ERROR"
