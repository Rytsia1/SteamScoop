from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "steamscoop",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    imports=["app.workers.tasks"],
    task_routes={
        "app.workers.tasks.ingest_game_reviews": {"queue": "ingestion"},
        "app.workers.tasks.cancel_ingestion_job": {"queue": "ingestion"},
        "app.workers.tasks.process_review_batch": {"queue": "ml_inference"},
        "app.workers.tasks.aggregate_game_analytics": {"queue": "analytics"},
        "app.workers.tasks.reprocess_game_pipeline": {"queue": "ml_inference"},
        "app.workers.tasks.generate_export_artifact": {"queue": "exports"},
        "app.workers.tasks.cleanup_expired_exports": {"queue": "exports"},
    },
)


@celery_app.task(name="app.workers.celery_app.health_ping")  # type: ignore[untyped-decorator]
def health_ping() -> str:
    """Lightweight health check task for Celery worker verification."""
    return "pong"
