"""Repository for PipelineRun execution state and PipelineRunItem diagnostic records."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml import PipelineRun, PipelineRunItem
from app.repositories.base import BaseRepository


class PipelineRunRepository(BaseRepository[PipelineRun]):
    """Data access repository for ML/analytics pipeline runs and item outcomes."""

    def __init__(self, session: Session) -> None:
        super().__init__(PipelineRun, session)

    def create_run(
        self,
        pipeline_type: str,
        ml_model_id: uuid.UUID | None = None,
        game_id: uuid.UUID | None = None,
        input_filter: dict[str, Any] | None = None,
        model_version_snapshot: str | None = None,
        input_count: int = 0,
    ) -> PipelineRun:
        """Create a new PipelineRun record with status='running' and started_at timestamp."""
        run = PipelineRun(
            pipeline_type=pipeline_type,
            ml_model_id=ml_model_id,
            game_id=game_id,
            status="running",
            input_filter=input_filter or {},
            model_version_snapshot=model_version_snapshot,
            started_at=datetime.now(UTC),
            input_count=input_count,
            success_count=0,
            failure_count=0,
            metrics={},
        )
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def update_progress(
        self,
        pipeline_run_id: uuid.UUID,
        success_count: int,
        failure_count: int,
        metrics: dict[str, Any] | None = None,
    ) -> PipelineRun | None:
        """Incrementally update success/failure counters and runtime metrics."""
        run = self.get_by_id(pipeline_run_id)
        if not run:
            return None

        run.success_count = success_count
        run.failure_count = failure_count
        if metrics:
            run.metrics = {**run.metrics, **metrics}

        self.session.commit()
        self.session.refresh(run)
        return run

    def finish_run(
        self,
        pipeline_run_id: uuid.UUID,
        status: str = "succeeded",
        success_count: int | None = None,
        failure_count: int | None = None,
        error_summary: str | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> PipelineRun | None:
        """Mark a pipeline run as completed or failed with terminal timestamps and statistics."""
        run = self.get_by_id(pipeline_run_id)
        if not run:
            return None

        run.status = status
        run.finished_at = datetime.now(UTC)
        if success_count is not None:
            run.success_count = success_count
        if failure_count is not None:
            run.failure_count = failure_count
        if error_summary:
            run.error_summary = error_summary
        if metrics:
            run.metrics = {**run.metrics, **metrics}

        self.session.commit()
        self.session.refresh(run)
        return run

    def record_item_outcome(
        self,
        pipeline_run_id: uuid.UUID,
        item_key: str,
        review_id: uuid.UUID | None = None,
        status: str = "succeeded",
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> PipelineRunItem:
        """Persist or update an item-level execution outcome idempotently."""
        stmt = select(PipelineRunItem).where(
            PipelineRunItem.pipeline_run_id == pipeline_run_id,
            PipelineRunItem.item_key == item_key,
        )
        existing = self.session.scalars(stmt).first()

        if existing:
            existing.status = status
            existing.review_id = review_id
            existing.error_code = error_code
            existing.error_message = error_message
            self.session.flush()
            return existing

        item = PipelineRunItem(
            pipeline_run_id=pipeline_run_id,
            review_id=review_id,
            item_key=item_key,
            status=status,
            error_code=error_code,
            error_message=error_message,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def bulk_record_item_outcomes(
        self,
        items_data: list[dict[str, Any]],
    ) -> list[PipelineRunItem]:
        """Record a batch of item-level processing outcomes in a single transaction."""
        created: list[PipelineRunItem] = []
        for d in items_data:
            item = self.record_item_outcome(
                pipeline_run_id=d["pipeline_run_id"],
                item_key=d["item_key"],
                review_id=d.get("review_id"),
                status=d.get("status", "succeeded"),
                error_code=d.get("error_code"),
                error_message=d.get("error_message"),
            )
            created.append(item)
        self.session.commit()
        return created

    def get_failed_items(
        self,
        pipeline_run_id: uuid.UUID,
    ) -> Sequence[PipelineRunItem]:
        """Fetch all failed items for a pipeline run (used for diagnosis and reprocessing)."""
        stmt = (
            select(PipelineRunItem)
            .where(
                PipelineRunItem.pipeline_run_id == pipeline_run_id,
                PipelineRunItem.status == "failed",
            )
            .order_by(PipelineRunItem.created_at.asc())
        )
        return self.session.scalars(stmt).all()

    def get_runs_for_game(
        self,
        game_id: uuid.UUID,
        pipeline_type: str | None = None,
        limit: int = 20,
    ) -> Sequence[PipelineRun]:
        """Retrieve recent pipeline execution runs for a game."""
        stmt = select(PipelineRun).where(PipelineRun.game_id == game_id)
        if pipeline_type:
            stmt = stmt.where(PipelineRun.pipeline_type == pipeline_type)
        stmt = stmt.order_by(PipelineRun.created_at.desc()).limit(limit)
        return self.session.scalars(stmt).all()
