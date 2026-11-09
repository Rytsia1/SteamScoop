import logging
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, GameNotFoundError, IngestionJobNotFoundError
from app.ingestion.schemas import IngestionJobConfig
from app.models.ingestion import CollectionCheckpoint, IngestionJob
from app.repositories.game import GameRepository
from app.repositories.ingestion import CollectionCheckpointRepository, IngestionJobRepository

logger = logging.getLogger("steamscoop.ingestion.service")


class IngestionService:
    """Service layer managing ingestion job lifecycles, checkpoints, and scheduling."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.game_repo = GameRepository(session)
        self.job_repo = IngestionJobRepository(session)
        self.checkpoint_repo = CollectionCheckpointRepository(session)

    def create_historical_job(
        self,
        game_id: uuid.UUID,
        config: IngestionJobConfig | None = None,
        requested_by_user_id: uuid.UUID | None = None,
    ) -> IngestionJob:
        """Create and queue a historical review ingestion job.

        Enforces constraint: Only one active historical job per game may be queued/running.
        """
        game = self.game_repo.get(game_id)
        if game is None:
            raise GameNotFoundError(str(game_id))

        active_job = self.job_repo.get_active_job_for_game(game_id, "historical")
        if active_job is not None:
            raise ConflictError(
                f"An active historical ingestion job ({active_job.id}) "
                "already exists for this game.",
                code="INGESTION_JOB_ALREADY_ACTIVE",
            )

        job_config = (config or IngestionJobConfig()).to_dict()
        job = self.job_repo.create_job(
            game_id=game_id,
            job_type="historical",
            request_config=job_config,
            requested_by_user_id=requested_by_user_id,
            scheduled_at=datetime.now(UTC),
        )
        logger.info("Created historical ingestion job %s for game %s", job.id, game_id)
        return job

    def create_incremental_job(
        self,
        game_id: uuid.UUID,
        config: IngestionJobConfig | None = None,
        requested_by_user_id: uuid.UUID | None = None,
    ) -> IngestionJob:
        """Create and queue an incremental review synchronization job.

        Enforces constraint: Only one active incremental job per game may be queued/running.
        """
        game = self.game_repo.get(game_id)
        if game is None:
            raise GameNotFoundError(str(game_id))

        active_job = self.job_repo.get_active_job_for_game(game_id, "incremental")
        if active_job is not None:
            raise ConflictError(
                f"An active incremental ingestion job ({active_job.id}) "
                "already exists for this game.",
                code="INGESTION_JOB_ALREADY_ACTIVE",
            )

        job_config = (config or IngestionJobConfig()).to_dict()
        job = self.job_repo.create_job(
            game_id=game_id,
            job_type="incremental",
            request_config=job_config,
            requested_by_user_id=requested_by_user_id,
            scheduled_at=datetime.now(UTC),
        )
        logger.info("Created incremental ingestion job %s for game %s", job.id, game_id)
        return job

    def cancel_job(self, job_id: uuid.UUID) -> IngestionJob:
        """Signal cancellation for an active ingestion job.

        If the job is queued, running, or retrying, it is marked cancelled.
        The running worker will observe this state and terminate gracefully.
        """
        job = self.job_repo.get(job_id)
        if job is None:
            raise IngestionJobNotFoundError(str(job_id))

        if job.status in ("succeeded", "failed", "cancelled"):
            return job

        now = datetime.now(UTC)
        job.status = "cancelled"
        if not job.started_at:
            job.started_at = now
        job.finished_at = now
        self.session.add(job)

        # Release any active checkpoint lock/status
        stream_key = (job.request_config or {}).get("stream_key") or f"{job.job_type}:all"
        checkpoint = self.checkpoint_repo.get_by_stream_key(job.game_id, stream_key)
        if checkpoint is not None and checkpoint.status == "running":
            checkpoint.status = "idle"
            self.session.add(checkpoint)

        self.session.commit()
        self.session.refresh(job)
        logger.info("Cancelled ingestion job %s", job.id)
        return job

    def get_job(self, job_id: uuid.UUID) -> IngestionJob | None:
        """Fetch job by primary identifier."""
        return self.job_repo.get(job_id)

    def list_jobs_for_game(self, game_id: uuid.UUID, limit: int = 20) -> Sequence[IngestionJob]:
        """Fetch historical and active jobs for a game."""
        return self.job_repo.get_jobs_for_game(game_id, limit=limit)

    def get_checkpoint(self, game_id: uuid.UUID, stream_key: str) -> CollectionCheckpoint | None:
        """Fetch durable collection checkpoint for a stream."""
        return self.checkpoint_repo.get_by_stream_key(game_id, stream_key)
