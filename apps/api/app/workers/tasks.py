import logging
import uuid
from typing import Any

import httpx
from celery import Task

from app.db.session import SessionLocal
from app.ingestion.pipeline import ReviewIngestionPipeline
from app.ingestion.service import IngestionService
from app.integrations.steam.client import SteamClient
from app.integrations.steam.exceptions import (
    SteamRateLimitError,
    SteamTemporaryServerError,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger("steamscoop.workers.tasks")


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=3,
    name="app.workers.tasks.ingest_game_reviews",
)
def ingest_game_reviews(self: Task, job_id: str) -> dict[str, Any]:
    """Execute review ingestion for a game in a Celery background worker.

    Catches transient upstream rate limits and network errors, applying bounded
    exponential backoff with respect to upstream Retry-After headers when available.
    """
    logger.info(
        "Starting ingest_game_reviews task for job: %s (attempt=%d)", job_id, self.request.retries
    )
    db = SessionLocal()
    try:
        with SteamClient() as steam_client:
            pipeline = ReviewIngestionPipeline(db=db, steam_client=steam_client)
            result = pipeline.execute_job(uuid.UUID(job_id))
            return result.model_dump(mode="json")
    except (
        SteamRateLimitError,
        SteamTemporaryServerError,
        httpx.TimeoutException,
        httpx.NetworkError,
    ) as exc:
        delay = getattr(exc, "retry_after", None)
        if delay is None or delay <= 0:
            delay = min(30 * (2**self.request.retries), 300)
        logger.warning(
            "Transient failure in ingest_game_reviews (%s): %s. Retrying in %ds (retry %d/%d)",
            job_id,
            exc,
            delay,
            self.request.retries + 1,
            self.max_retries,
        )
        raise self.retry(exc=exc, countdown=int(delay)) from exc
    except Exception as exc:
        logger.exception("Ingestion task failed permanently for job %s: %s", job_id, exc)
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.cancel_ingestion_job")  # type: ignore[untyped-decorator]
def cancel_ingestion_job(job_id: str) -> dict[str, Any]:
    """Signal cancellation for an active ingestion job in the database."""
    logger.info("Received request to cancel ingestion job %s", job_id)
    db = SessionLocal()
    try:
        service = IngestionService(db)
        job = service.cancel_job(uuid.UUID(job_id))
        return {
            "job_id": str(job.id),
            "status": job.status,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }
    finally:
        db.close()
