"""Administrative domain service for catalog, collections, and models."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ActiveJobExistsError,
    ConflictError,
    GameNotFoundError,
    IngestionJobNotFoundError,
    InvalidStateTransitionError,
    ModelNotFoundError,
    PipelineRunNotFoundError,
)
from app.models.game import Game
from app.models.ingestion import IngestionJob
from app.models.ml import MLModel, PipelineRun
from app.repositories.game import GameRepository
from app.repositories.ingestion import IngestionJobRepository
from app.repositories.pipeline_run import PipelineRunRepository
from app.schemas.admin import (
    AdminGameCreateRequest,
    AdminGameUpdateRequest,
    AdminIngestionJobCreateRequest,
)


class AdminService:
    """Service encapsulating administrative operations and infrastructure controls."""

    def __init__(
        self,
        session: Session,
        game_repo: GameRepository | None = None,
        ingestion_job_repo: IngestionJobRepository | None = None,
        pipeline_run_repo: PipelineRunRepository | None = None,
    ) -> None:
        self.session = session
        self.game_repo = game_repo or GameRepository(session)
        self.ingestion_job_repo = ingestion_job_repo or IngestionJobRepository(session)
        self.pipeline_run_repo = pipeline_run_repo or PipelineRunRepository(session)

    # Catalog operations
    def list_catalog_games(self, limit: int = 50, offset: int = 0) -> Sequence[Game]:
        """List managed games in the catalog."""
        stmt = select(Game).order_by(Game.created_at.desc()).offset(offset).limit(min(limit, 100))
        return self.session.scalars(stmt).all()

    def create_catalog_game(self, req: AdminGameCreateRequest) -> Game:
        """Add a new game to the managed catalog."""
        existing = self.game_repo.get_by_steam_app_id(req.steam_app_id)
        if existing:
            raise ConflictError(
                message=f"Game with steam_app_id {req.steam_app_id} already exists."
            )

        game = Game(
            steam_app_id=req.steam_app_id,
            name=req.name,
            short_description=req.short_description,
            genres=req.genres,
            release_date=req.release_date,
            is_free=req.is_free,
            catalog_status=req.catalog_status,
            is_active=True,
        )
        return self.game_repo.create(game)

    def update_catalog_game(self, game_id: uuid.UUID, req: AdminGameUpdateRequest) -> Game:
        """Update catalog metadata or status for an existing game."""
        game = self.game_repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundError(game_id)

        if req.name is not None:
            game.name = req.name
        if req.short_description is not None:
            game.short_description = req.short_description
        if req.catalog_status is not None:
            game.catalog_status = req.catalog_status
        if req.is_active is not None:
            game.is_active = req.is_active

        self.session.commit()
        self.session.refresh(game)
        return game

    # Ingestion orchestration
    def queue_ingestion_job(
        self,
        game_id: uuid.UUID,
        req: AdminIngestionJobCreateRequest,
        user_id: uuid.UUID,
    ) -> IngestionJob:
        """Queue a collection job verifying game existence and active-job conflicts."""
        game = self.game_repo.get_by_id(game_id)
        if not game:
            raise GameNotFoundError(game_id)

        active = self.ingestion_job_repo.get_active_job_for_game(game_id, req.job_type)
        if active is not None:
            raise ActiveJobExistsError(
                f"An active {req.job_type} collection job ({active.id}) "
                "already exists for this game."
            )

        return self.ingestion_job_repo.create_job(
            game_id=game_id,
            job_type=req.job_type,
            request_config=req.collection_config,
            requested_by_user_id=user_id,
        )

    def list_ingestion_jobs(
        self,
        game_id: uuid.UUID | None = None,
        job_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> Sequence[IngestionJob]:
        """List ingestion collection jobs with optional filters."""
        stmt = select(IngestionJob)
        if game_id:
            stmt = stmt.where(IngestionJob.game_id == game_id)
        if job_type:
            stmt = stmt.where(IngestionJob.job_type == job_type)
        if status:
            stmt = stmt.where(IngestionJob.status == status)

        stmt = stmt.order_by(IngestionJob.created_at.desc()).limit(min(limit, 100))
        return self.session.scalars(stmt).all()

    def get_ingestion_job(self, job_id: uuid.UUID) -> IngestionJob:
        """Fetch detailed status of a collection job."""
        job = self.ingestion_job_repo.get_by_id(job_id)
        if not job:
            raise IngestionJobNotFoundError(job_id)
        return job

    def retry_ingestion_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> IngestionJob:
        """Retry a failed or cancellable ingestion job."""
        job = self.ingestion_job_repo.get_by_id(job_id)
        if not job:
            raise IngestionJobNotFoundError(job_id)

        if job.status not in ("failed", "cancelled", "partial"):
            raise InvalidStateTransitionError(
                f"Job in status '{job.status}' cannot be retried. "
                "Only failed or cancelled jobs can be retried."
            )

        return self.ingestion_job_repo.create_job(
            game_id=job.game_id,
            job_type=job.job_type,
            request_config=job.request_config,
            requested_by_user_id=user_id,
        )

    def cancel_ingestion_job(self, job_id: uuid.UUID) -> IngestionJob:
        """Cancel an in-progress or queued collection job."""
        job = self.ingestion_job_repo.get_by_id(job_id)
        if not job:
            raise IngestionJobNotFoundError(job_id)

        if job.status not in ("queued", "running", "retrying"):
            raise InvalidStateTransitionError(f"Job in status '{job.status}' cannot be cancelled.")

        job.status = "cancelled"
        now = datetime.now(UTC)
        if job.started_at is None:
            job.started_at = now
        job.finished_at = now
        self.session.commit()
        self.session.refresh(job)
        return job

    # ML Pipeline runs
    def list_pipeline_runs(
        self,
        pipeline_type: str | None = None,
        limit: int = 50,
    ) -> Sequence[PipelineRun]:
        """List ML pipeline runs ordered by start time."""
        stmt = select(PipelineRun)
        if pipeline_type:
            stmt = stmt.where(PipelineRun.pipeline_type == pipeline_type)
        stmt = stmt.order_by(PipelineRun.started_at.desc()).limit(min(limit, 100))
        return self.session.scalars(stmt).all()

    def get_pipeline_run(self, run_id: uuid.UUID) -> PipelineRun:
        """Fetch pipeline run by ID."""
        run = self.pipeline_run_repo.get_by_id(run_id)
        if not run:
            raise PipelineRunNotFoundError(run_id)
        return run

    # Models
    def list_models(self) -> Sequence[MLModel]:
        """List registered ML model versions."""
        stmt = select(MLModel).order_by(MLModel.created_at.desc())
        return self.session.scalars(stmt).all()

    def activate_model(self, model_id: uuid.UUID) -> MLModel:
        """Atomically activate a model version and deactivate existing models for the task."""
        stmt = select(MLModel).where(MLModel.id == model_id)
        model = self.session.scalars(stmt).first()
        if not model:
            raise ModelNotFoundError(model_id)

        # Deactivate conflicting models for the same task
        deact_stmt = (
            update(MLModel)
            .where(MLModel.task == model.task, MLModel.id != model.id)
            .values(is_active=False)
        )
        self.session.execute(deact_stmt)

        model.is_active = True
        self.session.commit()
        self.session.refresh(model)
        return model
