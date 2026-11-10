"""Repository for asynchronous analytical exports and lifecycle state."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.workspace import ExportJob
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[ExportJob]):
    """Data access repository for analytical ExportJob entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(ExportJob, session)

    def create_export_job(
        self,
        requested_by_user_id: uuid.UUID,
        export_format: str,
        scope: dict[str, Any],
        filters: dict[str, Any],
        fields: list[str],
        project_id: uuid.UUID | None = None,
        row_limit: int | None = None,
        ttl_days: int = 7,
    ) -> ExportJob:
        """Create a new queued asynchronous export job."""
        now = datetime.now(UTC)
        export_config: dict[str, Any] = {
            "scope": scope,
            "filters": filters,
            "fields": fields,
        }
        if row_limit is not None:
            export_config["row_limit"] = row_limit

        export_job = ExportJob(
            requested_by_user_id=requested_by_user_id,
            project_id=project_id,
            format=export_format,
            status="queued",
            export_config=export_config,
            created_at=now,
            expires_at=now + timedelta(days=ttl_days),
        )
        self.session.add(export_job)
        self.session.commit()
        self.session.refresh(export_job)
        return export_job

    def get_by_user(self, export_id: uuid.UUID, user_id: uuid.UUID) -> ExportJob | None:
        """Fetch export job enforcing requester access."""
        stmt = select(ExportJob).where(
            ExportJob.id == export_id,
            ExportJob.requested_by_user_id == user_id,
        )
        return self.session.scalars(stmt).first()

    def count_active_jobs_by_user(self, user_id: uuid.UUID) -> int:
        """Count active queued or running jobs for concurrency rate-limiting."""
        stmt = select(func.count(ExportJob.id)).where(
            ExportJob.requested_by_user_id == user_id,
            ExportJob.status.in_(["queued", "running"]),
        )
        return self.session.scalar(stmt) or 0

    def cancel_export(
        self,
        export_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        is_admin: bool = False,
    ) -> ExportJob | None:
        """Cancel a queued, running, or completed export job."""
        if is_admin:
            job = self.get_by_id(export_id)
        elif user_id:
            job = self.get_by_user(export_id, user_id)
        else:
            return None

        if not job or job.status == "cancelled":
            return None

        job.status = "cancelled"
        job.finished_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_expired_jobs(self, now: datetime | None = None) -> Sequence[ExportJob]:
        """Fetch jobs whose expiration date has passed and are not yet marked expired."""
        cutoff = now or datetime.now(UTC)
        stmt = select(ExportJob).where(
            ExportJob.expires_at.is_not(None),
            ExportJob.expires_at < cutoff,
            ExportJob.status != "expired",
        )
        return self.session.scalars(stmt).all()
