from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories.analytics import AnalyticsRepository
from app.repositories.game import GameRepository
from app.repositories.ingestion import (
    CollectionCheckpointRepository,
    IngestionBatchRepository,
    IngestionJobRepository,
    commit_ingestion_page_transaction,
)
from app.repositories.review import ReviewRepository


def test_game_repository_crud_and_search(db_session: Session) -> None:
    repo = GameRepository(db_session)

    # Upsert new
    game, is_created = repo.upsert_game(
        steam_app_id=888001,
        name="Silksong Chronicle",
        catalog_status="indexed",
        is_active=True,
    )
    assert is_created is True
    assert game.name == "Silksong Chronicle"

    # Upsert existing
    game_updated, is_created = repo.upsert_game(
        steam_app_id=888001,
        name="Hollow Knight: Silksong",
    )
    assert is_created is False
    assert game_updated.id == game.id
    assert game_updated.name == "Hollow Knight: Silksong"

    # Lookup by Steam App ID
    found = repo.get_by_steam_app_id(888001)
    assert found is not None
    assert found.id == game.id

    # Search
    search_results = repo.search_by_name("Silksong")
    assert len(search_results) >= 1
    assert any(g.id == game.id for g in search_results)


def test_review_repository_idempotent_upsert(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    game, _ = game_repo.upsert_game(steam_app_id=888002, name="Review Repo Game")

    review_repo = ReviewRepository(db_session)

    # First collection
    rev1, is_created1 = review_repo.upsert_review(
        game_id=game.id,
        steam_review_id=777001,
        review_text="Initial review text.",
        voted_up=True,
        votes_up=10,
        steam_playtime_forever=120,
    )
    assert is_created1 is True
    assert rev1.review_text == "Initial review text."

    # Re-fetch review with edited text and playtime
    rev2, is_created2 = review_repo.upsert_review(
        game_id=game.id,
        steam_review_id=777001,
        review_text="Updated review text after 50 hours.",
        voted_up=True,
        votes_up=25,
        steam_playtime_forever=3000,
    )
    assert is_created2 is False
    assert rev2.id == rev1.id
    assert rev2.review_text == "Updated review text after 50 hours."
    assert rev2.votes_up == 25
    assert rev2.steam_playtime_forever == 3000

    # Verify no duplicate review row was inserted
    assert review_repo.count_reviews_by_game(game.id) == 1


def test_review_repository_queries_and_filters(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    game, _ = game_repo.upsert_game(steam_app_id=888003, name="Filtered Review Game")

    review_repo = ReviewRepository(db_session)
    now = datetime.now(UTC)

    review_repo.upsert_review(
        game_id=game.id,
        steam_review_id=777002,
        review_text="English positive",
        voted_up=True,
        language="en",
        steam_created_at=now - timedelta(days=2),
    )
    review_repo.upsert_review(
        game_id=game.id,
        steam_review_id=777003,
        review_text="English negative",
        voted_up=False,
        language="en",
        steam_created_at=now - timedelta(days=1),
    )
    review_repo.upsert_review(
        game_id=game.id,
        steam_review_id=777004,
        review_text="German positive",
        voted_up=True,
        language="de",
        steam_created_at=now,
    )

    assert review_repo.count_reviews_by_game(game.id) == 3

    # Filter by voted_up = True
    pos_reviews = review_repo.get_reviews_by_game(game.id, voted_up=True)
    assert len(pos_reviews) == 2

    # Filter by language = "en"
    en_reviews = review_repo.get_reviews_by_game(game.id, language="en")
    assert len(en_reviews) == 2


def test_ingestion_repositories_and_atomic_batch_commit(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    game, _ = game_repo.upsert_game(steam_app_id=888004, name="Ingestion Repo Game")

    job_repo = IngestionJobRepository(db_session)
    job = job_repo.create_job(
        game_id=game.id,
        job_type="historical",
        request_config={"language": "all"},
    )
    assert job.id is not None
    assert job.status == "queued"

    active_job = job_repo.get_active_job_for_game(game.id, "historical")
    assert active_job is not None
    assert active_job.id == job.id

    # Test atomic commit of an ingestion page
    reviews_batch_data = [
        {
            "steam_review_id": 777005,
            "review_text": "Batch review 1",
            "voted_up": True,
            "votes_up": 5,
            "language": "en",
        },
        {
            "steam_review_id": 777006,
            "review_text": "Batch review 2",
            "voted_up": False,
            "votes_up": 2,
            "language": "en",
        },
    ]

    batch = commit_ingestion_page_transaction(
        session=db_session,
        job_id=job.id,
        game_id=game.id,
        batch_number=1,
        cursor_in="cursor_0",
        cursor_out="cursor_1",
        request_started_at=datetime.now(UTC),
        request_finished_at=datetime.now(UTC),
        http_status=200,
        reviews_data=reviews_batch_data,
        checkpoint_stream_key="historical:all:all",
        collection_mode="historical",
        watermark_at=datetime.now(UTC),
    )
    assert batch.id is not None
    assert batch.inserted_count == 2
    assert batch.batch_status == "succeeded"

    # Check that job counters were updated
    db_session.refresh(job)
    assert job.reviews_seen == 2
    assert job.reviews_inserted == 2
    assert job.pages_processed == 1

    # Check checkpoint state
    ckpt_repo = CollectionCheckpointRepository(db_session)
    ckpt = ckpt_repo.get_by_stream_key(game.id, "historical:all:all")
    assert ckpt is not None
    assert ckpt.cursor == "cursor_1"
    assert ckpt.last_successful_job_id == job.id

    # Check batch list
    batch_repo = IngestionBatchRepository(db_session)
    batches = batch_repo.get_batches_for_job(job.id)
    assert len(batches) == 1


def test_atomic_batch_commit_rollback_on_failure(db_session: Session) -> None:
    """If an invalid review in the page causes a DB error, the entire batch transaction

    rolls back so no partial reviews or updated cursor are persisted.
    """
    game_repo = GameRepository(db_session)
    game, _ = game_repo.upsert_game(steam_app_id=888005, name="Rollback Game")

    job_repo = IngestionJobRepository(db_session)
    job = job_repo.create_job(game_id=game.id, job_type="historical")

    reviews_with_invalid = [
        {
            "steam_review_id": 777007,
            "review_text": "Valid review",
            "voted_up": True,
        },
        {
            "steam_review_id": 777008,
            "review_text": "   ",  # Invalid empty review violates ck_review_text_not_empty
            "voted_up": True,
        },
    ]

    with pytest.raises(IntegrityError):
        commit_ingestion_page_transaction(
            session=db_session,
            job_id=job.id,
            game_id=game.id,
            batch_number=1,
            cursor_in="cursor_0",
            cursor_out="cursor_should_not_commit",
            request_started_at=datetime.now(UTC),
            request_finished_at=datetime.now(UTC),
            http_status=200,
            reviews_data=reviews_with_invalid,
            checkpoint_stream_key="historical:all:all",
            collection_mode="historical",
        )

    # Verify rollback: no reviews inserted, no batch created, checkpoint not updated
    review_repo = ReviewRepository(db_session)
    assert review_repo.get_by_steam_review_id(game.id, 777007) is None

    batch_repo = IngestionBatchRepository(db_session)
    assert len(batch_repo.get_batches_for_job(job.id)) == 0

    ckpt_repo = CollectionCheckpointRepository(db_session)
    assert ckpt_repo.get_by_stream_key(game.id, "historical:all:all") is None


def test_analytics_repository_upsert_and_timeline(db_session: Session) -> None:
    game_repo = GameRepository(db_session)
    game, _ = game_repo.upsert_game(steam_app_id=888006, name="Analytics Repo Game")

    analytics_repo = AnalyticsRepository(db_session)
    start_d = date(2026, 3, 1)
    end_d = date(2026, 3, 7)

    # Upsert new analytic
    analytic, is_created = analytics_repo.upsert_analytic(
        game_id=game.id,
        period_type="week",
        period_start=start_d,
        period_end=end_d,
        review_count=100,
        positive_count=80,
        negative_count=15,
        neutral_count=5,
        steam_recommended_count=85,
        steam_not_recommended_count=15,
        sentiment_score=Decimal("0.65000"),
        aspect_summary={"gameplay": {"positive": 50, "negative": 5}},
    )
    assert is_created is True
    assert analytic.review_count == 100

    # Upsert update
    analytic_updated, is_created_update = analytics_repo.upsert_analytic(
        game_id=game.id,
        period_type="week",
        period_start=start_d,
        period_end=end_d,
        review_count=120,
        positive_count=95,
        negative_count=20,
        neutral_count=5,
        steam_recommended_count=100,
        steam_not_recommended_count=20,
        sentiment_score=Decimal("0.62500"),
    )
    assert is_created_update is False
    assert analytic_updated.id == analytic.id
    assert analytic_updated.review_count == 120

    # Query timeline
    timeline = analytics_repo.get_timeline(
        game_id=game.id,
        period_type="week",
        start_date=date(2026, 1, 1),
    )
    assert len(timeline) == 1
    assert timeline[0].review_count == 120
