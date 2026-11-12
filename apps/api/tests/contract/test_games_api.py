import uuid
from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.game import Game
from app.schemas.common import ResponseEnvelope
from app.schemas.game import GameDetail, GameListItem
from app.schemas.review import ReviewListItem


@pytest.fixture
def discovery_games(db_session: Session, sample_catalog: dict[str, Any]) -> dict[str, Game]:
    """An unreleased pending game and a free-to-play indexed game, alongside sample_catalog."""
    upcoming = Game(
        steam_app_id=990001,
        name="Zz Upcoming Test Game",
        genres=["Strategy"],
        release_date=date.today() + timedelta(days=30),
        is_free=False,
        catalog_status="pending",
        is_active=True,
    )
    free = Game(
        steam_app_id=990002,
        name="Zz Free Test Game",
        genres=["Shooter"],
        release_date=date(2015, 6, 1),
        is_free=True,
        catalog_status="indexed",
        is_active=True,
    )
    db_session.add_all([upcoming, free])
    db_session.flush()
    return {"upcoming": upcoming, "free": free}


def test_list_games_search_by_steam_app_id(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    data = client.get("/api/v1/games?q=1145360").json()["data"]
    assert [g["steam_app_id"] for g in data] == [1145360]


def test_list_games_free_and_year_filters(
    client: TestClient, discovery_games: dict[str, Game]
) -> None:
    free = client.get("/api/v1/games?is_free=true&limit=100").json()["data"]
    assert free and all(g["is_free"] is True for g in free)
    assert "Zz Free Test Game" in {g["name"] for g in free}

    paid = client.get("/api/v1/games?is_free=false&limit=100").json()["data"]
    assert "Zz Free Test Game" not in {g["name"] for g in paid}

    in_2015 = client.get("/api/v1/games?year_from=2015&year_to=2015&limit=100").json()["data"]
    assert in_2015 and all(g["release_date"].startswith("2015") for g in in_2015)


def test_list_games_upcoming(client: TestClient, discovery_games: dict[str, Game]) -> None:
    # Pending + unreleased: hidden from the default catalog...
    default_names = {g["name"] for g in client.get("/api/v1/games?limit=100").json()["data"]}
    assert "Zz Upcoming Test Game" not in default_names

    # ...but listed by the upcoming view, which only holds future-dated games
    data = client.get("/api/v1/games?upcoming=true&sort=release_asc&limit=100").json()["data"]
    assert "Zz Upcoming Test Game" in {g["name"] for g in data}
    today = date.today().isoformat()
    assert all(g["release_date"] > today for g in data)


def test_list_games_catalog_status_is_honoured(
    client: TestClient, discovery_games: dict[str, Game]
) -> None:
    data = client.get("/api/v1/games?catalog_status=pending&limit=100").json()["data"]
    assert data and all(g["catalog_status"] == "pending" for g in data)

    assert client.get("/api/v1/games?catalog_status=disabled").status_code == 422


def test_list_games_release_sort_paginates(
    client: TestClient, discovery_games: dict[str, Game]
) -> None:
    seen: list[str] = []
    cursor: str | None = None
    for _ in range(50):
        url = "/api/v1/games?sort=release_desc&limit=1" + (f"&cursor={cursor}" if cursor else "")
        body = client.get(url).json()
        seen.extend(g["release_date"] for g in body["data"])
        cursor = body["meta"]["pagination"]["next_cursor"]
        if not cursor:
            break
    assert len(seen) >= 3
    assert seen == sorted(seen, reverse=True)


def test_list_games_includes_review_metrics(
    client: TestClient, sample_catalog: dict[str, Any]
) -> None:
    hades = client.get("/api/v1/games?q=1145360").json()["data"][0]
    # sample_catalog: 1 recommended + 1 not recommended; 1 positive + 1 negative prediction
    assert hades["review_count"] >= 2
    assert 0 <= hades["steam_positive_percentage"] <= 100
    assert 0 <= hades["model_sentiment_positive_rate"] <= 1


def test_list_game_genres(client: TestClient, sample_catalog: dict[str, Any]) -> None:
    response = client.get("/api/v1/games/genres")
    assert response.status_code == 200
    genres = response.json()["data"]
    assert {"Action", "RPG", "Indie"} <= set(genres)
    assert genres == sorted(genres)


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
