"""Repository for asynchronous analytical exports and lifecycle state."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
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
        ttl_days: int = 7,
    ) -> ExportJob:
        """Create a new queued asynchronous export job."""
        now = datetime.now(UTC)
        export_job = ExportJob(
            requested_by_user_id=requested_by_user_id,
            project_id=project_id,
            format=export_format,
            status="queued",
            export_config={
                "scope": scope,
                "filters": filters,
                "fields": fields,
            },
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

    def cancel_export(self, export_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Cancel a queued or running export job."""
        job = self.get_by_user(export_id, user_id)
        if not job or job.status not in ["queued", "running"]:
            return False

        job.status = "cancelled"
        job.finished_at = datetime.now(UTC)
        self.session.commit()
        return True
