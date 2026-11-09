import json
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.ingestion.pipeline import ReviewIngestionPipeline
from app.ingestion.schemas import IngestionJobConfig
from app.ingestion.service import IngestionService
from app.integrations.steam.client import SteamClient
from app.integrations.steam.exceptions import (
    SteamRateLimitError,
)
from app.integrations.steam.transport import SteamTransport
from app.models.ingestion import IngestionBatch
from app.models.review import Review
from app.workers.tasks import cancel_ingestion_job, ingest_game_reviews


def create_mock_steam_client(handler: Any, max_retries: int | None = None) -> SteamClient:
    """Helper to create an isolated SteamClient with a mock HTTPX transport."""
    mock_transport = httpx.MockTransport(handler)
    httpx_client = httpx.Client(transport=mock_transport)
    transport = SteamTransport(
        client=httpx_client, max_retries=max_retries, sleep_fn=lambda _: None
    )
    return SteamClient(transport=transport)


def build_steam_reviews_page(
    review_ids: list[int],
    cursor: str,
    has_more: bool = True,
    voted_up: bool = True,
    updated_at: int | None = None,
) -> dict[str, Any]:
    """Build a standard Steam GetAppReviews/v1 JSON payload."""
    reviews = []
    ts = updated_at or int(datetime.now(UTC).timestamp())
    for rid in review_ids:
        reviews.append(
            {
                "recommendationid": str(rid),
                "author": {
                    "steamid": "76561198000000000",
                    "num_games_owned": 100,
                    "num_reviews": 10,
                    "playtime_forever": 1200,
                    "playtime_last_two_weeks": 60,
                    "playtime_at_review": 600,
                    "last_played": ts,
                },
                "language": "english",
                "review": f"Sample review content for id {rid}.",
                "timestamp_created": ts - 3600,
                "timestamp_updated": ts,
                "voted_up": voted_up,
                "votes_up": 10,
                "votes_funny": 1,
                "weighted_vote_score": "0.750000000000000000",
                "comment_count": 0,
                "steam_purchase": True,
                "received_for_free": False,
                "written_during_early_access": False,
            }
        )

    return {
        "response": {
            "reviews": reviews,
            "cursor": cursor,
            "query_summary": {
                "num_reviews": len(reviews),
                "total_positive": len(reviews) if voted_up else 0,
                "total_negative": 0 if voted_up else len(reviews),
                "total_reviews": len(reviews),
            },
            "success": 1,
        }
    }


