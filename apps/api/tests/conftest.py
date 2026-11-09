from collections.abc import Generator
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import engine, get_db
from app.main import app
from app.models.game import Game
from app.models.ml import MLModel, PipelineRun
from app.models.review import Review
from app.models.sentiment import SentimentPrediction


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session rolled back after every test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with overridden get_db injecting test db_session."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_catalog(db_session: Session) -> dict[str, Any]:
    """Deterministic catalog fixture containing games, reviews, and predictions."""
    game1 = db_session.scalars(select(Game).where(Game.steam_app_id == 1145360)).first()
    if game1 is None:
        game1 = Game(
            steam_app_id=1145360,
            name="Hades",
            short_description="Rogue-like dungeon crawler from Supergiant Games.",
            header_image_url="https://example.com/hades.jpg",
            website_url="https://supergiantgames.com",
            developers=["Supergiant Games"],
            publishers=["Supergiant Games"],
            genres=["Action", "RPG", "Indie"],
            categories=["Single-player", "Full controller support"],
            release_date=date(2020, 9, 17),
            is_free=False,
            catalog_status="indexed",
            is_active=True,
        )
        db_session.add(game1)
        db_session.flush()

    game2 = db_session.scalars(select(Game).where(Game.steam_app_id == 367520)).first()
    if game2 is None:
        game2 = Game(
            steam_app_id=367520,
            name="Hollow Knight",
            short_description="Challenging 2D action adventure in an interconnected underworld.",
            header_image_url="https://example.com/hk.jpg",
            developers=["Team Cherry"],
            publishers=["Team Cherry"],
            genres=["Action", "Indie"],
            release_date=date(2017, 2, 24),
            is_free=False,
            catalog_status="indexed",
            is_active=True,
        )
        db_session.add(game2)
        db_session.flush()

    model = db_session.scalars(
        select(MLModel).where(
            MLModel.model_key == "distilbert-sentiment",
            MLModel.version == "v1.0.0",
        )
    ).first()
    if model is None:
        model = MLModel(
            model_key="distilbert-sentiment",
            version="v1.0.0",
            task="sentiment",
            framework="transformers",
            artifact_uri="s3://bucket/model.tar.gz",
            language_scope=["en"],
            label_schema={"positive": 0, "negative": 1, "neutral": 2},
            config={},
            metrics={},
            is_active=True,
        )
        db_session.add(model)
        db_session.flush()

    run = db_session.scalars(
        select(PipelineRun).where(PipelineRun.ml_model_id == model.id)
    ).first()
    if run is None:
        run = PipelineRun(
            pipeline_type="sentiment",
            ml_model_id=model.id,
            game_id=game1.id,
            status="succeeded",
            input_filter={},
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        db_session.add(run)
        db_session.flush()

    review1 = db_session.scalars(
        select(Review).where(
            Review.game_id == game1.id, Review.steam_review_id == 100000001
        )
    ).first()
    if review1 is None:
        review1 = Review(
            game_id=game1.id,
            steam_review_id=100000001,
            review_text="Brilliant game with responsive combat and incredible soundtrack.",
            language="english",
            voted_up=True,
            votes_up=25,
            votes_funny=2,
            comment_count=1,
            steam_playtime_forever=3600,
            steam_created_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        )
        db_session.add(review1)
        db_session.flush()

    review2 = db_session.scalars(
        select(Review).where(
            Review.game_id == game1.id, Review.steam_review_id == 100000002
        )
    ).first()
    if review2 is None:
        review2 = Review(
            game_id=game1.id,
            steam_review_id=100000002,
            review_text="Too difficult and repetitive for my taste.",
            language="english",
            voted_up=False,
            votes_up=4,
            votes_funny=0,
            comment_count=0,
            steam_playtime_forever=120,
            steam_created_at=datetime(2026, 1, 10, 8, 30, tzinfo=UTC),
        )
        db_session.add(review2)
        db_session.flush()

    pred1 = db_session.scalars(
        select(SentimentPrediction).where(
            SentimentPrediction.review_id == review1.id,
            SentimentPrediction.is_current.is_(True),
        )
    ).first()
    if pred1 is None:
        pred1 = SentimentPrediction(
            review_id=review1.id,
            ml_model_id=model.id,
            pipeline_run_id=run.id,
            label="positive",
            confidence=Decimal("0.96000"),
            is_current=True,
        )
        db_session.add(pred1)
        db_session.flush()

    pred2 = db_session.scalars(
        select(SentimentPrediction).where(
            SentimentPrediction.review_id == review2.id,
            SentimentPrediction.is_current.is_(True),
        )
    ).first()
    if pred2 is None:
        pred2 = SentimentPrediction(
            review_id=review2.id,
            ml_model_id=model.id,
            pipeline_run_id=run.id,
            label="negative",
            confidence=Decimal("0.88000"),
            is_current=True,
        )
        db_session.add(pred2)
        db_session.flush()

    return {
        "game1": game1,
        "game2": game2,
        "model": model,
        "run": run,
        "review1": review1,
        "review2": review2,
    }
