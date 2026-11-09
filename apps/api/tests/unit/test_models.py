from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.analytics import GameAnalytic
from app.models.aspect import Aspect, AspectPrediction
from app.models.game import Game
from app.models.ingestion import IngestionBatch, IngestionJob
from app.models.ml import MLModel, PipelineRun
from app.models.review import Review
from app.models.sentiment import SentimentPrediction


def test_game_creation_and_constraints(db_session: Session) -> None:
    """Test Game model valid creation and constraints."""
    game = Game(
        steam_app_id=999901,
        name="Test Game Alpha",
        catalog_status="pending",
        is_active=True,
    )
    db_session.add(game)
    db_session.flush()
    assert game.id is not None
    assert game.developers == []
    assert game.catalog_status == "pending"


def test_game_steam_app_id_positive_constraint(db_session: Session) -> None:
    """Enforce steam_app_id > 0."""
    invalid_game = Game(
        steam_app_id=0,
        name="Invalid App ID Game",
    )
    db_session.add(invalid_game)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_game_catalog_status_constraint(db_session: Session) -> None:
    """Enforce catalog_status IN ('pending', 'indexed', 'failed', 'disabled')."""
    invalid_game = Game(
        steam_app_id=999902,
        name="Invalid Status Game",
        catalog_status="unknown_status",
    )
    db_session.add(invalid_game)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_game_unique_steam_app_id(db_session: Session) -> None:
    """Enforce uniqueness of steam_app_id."""
    g1 = Game(steam_app_id=999903, name="Game One")
    db_session.add(g1)
    db_session.flush()

    g2 = Game(steam_app_id=999903, name="Game Duplicate")
    db_session.add(g2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_review_creation_and_empty_text_check(db_session: Session) -> None:
    """Enforce review_text cannot be empty after trimming."""
    game = Game(steam_app_id=999904, name="Game for Review")
    db_session.add(game)
    db_session.flush()

    empty_rev = Review(
        game_id=game.id,
        steam_review_id=888801,
        review_text="    ",
        voted_up=True,
    )
    db_session.add(empty_rev)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_review_unique_game_and_steam_review_id(db_session: Session) -> None:
    """Enforce idempotency uniqueness of (game_id, steam_review_id)."""
    game = Game(steam_app_id=999905, name="Game for Review Idempotency")
    db_session.add(game)
    db_session.flush()

    r1 = Review(
        game_id=game.id,
        steam_review_id=888802,
        review_text="Legitimate review text",
        voted_up=True,
    )
    db_session.add(r1)
    db_session.flush()

    r2 = Review(
        game_id=game.id,
        steam_review_id=888802,
        review_text="Duplicate review payload",
        voted_up=False,
    )
    db_session.add(r2)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_foreign_key_delete_restrict_on_game_with_reviews(db_session: Session) -> None:
    """Deleting a game that has associated reviews must be restricted (ON DELETE RESTRICT)."""
    game = Game(steam_app_id=999906, name="Protected Game")
    db_session.add(game)
    db_session.flush()

    rev = Review(
        game_id=game.id,
        steam_review_id=888803,
        review_text="Preserved review",
        voted_up=True,
    )
    db_session.add(rev)
    db_session.flush()

    db_session.delete(game)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_foreign_key_delete_cascade_on_ingestion_job(db_session: Session) -> None:
    """Deleting an ingestion job must cascade to its ingestion batches (ON DELETE CASCADE)."""
    game = Game(steam_app_id=999907, name="Job Game")
    db_session.add(game)
    db_session.flush()

    job = IngestionJob(
        game_id=game.id,
        job_type="historical",
        status="succeeded",
    )
    db_session.add(job)
    db_session.flush()

    batch = IngestionBatch(
        ingestion_job_id=job.id,
        game_id=game.id,
        batch_number=1,
        request_started_at=datetime.now(UTC),
    )
    db_session.add(batch)
    db_session.flush()

    batch_id = batch.id
    db_session.delete(job)
    db_session.flush()

    # Batch should be deleted
    assert db_session.get(IngestionBatch, batch_id) is None


def test_sentiment_prediction_constraints(db_session: Session) -> None:
    """Enforce valid sentiment label and confidence bounds [0, 1]."""
    game = Game(steam_app_id=999908, name="Sentiment Game")
    db_session.add(game)
    db_session.flush()

    rev = Review(
        game_id=game.id,
        steam_review_id=888804,
        review_text="Sentiment review",
        voted_up=True,
    )
    db_session.add(rev)

    model = MLModel(
        model_key="test-sent",
        version="v1.0.0",
        task="sentiment",
        framework="transformers",
    )
    db_session.add(model)
    db_session.flush()

    prun = PipelineRun(
        pipeline_type="sentiment",
        ml_model_id=model.id,
        game_id=game.id,
        status="succeeded",
    )
    db_session.add(prun)
    db_session.flush()

    # Invalid label
    invalid_pred = SentimentPrediction(
        review_id=rev.id,
        ml_model_id=model.id,
        pipeline_run_id=prun.id,
        label="ecstatic",
        confidence=Decimal("0.90000"),
    )
    db_session.add(invalid_pred)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_aspect_prediction_offset_constraint(db_session: Session) -> None:
    """Enforce aspect offsets: end_offset >= start_offset."""
    game = Game(steam_app_id=999909, name="Aspect Game")
    db_session.add(game)
    db_session.flush()

    rev = Review(
        game_id=game.id,
        steam_review_id=888805,
        review_text="Aspect review body",
        voted_up=True,
    )
    db_session.add(rev)

    aspect = Aspect(aspect_key="combat", display_name="Combat")
    db_session.add(aspect)

    model = MLModel(
        model_key="test-absa",
        version="v1.0.0",
        task="absa",
        framework="transformers",
    )
    db_session.add(model)
    db_session.flush()

    prun = PipelineRun(
        pipeline_type="absa",
        ml_model_id=model.id,
        game_id=game.id,
        status="succeeded",
    )
    db_session.add(prun)
    db_session.flush()

    # Invalid offset (end < start)
    invalid_aspect = AspectPrediction(
        review_id=rev.id,
        aspect_id=aspect.id,
        ml_model_id=model.id,
        pipeline_run_id=prun.id,
        sentiment_label="positive",
        start_offset=20,
        end_offset=10,
    )
    db_session.add(invalid_aspect)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_game_analytic_date_and_sum_constraints(db_session: Session) -> None:
    """Enforce period_end > period_start and positive + negative + neutral <= review_count."""
    game = Game(steam_app_id=999910, name="Analytic Game")
    db_session.add(game)
    db_session.flush()

    # Test period_end <= period_start violation
    invalid_dates = GameAnalytic(
        game_id=game.id,
        period_type="week",
        period_start=date(2026, 3, 15),
        period_end=date(2026, 3, 10),
        review_count=10,
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(invalid_dates)
        db_session.flush()

    # Test sentiment sum > review_count violation
    invalid_sum = GameAnalytic(
        game_id=game.id,
        period_type="week",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 3, 7),
        review_count=5,
        positive_count=4,
        negative_count=3,  # 4 + 3 = 7 > 5 review_count
        neutral_count=0,
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(invalid_sum)
        db_session.flush()


def test_active_ingestion_job_partial_index(db_session: Session) -> None:
    """Enforce only one active (queued, running, retrying) ingestion job per game and job_type."""
    game = Game(steam_app_id=999911, name="Job Game 2")
    db_session.add(game)
    db_session.flush()

    job1 = IngestionJob(
        game_id=game.id,
        job_type="historical",
        status="running",
    )
    db_session.add(job1)
    db_session.flush()

    job2 = IngestionJob(
        game_id=game.id,
        job_type="historical",
        status="queued",
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(job2)
        db_session.flush()

    # But allows multiple succeeded jobs
    job_succ1 = IngestionJob(game_id=game.id, job_type="historical", status="succeeded")
    job_succ2 = IngestionJob(game_id=game.id, job_type="historical", status="succeeded")
    db_session.add(job_succ1)
    db_session.add(job_succ2)
    db_session.flush()
    assert job_succ1.id is not None
    assert job_succ2.id is not None
