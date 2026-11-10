"""Unit tests for AnalyticsService business logic, date bucketing, and query models."""

import uuid
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import GameNotFoundError
from app.models.game import Game
from app.services.analytics_service import AnalyticsService
from app.services.inference_pipeline_service import InferencePipelineService


def test_aggregate_game_success(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Validate game analytics aggregation for all period types."""
    game = sample_catalog["game1"]

    # First run batch inference so reviews have predictions
    inf_service = InferencePipelineService(session=db_session)
    inf_service.run_sentiment_batch_inference(game_id=game.id)
    inf_service.run_absa_batch_inference(game_id=game.id)

    analytics_svc = AnalyticsService(session=db_session)
    result = analytics_svc.aggregate_game(
        game_id=game.id,
        period_types=["day", "week", "month"],
        model_version_key="baseline",
    )

    assert result["game_id"] == str(game.id)
    assert result["model_version_key"] == "baseline"
    assert result["buckets_computed"] >= 3

    # Query timeline back
    timeline = analytics_svc.get_game_analytics(
        game_id=game.id,
        period_type="week",
        model_version_key="baseline",
    )
    assert timeline.game_id == game.id
    assert timeline.period == "week"
    assert len(timeline.points) >= 1

    point = timeline.points[0]
    assert point.period_end > point.period_start
    assert point.review_count >= 1
    assert point.positive_count + point.negative_count + point.neutral_count <= point.review_count


def test_aggregate_game_no_reviews(db_session: Session) -> None:
    """Validate graceful handling when aggregating a game with zero reviews."""
    empty_game = Game(
        steam_app_id=9876543,
        name="Empty Game",
        short_description="Game with no reviews yet.",
        is_free=False,
        is_active=True,
    )
    db_session.add(empty_game)
    db_session.flush()

    service = AnalyticsService(session=db_session)
    result = service.aggregate_game(empty_game.id)

    assert result["buckets_computed"] == 0
    assert "No reviews found" in result["message"]


def test_aggregate_game_not_found(db_session: Session) -> None:
    """Validate GameNotFoundError when aggregating an unindexed game UUID."""
    service = AnalyticsService(session=db_session)
    random_id = uuid.uuid4()

    with pytest.raises(GameNotFoundError):
        service.aggregate_game(random_id)


def test_get_game_sentiment_distribution(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Validate retrieval of sentiment distribution and rates with explicit denominators."""
    game = sample_catalog["game1"]

    inf_service = InferencePipelineService(session=db_session)
    inf_service.run_sentiment_batch_inference(game_id=game.id)

    service = AnalyticsService(session=db_session)
    service.aggregate_game(game_id=game.id, period_types=["week"])

    sentiment_data = service.get_game_sentiment_distribution(
        game_id=game.id,
        include_trend=True,
    )

    assert sentiment_data.game_id == game.id
    assert sentiment_data.total_reviews >= 1
    assert sentiment_data.classified_count >= 1
    assert (
        sentiment_data.classified_count
        == sentiment_data.positive_count
        + sentiment_data.negative_count
        + sentiment_data.neutral_count
    )
    assert sentiment_data.positive_rate >= 0.0
    assert sentiment_data.coverage_rate > 0.0
    assert sentiment_data.timeline is not None
    assert len(sentiment_data.timeline) >= 1


def test_get_game_aspects(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Validate aspect-level distribution query and sort ordering."""
    game = sample_catalog["game1"]

    inf_service = InferencePipelineService(session=db_session)
    inf_service.run_absa_batch_inference(game_id=game.id)

    service = AnalyticsService(session=db_session)
    service.aggregate_game(game_id=game.id, period_types=["week"])

    aspects_data = service.get_game_aspects(game_id=game.id, sort="mentions_desc")

    assert aspects_data.game_id == game.id
    assert aspects_data.taxonomy_version == "aspects-1.0"
    assert len(aspects_data.aspects) >= 1

    first_aspect = aspects_data.aspects[0]
    assert first_aspect.mention_count >= 1
    assert first_aspect.aspect_key != ""
    assert -1.0 <= (first_aspect.sentiment_score or 0.0) <= 1.0
