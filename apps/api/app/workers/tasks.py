import logging
import uuid
from typing import Any

import httpx
from celery import Task
from sqlalchemy.exc import DatabaseError, OperationalError

from app.db.session import SessionLocal
from app.ingestion.pipeline import ReviewIngestionPipeline
from app.ingestion.service import IngestionService
from app.integrations.steam.client import SteamClient
from app.integrations.steam.exceptions import (
    SteamRateLimitError,
    SteamTemporaryServerError,
)
from app.services.analytics_service import AnalyticsService
from app.services.inference_pipeline_service import InferencePipelineService
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


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=3,
    name="app.workers.tasks.process_review_batch",
)
def process_review_batch(
    self: Task,
    game_id: str,
    batch_size: int = 100,
    run_topics: bool = True,
    refresh_aggregates: bool = True,
) -> dict[str, Any]:
    """Execute complete ML batch inference pipeline for a game in background worker.

    Runs sentiment analysis, ABSA, and topic modeling with durable pipeline runs,
    item-level tracking, and automatic aggregate refresh upon completion.
    """
    logger.info(
        "Starting ML batch inference for game %s (attempt=%d)", game_id, self.request.retries
    )
    db = SessionLocal()
    try:
        service = InferencePipelineService(session=db)
        runs = service.run_full_nlp_pipeline(
            game_id=uuid.UUID(game_id),
            batch_size=batch_size,
            run_topics=run_topics,
        )

        results = {
            task: {
                "run_id": str(run.id),
                "status": run.status,
                "input_count": run.input_count,
                "success_count": run.success_count,
                "failure_count": run.failure_count,
            }
            for task, run in runs.items()
        }

        if refresh_aggregates:
            analytics_svc = AnalyticsService(session=db)
            agg_result = analytics_svc.aggregate_game(game_id=uuid.UUID(game_id))
            results["analytics"] = agg_result

        return results
    except (OperationalError, DatabaseError) as exc:
        delay = min(15 * (2**self.request.retries), 180)
        logger.warning(
            "Database transient failure in process_review_batch (%s): %s. Retrying in %ds",
            game_id,
            exc,
            delay,
        )
        raise self.retry(exc=exc, countdown=int(delay)) from exc
    except Exception as exc:
        logger.exception("ML batch inference failed permanently for game %s: %s", game_id, exc)
        raise
    finally:
        db.close()


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=3,
    name="app.workers.tasks.aggregate_game_analytics",
)
def aggregate_game_analytics(
    self: Task,
    game_id: str,
    period_types: list[str] | None = None,
    model_version_key: str = "baseline",
) -> dict[str, Any]:
    """Execute time-bucketed analytics aggregation for a game in background worker."""
    logger.info(
        "Starting analytics aggregation for game %s (version=%s, attempt=%d)",
        game_id,
        model_version_key,
        self.request.retries,
    )
    db = SessionLocal()
    try:
        service = AnalyticsService(session=db)
        result = service.aggregate_game(
            game_id=uuid.UUID(game_id),
            period_types=period_types,
            model_version_key=model_version_key,
        )
        return result
    except (OperationalError, DatabaseError) as exc:
        delay = min(10 * (2**self.request.retries), 120)
        logger.warning(
            "Transient failure in aggregate_game_analytics (%s): %s. Retrying in %ds",
            game_id,
            exc,
            delay,
        )
        raise self.retry(exc=exc, countdown=int(delay)) from exc
    except Exception as exc:
        logger.exception("Analytics aggregation failed for game %s: %s", game_id, exc)
        raise
    finally:
        db.close()


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=3,
    name="app.workers.tasks.reprocess_game_pipeline",
)
def reprocess_game_pipeline(
    self: Task,
    game_id: str,
    failed_pipeline_run_id: str | None = None,
) -> dict[str, Any]:
    """Reprocess failed inference items or backfill game predictions and refresh aggregates."""
    logger.info(
        "Starting reprocessing for game %s (run_id=%s, attempt=%d)",
        game_id,
        failed_pipeline_run_id,
        self.request.retries,
    )
    db = SessionLocal()
    try:
        service = InferencePipelineService(session=db)
        if failed_pipeline_run_id:
            reprocessed_run = service.reprocess_failed_items(
                failed_pipeline_run_id=uuid.UUID(failed_pipeline_run_id)
            )
            result: dict[str, Any] = {
                "reprocessed_run_id": str(reprocessed_run.id),
                "status": reprocessed_run.status,
                "success_count": reprocessed_run.success_count,
                "failure_count": reprocessed_run.failure_count,
            }
        else:
            runs = service.run_full_nlp_pipeline(game_id=uuid.UUID(game_id))
            result = {
                task: {
                    "run_id": str(run.id),
                    "status": run.status,
                    "success_count": run.success_count,
                }
                for task, run in runs.items()
            }

        analytics_svc = AnalyticsService(session=db)
        agg_result = analytics_svc.aggregate_game(game_id=uuid.UUID(game_id))
        result["analytics"] = agg_result
        return result
    except (OperationalError, DatabaseError) as exc:
        delay = min(15 * (2**self.request.retries), 180)
        logger.warning(
            "Transient failure in reprocess_game_pipeline (%s): %s. Retrying in %ds",
            game_id,
            exc,
            delay,
        )
        raise self.retry(exc=exc, countdown=int(delay)) from exc
    except Exception as exc:
        logger.exception("Reprocessing failed for game %s: %s", game_id, exc)
        raise
    finally:
        db.close()


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    max_retries=2,
    name="app.workers.tasks.generate_export_artifact",
)
def generate_export_artifact(self: Task, export_id: str) -> dict[str, Any]:
    """Execute asynchronous analytical data export and file generation."""
    logger.info("Starting generate_export_artifact task for export: %s", export_id)
    db = SessionLocal()
    try:
        from app.services.export_service import ExportService

        service = ExportService(session=db)
        job = service.generate_artifact(uuid.UUID(export_id))
        return {
            "export_id": str(job.id),
            "status": job.status,
            "row_count": job.row_count,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }
    except Exception as exc:
        logger.exception("Export generation failed for job %s: %s", export_id, exc)
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.cleanup_expired_exports")  # type: ignore[untyped-decorator]
def cleanup_expired_exports() -> dict[str, Any]:
    """Scan and purge expired export artifacts from private storage."""
    logger.info("Running cleanup_expired_exports task")
    db = SessionLocal()
    try:
        from app.services.export_service import ExportService

        service = ExportService(session=db)
        purged_count = service.cleanup_expired_exports()
        return {"purged_count": purged_count}
    finally:
        db.close()
