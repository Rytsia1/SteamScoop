import uuid
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import GameNotFoundError, ReviewNotFoundError
from app.repositories.game import GameRepository
from app.repositories.review import ReviewRepository
from app.schemas.game import GameQueryParams
from app.schemas.review import ReviewQueryParams
from app.services.game_service import GameService
from app.services.review_service import ReviewService


def test_game_service_get_by_id_success(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    game_repo = GameRepository(db_session)
    service = GameService(game_repo)

    game = sample_catalog["game1"]
    detail = service.get_game_by_id(game.id)
    assert detail.id == game.id
    assert detail.steam_app_id == 1145360
    assert detail.name == "Hades"
    assert detail.data_coverage is not None
    assert detail.data_coverage.stored_reviews_count >= 1


def test_game_service_get_by_id_not_found(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    service = GameService(game_repo)

    random_id = uuid.uuid4()
    with pytest.raises(GameNotFoundError) as exc_info:
        service.get_game_by_id(random_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "GAME_NOT_FOUND"


def test_game_service_get_by_steam_app_id_success(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    game_repo = GameRepository(db_session)
    service = GameService(game_repo)

    detail = service.get_game_by_steam_app_id(1145360)
    assert detail.steam_app_id == 1145360
    assert detail.name == "Hades"


def test_game_service_get_by_steam_app_id_not_found(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    service = GameService(game_repo)

    with pytest.raises(GameNotFoundError) as exc_info:
        service.get_game_by_steam_app_id(999999999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "GAME_NOT_FOUND"


def test_game_service_search_games(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    game_repo = GameRepository(db_session)
    service = GameService(game_repo)

    # Search with q
    items, pagination = service.search_games(GameQueryParams(q="Hades", limit=10))
    assert len(items) >= 1
    assert any("Hades" in g.name for g in items)
    assert pagination.limit == 10

    # Search with limit=1 to test cursor pagination
    items_p1, p1_meta = service.search_games(GameQueryParams(limit=1))
    assert len(items_p1) == 1
    if p1_meta.has_more:
        assert p1_meta.next_cursor is not None
        # Follow cursor
        items_p2, _ = service.search_games(GameQueryParams(limit=1, cursor=p1_meta.next_cursor))
        assert len(items_p2) == 1
        assert items_p2[0].id != items_p1[0].id


def test_review_service_get_review_success(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    game_repo = GameRepository(db_session)
    review_repo = ReviewRepository(db_session)
    service = ReviewService(game_repo, review_repo)

    review = sample_catalog["review1"]
    detail = service.get_review(review.id)
    assert detail.id == review.id
    assert detail.steam_review_id == review.steam_review_id
    assert detail.review_text == review.review_text
    assert detail.voted_up == review.voted_up
    assert detail.sentiment is not None
    assert detail.sentiment.label in ("positive", "negative", "neutral")


def test_review_service_get_review_not_found(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    review_repo = ReviewRepository(db_session)
    service = ReviewService(game_repo, review_repo)

    random_id = uuid.uuid4()
    with pytest.raises(ReviewNotFoundError) as exc_info:
        service.get_review(random_id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "REVIEW_NOT_FOUND"


def test_review_service_get_game_reviews_success(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    game_repo = GameRepository(db_session)
    review_repo = ReviewRepository(db_session)
    service = ReviewService(game_repo, review_repo)

    game = sample_catalog["game1"]
    items, pagination = service.get_game_reviews(game.id, ReviewQueryParams(limit=5))
    assert len(items) >= 1
    assert pagination.limit == 5
    for item in items:
        assert item.id is not None
        assert item.review_text is not None


def test_review_service_get_game_reviews_game_not_found(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    review_repo = ReviewRepository(db_session)
    service = ReviewService(game_repo, review_repo)

    random_id = uuid.uuid4()
    with pytest.raises(GameNotFoundError) as exc_info:
        service.get_game_reviews(random_id, ReviewQueryParams())
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "GAME_NOT_FOUND"
