import uuid
from typing import Any

from fastapi.testclient import TestClient

from app.schemas.common import ResponseEnvelope
from app.schemas.game import GameDetail, GameListItem
from app.schemas.review import ReviewListItem


def test_list_games_contract(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    custom_req_id = "test-game-req-001"
    response = client.get("/api/v1/games", headers={"X-Request-ID": custom_req_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_req_id

    data = response.json()
    validated = ResponseEnvelope[list[GameListItem]].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert len(validated.data) > 0
    assert validated.meta.request_id == custom_req_id
    assert validated.meta.pagination is not None
    assert validated.meta.pagination.limit == 20

    # Ensure first game has required fields
    first = validated.data[0]
    assert first.id is not None
    assert first.steam_app_id > 0
    assert first.name != ""
    assert first.catalog_status == "indexed"


def test_list_games_filter_and_search(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    # Filter by query 'Hades'
    response = client.get("/api/v1/games?q=Hades")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    for game in data["data"]:
        assert "hades" in game["name"].lower()

    # Filter by genre 'RPG'
    response_rpg = client.get("/api/v1/games?genre=RPG")
    assert response_rpg.status_code == 200
    assert len(response_rpg.json()["data"]) >= 1


def test_list_games_pagination_cursor(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    res1 = client.get("/api/v1/games?limit=1")
    assert res1.status_code == 200
    meta1 = res1.json()["meta"]["pagination"]
    assert meta1["limit"] == 1

    if meta1["has_more"]:
        cursor = meta1["next_cursor"]
        assert cursor is not None

        res2 = client.get(f"/api/v1/games?limit=1&cursor={cursor}")
        assert res2.status_code == 200
        data1 = res1.json()["data"]
        data2 = res2.json()["data"]
        assert data1[0]["id"] != data2[0]["id"]


def test_list_games_validation_error(client: TestClient) -> None:
    # limit exceeds 100
    response = client.get("/api/v1/games?limit=999")
    assert response.status_code == 422
    data = response.json()

    assert data["data"] is None
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0


def test_get_game_by_id_contract(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game_id = str(sample_catalog["game1"].id)

    response = client.get(f"/api/v1/games/{game_id}")
    assert response.status_code == 200

    data = response.json()
    validated = ResponseEnvelope[GameDetail].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert str(validated.data.id) == game_id
    assert validated.data.data_coverage is not None
    assert validated.data.data_coverage.stored_reviews_count >= 0


def test_get_game_by_id_not_found(client: TestClient) -> None:
    unknown_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/games/{unknown_id}")
    assert response.status_code == 404

    data = response.json()
    assert data["data"] is None
    assert data["error"]["code"] == "GAME_NOT_FOUND"
    assert unknown_id in data["error"]["message"]


def test_get_game_by_steam_app_id_contract(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    # 1145360 is Hades
    response = client.get("/api/v1/games/by-steam-id/1145360")
    assert response.status_code == 200

    data = response.json()
    validated = ResponseEnvelope[GameDetail].model_validate(data)
    assert validated.data is not None
    assert validated.data.steam_app_id == 1145360
    assert validated.data.name == "Hades"


def test_get_game_by_steam_app_id_not_found(client: TestClient) -> None:
    response = client.get("/api/v1/games/by-steam-id/999999999")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "GAME_NOT_FOUND"


def test_list_game_reviews_contract(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game_id = str(sample_catalog["game1"].id)

    response = client.get(f"/api/v1/games/{game_id}/reviews?limit=5")
    assert response.status_code == 200

    data = response.json()
    validated = ResponseEnvelope[list[ReviewListItem]].model_validate(data)

    assert validated.error is None
    assert validated.data is not None
    assert len(validated.data) > 0
    assert validated.meta.pagination is not None
    assert validated.meta.pagination.limit == 5

    review = validated.data[0]
    assert review.steam_review_id > 0
    assert review.review_text != ""
    assert isinstance(review.voted_up, bool)


def test_list_game_reviews_filtering(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    game_id = str(sample_catalog["game1"].id)

    # Filter steam_recommended=true
    res_rec = client.get(f"/api/v1/games/{game_id}/reviews?steam_recommended=true")
    assert res_rec.status_code == 200
    for r in res_rec.json()["data"]:
        assert r["voted_up"] is True

    # Filter sentiment=positive
    res_pos = client.get(f"/api/v1/games/{game_id}/reviews?sentiment=positive")
    assert res_pos.status_code == 200
    for r in res_pos.json()["data"]:
        if r["sentiment"] is not None:
            assert r["sentiment"]["label"] == "positive"


def test_list_game_reviews_invalid_cursor(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    game_id = str(sample_catalog["game1"].id)

    response = client.get(f"/api/v1/games/{game_id}/reviews?cursor=invalid-cursor-value!!!")
    assert response.status_code == 400
    data = response.json()
    assert data["data"] is None
    assert data["error"]["code"] == "INVALID_CURSOR"