def test_historical_collection_success_atomicity(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Verify multi-page historical review collection, atomic batch commits,

    cursor advancement, and job completion.
    """
    game = sample_catalog["game1"]
    service = IngestionService(db_session)
    job = service.create_historical_job(game.id, IngestionJobConfig(max_pages=5))

    page_requests: list[str] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        input_json_str = request.url.params.get("input_json", "{}")
        input_json = json.loads(input_json_str)
        cursor = input_json.get("cursor", "*")
        page_requests.append(cursor)

        if cursor == "*":
            payload = build_steam_reviews_page(
                [300001, 300002], cursor="cursor_page_1", has_more=True
            )
        elif cursor == "cursor_page_1":
            payload = build_steam_reviews_page([300003], cursor="cursor_page_1", has_more=False)
        else:
            payload = {"response": {"reviews": [], "cursor": cursor, "success": 1}}

        return httpx.Response(200, json=payload)

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    result = pipeline.execute_job(job.id)

    assert result.status == "succeeded"
    assert result.pages_processed == 2
    assert result.reviews_seen == 3
    assert result.reviews_inserted == 3
    assert result.cursor == "cursor_page_1"

    # Verify Job state
    db_session.refresh(job)
    assert job.status == "succeeded"
    assert job.pages_processed == 2
    assert job.reviews_seen == 3
    assert job.reviews_inserted == 3
    assert job.finished_at is not None

    # Verify Checkpoint state
    ckpt = service.get_checkpoint(game.id, "historical:all")
    assert ckpt is not None
    assert ckpt.cursor == "cursor_page_1"
    assert ckpt.status == "idle"
    assert ckpt.last_successful_job_id == job.id

    # Verify Ingestion Batches recorded
    batches = db_session.scalars(
        select(IngestionBatch)
        .where(IngestionBatch.ingestion_job_id == job.id)
        .order_by(IngestionBatch.batch_number.asc())
    ).all()
    assert len(batches) == 2
    assert batches[0].batch_number == 1
    assert batches[0].cursor_in == "*"
    assert batches[0].cursor_out == "cursor_page_1"
    assert batches[0].inserted_count == 2

    assert batches[1].batch_number == 2
    assert batches[1].cursor_in == "cursor_page_1"
    assert batches[1].cursor_out == "cursor_page_1"
    assert batches[1].inserted_count == 1

    # Verify reviews persisted
    reviews = db_session.scalars(
        select(Review).where(
            Review.game_id == game.id, Review.steam_review_id.in_([300001, 300002, 300003])
        )
    ).all()
    assert len(reviews) == 3


def test_empty_response_handling(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Steam returns 0 reviews; verifies clean termination, 0 records inserted, checkpoint idle."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)
    job = service.create_historical_job(game.id)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "response": {
                    "reviews": [],
                    "cursor": "*",
                    "query_summary": {"num_reviews": 0, "total_reviews": 0},
                    "success": 1,
                }
            },
        )

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    result = pipeline.execute_job(job.id)

    assert result.status == "succeeded"
    assert result.pages_processed == 1
    assert result.reviews_seen == 0
    assert result.reviews_inserted == 0

    db_session.refresh(job)
    assert job.status == "succeeded"
    assert job.reviews_seen == 0
    assert job.reviews_inserted == 0

    ckpt = service.get_checkpoint(game.id, "historical:all")
    assert ckpt is not None
    assert ckpt.status == "idle"


def test_duplicate_reviews_idempotency(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Verifies in-batch deduplication and cross-run idempotent updates with zero duplicated rows."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)

    # 1. Payload with duplicate review id in same page
    duplicate_payload = {
        "response": {
            "reviews": [
                {
                    "recommendationid": "500001",
                    "author": {"steamid": "1", "playtime_forever": 100},
                    "language": "english",
                    "review": "First version",
                    "timestamp_created": 1600000000,
                    "timestamp_updated": 1600000000,
                    "voted_up": True,
                    "votes_up": 5,
                },
                {
                    "recommendationid": "500001",  # Same review ID in same batch
                    "author": {"steamid": "1", "playtime_forever": 120},
                    "language": "english",
                    "review": "Updated version in same batch",
                    "timestamp_created": 1600000000,
                    "timestamp_updated": 1600000500,
                    "voted_up": True,
                    "votes_up": 8,
                },
            ],
            "cursor": "cursor_dup",
            "query_summary": {"num_reviews": 2, "total_reviews": 2},
            "success": 1,
        }
    }

    def mock_handler_run1(request: httpx.Request) -> httpx.Response:
        input_json = json.loads(request.url.params.get("input_json", "{}"))
        cursor = input_json.get("cursor", "*")
        if cursor == "*":
            return httpx.Response(200, json=duplicate_payload)
        return httpx.Response(
            200, json={"response": {"reviews": [], "cursor": "cursor_dup", "success": 1}}
        )

    job1 = service.create_historical_job(game.id)
    client1 = create_mock_steam_client(mock_handler_run1)
    pipeline1 = ReviewIngestionPipeline(db=db_session, steam_client=client1)

    result1 = pipeline1.execute_job(job1.id)
    assert result1.reviews_seen == 1
    assert result1.reviews_inserted == 1
    assert result1.reviews_updated == 0

    # Verify only 1 review row was inserted
    reviews = db_session.scalars(
        select(Review).where(Review.game_id == game.id, Review.steam_review_id == 500001)
    ).all()
    assert len(reviews) == 1
    assert reviews[0].review_text == "Updated version in same batch"

    # 2. Run a second job with the same review (re-ingestion)
    def mock_handler_run2(request: httpx.Request) -> httpx.Response:
        input_json = json.loads(request.url.params.get("input_json", "{}"))
        cursor = input_json.get("cursor", "*")
        if cursor == "cursor_dup":
            return httpx.Response(
                200,
                json={
                    "response": {
                        "reviews": [
                            {
                                "recommendationid": "500001",
                                "author": {"steamid": "1"},
                                "language": "english",
                                "review": "Second job edited review text",
                                "timestamp_created": 1600000000,
                                "timestamp_updated": 1600001000,
                                "voted_up": False,  # Changed recommendation
                                "votes_up": 20,
                            }
                        ],
                        "cursor": "cursor_dup_2",
                        "query_summary": {"num_reviews": 1},
                        "success": 1,
                    }
                },
            )
        return httpx.Response(
            200, json={"response": {"reviews": [], "cursor": "cursor_dup_2", "success": 1}}
        )

    job2 = service.create_historical_job(game.id)
    client2 = create_mock_steam_client(mock_handler_run2)
    pipeline2 = ReviewIngestionPipeline(db=db_session, steam_client=client2)

    result2 = pipeline2.execute_job(job2.id)
    assert result2.reviews_inserted == 0
    assert result2.reviews_updated == 1

    # Verify row count is still exactly 1, but updated
    reviews_after = db_session.scalars(
        select(Review).where(Review.game_id == game.id, Review.steam_review_id == 500001)
    ).all()
    assert len(reviews_after) == 1
    assert reviews_after[0].review_text == "Second job edited review text"
    assert reviews_after[0].voted_up is False
    assert reviews_after[0].votes_up == 20


def test_invalid_cursor_handling(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Malformed Steam payload or cursor causes clean permanent error handling without cursor corruption."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)
    job = service.create_historical_job(game.id)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        # Return invalid payload missing expected response object
        return httpx.Response(200, json={"corrupted": "bad response structure"})

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    result = pipeline.execute_job(job.id)

    assert result.status == "failed"
    assert result.error_code == "SteamMalformedResponseError"

    db_session.refresh(job)
    assert job.status == "failed"
    assert job.error_code == "SteamMalformedResponseError"

    ckpt = service.get_checkpoint(game.id, "historical:all")
    assert ckpt is not None
    assert ckpt.status == "error"


def test_http_429_rate_limit_and_bounded_retry(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """HTTP 429 triggers bounded retry: marks job retrying on first attempt, then succeeds on retry."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)
    job = service.create_historical_job(game.id)

    call_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, headers={"Retry-After": "2"}, text="Too Many Requests")
        return httpx.Response(
            200,
            json=build_steam_reviews_page([600001], cursor="cursor_after_retry", has_more=False),
        )

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    # Attempt 1: Raises SteamRateLimitError and sets job to retrying
    with pytest.raises(SteamRateLimitError) as exc_info:
        pipeline.execute_job(job.id)
    assert exc_info.value.retry_after == 2

    db_session.refresh(job)
    assert job.status == "retrying"
    assert job.retry_count == 1
    assert job.error_code == "SteamRateLimitError"

    # Attempt 2: Retries and completes successfully
    result = pipeline.execute_job(job.id)
    assert result.status == "succeeded"
    assert result.reviews_inserted == 1

    db_session.refresh(job)
    assert job.status == "succeeded"
    assert job.retry_count == 1  # Retained diagnostic count


