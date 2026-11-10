"""End-to-end integration tests for ML batch inference, analytics aggregation, and API endpoints."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import GameAnalytic
from app.models.aspect import AspectPrediction
from app.models.game import Game
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.models.topic import ReviewTopic, Topic
from app.services.analytics_service import AnalyticsService
from app.services.inference_pipeline_service import InferencePipelineService


@pytest.fixture
def populated_integration_game(db_session: Session) -> dict[str, Any]:
    """Seed game with 30 diverse reviews spanning 3 weeks for end-to-end integration testing."""
    game = Game(
        steam_app_id=777888,
        name="Integration Odyssey",
        short_description="An epic game used for pipeline and analytics integration testing.",
        genres=["Action", "Adventure"],
        release_date=date(2026, 9, 1),
        is_free=False,
        is_active=True,
    )
    db_session.add(game)
    db_session.flush()

    base_time = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)

    review_templates = [
        ("The combat and gameplay are exhilarating and smooth! Best roguelike ever.", True),
        ("Terrible stuttering and awful performance, crashed 5 times in 1 hour.", False),
        ("Decent graphics and gorgeous soundtrack, but the story is just okay.", True),
        ("Masterpiece visuals and combat. Worth every single penny.", True),
        ("Unplayable due to frame drops and broken controller inputs.", False),
        ("Fun multiplayer with friends, great netcode and fast matching.", True),
    ]

    reviews: list[Review] = []
    for i in range(30):
        tmpl_text, voted_up = review_templates[i % len(review_templates)]
        rev = Review(
            game_id=game.id,
            steam_review_id=888000 + i,
            language="en",
            review_text=f"{tmpl_text} (Review #{i + 1} additional context for corpus size).",
            voted_up=voted_up,
            votes_up=i * 2,
            votes_funny=i % 3,
            comment_count=i % 4,
            steam_created_at=base_time + timedelta(days=i // 2),
        )
        db_session.add(rev)
        reviews.append(rev)

    db_session.commit()

    return {"game": game, "reviews": reviews}


def test_end_to_end_pipeline_and_analytics_flow(
    db_session: Session,
    client: TestClient,
    populated_integration_game: dict[str, Any],
) -> None:
    """Validate full flow: Batch Inference -> DB Persistence -> Aggregation -> Public REST API."""
    game: Game = populated_integration_game["game"]
    game_id = game.id

    # 1. Execute Batch Inference Pipeline (Sentiment + ABSA + Topic Modeling)
    inf_service = InferencePipelineService(session=db_session)
    runs = inf_service.run_full_nlp_pipeline(
        game_id=game_id,
        batch_size=10,
        run_topics=True,
    )

    assert "sentiment" in runs
    assert "absa" in runs
    assert "topic" in runs

    assert runs["sentiment"].status == "succeeded"
    assert runs["sentiment"].success_count == 30
    assert runs["absa"].status == "succeeded"
    assert runs["topic"].status == "succeeded"

    # Verify Sentiment predictions in PostgreSQL
    sent_preds = list(
        db_session.scalars(
            select(SentimentPrediction).where(
                SentimentPrediction.pipeline_run_id == runs["sentiment"].id
            )
        ).all()
    )
    assert len(sent_preds) == 30

    # Verify Aspect predictions in PostgreSQL
    asp_preds = list(
        db_session.scalars(
            select(AspectPrediction).where(AspectPrediction.pipeline_run_id == runs["absa"].id)
        ).all()
    )
    assert len(asp_preds) > 0

    # Verify Topics in PostgreSQL
    topics = list(
        db_session.scalars(
            select(Topic).where(Topic.ml_model_id == runs["topic"].ml_model_id)
        ).all()
    )
    assert len(topics) >= 1

    # Verify ReviewTopic assignments
    review_topics = list(
        db_session.scalars(
            select(ReviewTopic).where(ReviewTopic.pipeline_run_id == runs["topic"].id)
        ).all()
    )
    assert len(review_topics) >= 20

    # 2. Execute Analytics Aggregation Job
    analytics_svc = AnalyticsService(session=db_session)
    agg_result = analytics_svc.aggregate_game(
        game_id=game_id,
        period_types=["day", "week", "month"],
        model_version_key="baseline",
    )
    assert agg_result["buckets_computed"] > 0

    # Verify GameAnalytic records in PostgreSQL
    analytics_records = list(
        db_session.scalars(
            select(GameAnalytic).where(
                GameAnalytic.game_id == game_id,
                GameAnalytic.model_version_key == "baseline",
            )
        ).all()
    )
    assert len(analytics_records) == agg_result["buckets_computed"]

    # Verify PostgreSQL table check constraints on all computed records
    for r in analytics_records:
        assert r.review_count >= 0
        assert r.positive_count + r.negative_count + r.neutral_count <= r.review_count
        assert r.steam_recommended_count + r.steam_not_recommended_count <= r.review_count
        if r.sentiment_score is not None:
            assert -1.0 <= float(r.sentiment_score) <= 1.0

    # 3. Query Public API: GET /api/v1/games/{id}/analytics
    resp_analytics = client.get(f"/api/v1/games/{game_id}/analytics?period=week")
    assert resp_analytics.status_code == 200
    body_analytics = resp_analytics.json()
    assert body_analytics["error"] is None
    assert body_analytics["meta"]["request_id"] is not None
    assert body_analytics["data"]["game_id"] == str(game_id)
    assert body_analytics["data"]["period"] == "week"
    assert len(body_analytics["data"]["points"]) >= 1

    # 4. Query Public API: GET /api/v1/games/{id}/sentiment
    resp_sentiment = client.get(f"/api/v1/games/{game_id}/sentiment?include_trend=true")
    assert resp_sentiment.status_code == 200
    body_sentiment = resp_sentiment.json()
    assert body_sentiment["error"] is None
    sent_data = body_sentiment["data"]
    assert sent_data["total_reviews"] == 30
    assert sent_data["classified_count"] == 30
    assert sent_data["unclassified_count"] == 0
    assert sent_data["coverage_rate"] == 1.0
    assert sent_data["positive_rate"] > 0.0
    assert sent_data["negative_rate"] > 0.0
    assert sent_data["sentiment_score"] is not None
    assert len(sent_data["timeline"]) >= 1

    # 5. Query Public API: GET /api/v1/games/{id}/aspects
    resp_aspects = client.get(f"/api/v1/games/{game_id}/aspects")
    assert resp_aspects.status_code == 200
    body_aspects = resp_aspects.json()
    assert body_aspects["error"] is None
    asp_data = body_aspects["data"]
    assert asp_data["taxonomy_version"] == "aspects-1.0"
    assert len(asp_data["aspects"]) >= 1
    assert asp_data["total_aspect_mentions"] > 0

    # 6. Query Public API: GET /api/v1/games/{id}/topics
    resp_topics = client.get(f"/api/v1/games/{game_id}/topics")
    assert resp_topics.status_code == 200
    body_topics = resp_topics.json()
    assert body_topics["error"] is None
    top_data = body_topics["data"]
    assert len(top_data["topics"]) >= 1
    assert top_data["total_assigned_reviews"] > 0
