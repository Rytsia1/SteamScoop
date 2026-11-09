import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ingestion import CollectionCheckpoint, IngestionBatch, IngestionJob
from app.repositories.base import BaseRepository
from app.repositories.review import ReviewRepository


class IngestionJobRepository(BaseRepository[IngestionJob]):
    """Repository managing lifecycle and state for durable ingestion jobs."""

    def __init__(self, session: Session) -> None:
        super().__init__(IngestionJob, session)

    def get_active_job_for_game(self, game_id: uuid.UUID, job_type: str) -> IngestionJob | None:
        """Fetch active (queued, running, or retrying) job for a game and job type."""
        stmt = select(IngestionJob).where(
            IngestionJob.game_id == game_id,
            IngestionJob.job_type == job_type,
            IngestionJob.status.in_(["queued", "running", "retrying"]),
        )
        return self.session.scalars(stmt).first()

    def create_job(
        self,
        game_id: uuid.UUID,
        job_type: str,
        request_config: dict[str, Any] | None = None,
        requested_by_user_id: uuid.UUID | None = None,
        scheduled_at: datetime | None = None,
    ) -> IngestionJob:
        """Create and enqueue a new ingestion job."""
        job = IngestionJob(
            game_id=game_id,
            job_type=job_type,
            status="queued",
            request_config=request_config or {},
            requested_by_user_id=requested_by_user_id,
            scheduled_at=scheduled_at or datetime.now(UTC),
        )
        return self.create(job)

    def get_jobs_for_game(self, game_id: uuid.UUID, limit: int = 20) -> Sequence[IngestionJob]:
        """Fetch job history for a target game in descending chronological order."""
        stmt = (
            select(IngestionJob)
            .where(IngestionJob.game_id == game_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(limit)
        )
        return self.session.scalars(stmt).all()


class IngestionBatchRepository(BaseRepository[IngestionBatch]):
    """Repository managing per-page batch evidence and cursor tracking."""

    def __init__(self, session: Session) -> None:
        super().__init__(IngestionBatch, session)

    def get_batches_for_job(self, job_id: uuid.UUID) -> Sequence[IngestionBatch]:
        """Fetch all batch records for a parent job ordered by batch number."""
        stmt = (
            select(IngestionBatch)
            .where(IngestionBatch.ingestion_job_id == job_id)
            .order_by(IngestionBatch.batch_number.asc())
        )
        return self.session.scalars(stmt).all()


class CollectionCheckpointRepository(BaseRepository[CollectionCheckpoint]):
    """Repository tracking resumable collection progress per game and stream."""

    def __init__(self, session: Session) -> None:
        super().__init__(CollectionCheckpoint, session)

    def get_by_stream_key(self, game_id: uuid.UUID, stream_key: str) -> CollectionCheckpoint | None:
        """Fetch durable checkpoint by composite key (game_id, stream_key)."""
        stmt = select(CollectionCheckpoint).where(
            CollectionCheckpoint.game_id == game_id,
            CollectionCheckpoint.stream_key == stream_key,
        )
        return self.session.scalars(stmt).first()

    def get_or_create(
        self,
        game_id: uuid.UUID,
        stream_key: str,
        collection_mode: str,
    ) -> CollectionCheckpoint:
        """Retrieve existing checkpoint or create an initialized idle checkpoint."""
        checkpoint = self.get_by_stream_key(game_id, stream_key)
        if checkpoint is not None:
            return checkpoint

        checkpoint = CollectionCheckpoint(
            game_id=game_id,
            stream_key=stream_key,
            collection_mode=collection_mode,
            status="idle",
            metadata_={},
        )
        return self.create(checkpoint)


def commit_ingestion_page_transaction(
    session: Session,
    job_id: uuid.UUID,
    game_id: uuid.UUID,
    batch_number: int,
    cursor_in: str | None,
    cursor_out: str | None,
    request_started_at: datetime,
    request_finished_at: datetime | None,
    http_status: int | None,
    reviews_data: list[dict[str, Any]],
    checkpoint_stream_key: str,
    collection_mode: str,
    watermark_at: datetime | None = None,
    checkpoint_status: str = "running",
) -> IngestionBatch:
    """Atomic transaction invariant: commit review upserts, batch record,

    checkpoint progress, and job counters together in a single database transaction.
    If an error occurs, the transaction rolls back completely, ensuring no cursor
    advances past unpersisted reviews.
    """
    review_repo = ReviewRepository(session)
    checkpoint_repo = CollectionCheckpointRepository(session)

    try:
        inserted_count = 0
        updated_count = 0

        for rdata in reviews_data:
            steam_review_id = rdata["steam_review_id"]
            review_text = rdata["review_text"]
            voted_up = rdata["voted_up"]
            extra = {
                k: v
                for k, v in rdata.items()
                if k not in ("steam_review_id", "review_text", "voted_up")
            }

            _, is_created = review_repo.upsert_review(
                game_id=game_id,
                steam_review_id=steam_review_id,
                review_text=review_text,
                voted_up=voted_up,
                commit=False,
                **extra,
            )
            if is_created:
                inserted_count += 1
            else:
                updated_count += 1

        batch = IngestionBatch(
            ingestion_job_id=job_id,
            game_id=game_id,
            batch_number=batch_number,
            cursor_in=cursor_in,
            cursor_out=cursor_out,
            request_started_at=request_started_at,
            request_finished_at=request_finished_at,
            http_status=http_status,
            source_count=len(reviews_data),
            inserted_count=inserted_count,
            updated_count=updated_count,
            duplicate_count=0,
            batch_status="succeeded",
        )
        session.add(batch)

        # Update checkpoint
        checkpoint = checkpoint_repo.get_by_stream_key(game_id, checkpoint_stream_key)
        if checkpoint is None:
            checkpoint = CollectionCheckpoint(
                game_id=game_id,
                stream_key=checkpoint_stream_key,
                collection_mode=collection_mode,
                cursor=cursor_out,
                watermark_at=watermark_at,
                last_successful_job_id=job_id,
                last_success_at=datetime.now(UTC),
                status=checkpoint_status,
                metadata_={},
            )
            session.add(checkpoint)
        else:
            checkpoint.cursor = cursor_out
            if watermark_at is not None:
                checkpoint.watermark_at = watermark_at
            checkpoint.last_successful_job_id = job_id
            checkpoint.last_success_at = datetime.now(UTC)
            checkpoint.status = checkpoint_status
            session.add(checkpoint)

        # Update parent job counters
        job = session.get(IngestionJob, job_id)
        if job is not None:
            job.reviews_seen += len(reviews_data)
            job.reviews_inserted += inserted_count
            job.reviews_updated += updated_count
            job.pages_processed += 1
            session.add(job)

        session.commit()
        session.refresh(batch)
        return batch
    except Exception:
        session.rollback()
        raise