def test_steam_timeout_retry_exhaustion(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Persistent network timeout exhausts max retries and transitions job to failed."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)
    job = service.create_historical_job(game.id)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Read timed out")

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    # Attempt 1 -> retrying (1)
    with pytest.raises(httpx.TimeoutException):
        pipeline.execute_job(job.id)
    db_session.refresh(job)
    assert job.status == "retrying"
    assert job.retry_count == 1

    # Attempt 2 -> retrying (2)
    with pytest.raises(httpx.TimeoutException):
        pipeline.execute_job(job.id)
    db_session.refresh(job)
    assert job.status == "retrying"
    assert job.retry_count == 2

    # Attempt 3 -> retrying (3)
    with pytest.raises(httpx.TimeoutException):
        pipeline.execute_job(job.id)
    db_session.refresh(job)
    assert job.status == "retrying"
    assert job.retry_count == 3

    # Attempt 4 -> retries exhausted, marks failed
    result = pipeline.execute_job(job.id)
    assert result.status == "failed"
    assert "Max retries (3) exhausted" in (result.error_message or "")

    db_session.refresh(job)
    assert job.status == "failed"
    ckpt = service.get_checkpoint(game.id, "historical:all")
    assert ckpt is not None
    assert ckpt.status == "error"


def test_worker_termination_and_resume_from_checkpoint(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """Simulates worker crash after page 1; restarts and resumes cleanly from last checkpoint cursor."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)

    # Job 1 processes only page 1 (simulating crash/budget cut)
    job = service.create_historical_job(game.id, IngestionJobConfig(max_pages=1))

    def mock_handler(request: httpx.Request) -> httpx.Response:
        input_json = json.loads(request.url.params.get("input_json", "{}"))
        cursor = input_json.get("cursor", "*")

        if cursor == "*":
            return httpx.Response(
                200,
                json=build_steam_reviews_page(
                    [700001, 700002], cursor="cursor_step_1", has_more=True
                ),
            )
        elif cursor == "cursor_step_1":
            return httpx.Response(
                200, json=build_steam_reviews_page([700003], cursor="cursor_step_1", has_more=False)
            )
        return httpx.Response(
            200, json={"response": {"reviews": [], "cursor": cursor, "success": 1}}
        )

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline1 = ReviewIngestionPipeline(db=db_session, steam_client=client)

    result1 = pipeline1.execute_job(job.id)
    assert result1.pages_processed == 1
    assert result1.reviews_inserted == 2
    assert result1.cursor == "cursor_step_1"

    # Verify Checkpoint holds cursor_step_1
    ckpt = service.get_checkpoint(game.id, "historical:all")
    assert ckpt is not None
    assert ckpt.cursor == "cursor_step_1"

    # Now simulate a resumed run on a new job referencing the same checkpoint
    job2 = service.create_historical_job(game.id, IngestionJobConfig(max_pages=5))
    client2 = create_mock_steam_client(mock_handler)
    pipeline2 = ReviewIngestionPipeline(db=db_session, steam_client=client2)

    result2 = pipeline2.execute_job(job2.id)
    assert result2.status == "succeeded"
    assert result2.pages_processed == 1
    assert result2.reviews_inserted == 1
    assert result2.cursor == "cursor_step_1"

    # Verify both batches of reviews are present in DB (3 total)
    total_reviews = db_session.scalars(
        select(Review).where(
            Review.game_id == game.id, Review.steam_review_id.in_([700001, 700002, 700003])
        )
    ).all()
    assert len(total_reviews) == 3


def test_incremental_watermark_safety_on_failure(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """CRITICAL INVARIANT: Incomplete incremental sync NEVER advances the committed watermark."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)

    # Establish an existing safe watermark
    initial_watermark = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
    ckpt = service.checkpoint_repo.get_or_create(
        game.id, "incremental:all", collection_mode="incremental"
    )
    ckpt.watermark_at = initial_watermark
    db_session.add(ckpt)
    db_session.commit()

    job = service.create_incremental_job(game.id, IngestionJobConfig(max_pages=5))

    page_counter = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal page_counter
        page_counter += 1
        if page_counter == 1:
            # Page 1 succeeds
            return httpx.Response(
                200, json=build_steam_reviews_page([800001], cursor="inc_page_1", has_more=True)
            )
        # Page 2 fails fatally
        raise httpx.RequestError("Network dropped on page 2")

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    # Execute — should fail on page 2
    with pytest.raises(httpx.RequestError):
        pipeline.execute_job(job.id)

    # Verify page 1 reviews were persisted atomically
    r = db_session.scalars(select(Review).where(Review.steam_review_id == 800001)).first()
    assert r is not None

    # CRITICAL CHECK: Watermark MUST NOT have changed!
    db_session.refresh(ckpt)
    assert ckpt.watermark_at == initial_watermark


def test_incremental_watermark_advancement_on_success(
    db_session: Session, sample_catalog: dict[str, Any]
) -> None:
    """On complete successful incremental sync, watermark advances to the sync execution timestamp."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)

    initial_watermark = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
    ckpt = service.checkpoint_repo.get_or_create(
        game.id, "incremental:all", collection_mode="incremental"
    )
    ckpt.watermark_at = initial_watermark
    db_session.add(ckpt)
    db_session.commit()

    job = service.create_incremental_job(game.id, IngestionJobConfig(max_pages=5))

    def mock_handler(request: httpx.Request) -> httpx.Response:
        input_json = json.loads(request.url.params.get("input_json", "{}"))
        cursor = input_json.get("cursor", "*")
        if cursor == "*":
            return httpx.Response(
                200, json=build_steam_reviews_page([810001], cursor="inc_c1", has_more=True)
            )
        return httpx.Response(
            200, json=build_steam_reviews_page([], cursor="inc_c1", has_more=False)
        )

    client = create_mock_steam_client(mock_handler, max_retries=0)
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    result = pipeline.execute_job(job.id)
    assert result.status == "succeeded"

    db_session.refresh(ckpt)
    assert ckpt.watermark_at is not None
    assert ckpt.watermark_at > initial_watermark
    assert ckpt.watermark_at.year >= 2026


def test_job_cancellation(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """Cancelling a job before or during pagination stops execution immediately."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)

    # 1. Cancel before run
    job1 = service.create_historical_job(game.id)
    service.cancel_job(job1.id)

    client = create_mock_steam_client(lambda r: httpx.Response(200, json={}))
    pipeline = ReviewIngestionPipeline(db=db_session, steam_client=client)

    result1 = pipeline.execute_job(job1.id)
    assert result1.status == "cancelled"
    assert result1.pages_processed == 0

    # 2. Cancel between pages
    job2 = service.create_historical_job(game.id, IngestionJobConfig(max_pages=5))

    def mock_handler(request: httpx.Request) -> httpx.Response:
        # After page 1 is requested, cancel job in DB
        service.cancel_job(job2.id)
        return httpx.Response(
            200,
            json=build_steam_reviews_page([900001], cursor="cancel_cur_1", has_more=True),
        )

    client2 = create_mock_steam_client(mock_handler)
    pipeline2 = ReviewIngestionPipeline(db=db_session, steam_client=client2)
    result2 = pipeline2.execute_job(job2.id)

    assert result2.status == "cancelled"
    assert result2.pages_processed == 1  # Committed page 1, then halted before page 2
    db_session.refresh(job2)
    assert job2.status == "cancelled"


def test_service_active_job_conflict(db_session: Session, sample_catalog: dict[str, Any]) -> None:
    """IngestionService prevents concurrent active jobs of the same type for a game."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)

    job1 = service.create_historical_job(game.id)
    assert job1.status == "queued"

    with pytest.raises(ConflictError) as exc_info:
        service.create_historical_job(game.id)
    assert exc_info.value.code == "INGESTION_JOB_ALREADY_ACTIVE"


def test_celery_task_integration(
    db_session: Session, sample_catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify Celery task execution and job cancellation tasks in eager mode."""
    game = sample_catalog["game1"]
    service = IngestionService(db_session)
    job = service.create_historical_job(game.id, IngestionJobConfig(max_pages=2))

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=build_steam_reviews_page([950001], cursor="celery_c1", has_more=False),
        )

    # Monkeypatch SteamClient and SessionLocal inside task execution
    monkeypatch.setattr(
        "app.workers.tasks.SteamClient",
        lambda: create_mock_steam_client(mock_handler),
    )
    monkeypatch.setattr(
        "app.workers.tasks.SessionLocal",
        lambda: db_session,
    )
    monkeypatch.setattr(
        db_session,
        "close",
        lambda: None,
    )

    # Test eager execution of ingest_game_reviews
    async_result = ingest_game_reviews.apply(args=[str(job.id)])
    assert async_result.successful()
    task_output = async_result.result
    assert task_output["status"] == "succeeded"
    assert task_output["reviews_inserted"] == 1

    # Test cancel_ingestion_job task
    job2 = service.create_historical_job(game.id)
    cancel_res = cancel_ingestion_job.apply(args=[str(job2.id)])
    assert cancel_res.successful()
    assert cancel_res.result["status"] == "cancelled"
