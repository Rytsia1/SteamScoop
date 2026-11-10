"""Service implementing asynchronous data export creation, status checking, and retrieval."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ExportExpiredError,
    ExportNotFoundError,
    GameNotFoundError,
    ValidationException,
)
from app.models.workspace import ExportJob, User
from app.repositories.export import ExportRepository
from app.repositories.game import GameRepository
from app.repositories.review import ReviewRepository
from app.schemas.export import ExportCreateRequest, ExportResponseData

ALLOWED_EXPORT_FIELDS: set[str] = {
    "review_text",
    "language",
    "voted_up",
    "steam_created_at",
    "sentiment",
    "votes_up",
    "votes_funny",
    "playtime_forever",
    "weighted_vote_score",
    "aspects",
    "topics",
}


class ExportService:
    """Domain service for asynchronous analytical exports."""

    def __init__(
        self,
        session: Session,
        export_repo: ExportRepository | None = None,
        game_repo: GameRepository | None = None,
        review_repo: ReviewRepository | None = None,
    ) -> None:
        self.session = session
        self.export_repo = export_repo or ExportRepository(session)
        self.game_repo = game_repo or GameRepository(session)
        self.review_repo = review_repo or ReviewRepository(session)

    def create_export(
        self,
        user: User,
        request: ExportCreateRequest,
    ) -> ExportResponseData:
        """Validate export parameters and enqueue asynchronous job."""
        # 1. Validate fields allowlist
        invalid_fields = [f for f in request.fields if f not in ALLOWED_EXPORT_FIELDS]
        if invalid_fields:
            allowed = sorted(ALLOWED_EXPORT_FIELDS)
            raise ValidationException(
                field="fields",
                issue=f"Unsupported export fields: {invalid_fields}. Allowed fields: {allowed}",
            )

        # 2. Validate scope
        scope_type = request.scope.get("type")
        if scope_type not in ("game_reviews", "reviews"):
            raise ValidationException(
                field="scope.type",
                issue="Currently supported export scope types are 'game_reviews' or 'reviews'.",
            )

        target_game_id: uuid.UUID | None = None
        if "game_id" in request.scope:
            try:
                target_game_id = uuid.UUID(str(request.scope["game_id"]))
            except (ValueError, TypeError) as err:
                raise ValidationException(
                    field="scope.game_id", issue="game_id must be a valid UUID."
                ) from err

            game = self.game_repo.get_by_id(target_game_id)
            if not game:
                raise GameNotFoundError(target_game_id)

        # 3. Create queued job
        job = self.export_repo.create_export_job(
            requested_by_user_id=user.id,
            export_format=request.format,
            scope=request.scope,
            filters=request.filters,
            fields=request.fields,
            project_id=None,
        )

        return ExportResponseData(
            export_id=job.id,
            status=job.status,  # type: ignore[arg-type]
            format=job.format,
            row_count=job.row_count,
            created_at=job.created_at,
            finished_at=job.finished_at,
            expires_at=job.expires_at,
        )

    def get_export(
        self,
        user: User,
        export_id: uuid.UUID,
        user_roles: list[str] | None = None,
    ) -> ExportResponseData:
        """Fetch export status enforcing requester ownership or administrative access."""
        is_admin = bool(user_roles and "admin" in user_roles)
        job: ExportJob | None = None

        if is_admin:
            job = self.export_repo.get_by_id(export_id)
        else:
            job = self.export_repo.get_by_user(export_id, user.id)

        if not job:
            raise ExportNotFoundError(export_id)

        # Check expiration
        now = datetime.now(UTC)
        if job.expires_at and job.expires_at < now and job.status != "expired":
            job.status = "expired"
            self.session.commit()

        return ExportResponseData(
            export_id=job.id,
            status=job.status,  # type: ignore[arg-type]
            format=job.format,
            row_count=job.row_count,
            created_at=job.created_at,
            finished_at=job.finished_at,
            expires_at=job.expires_at,
        )

    def download_export(
        self,
        user: User,
        export_id: uuid.UUID,
        user_roles: list[str] | None = None,
    ) -> tuple[str, str, bytes]:
        """Download completed export artifact content as (filename, media_type, bytes)."""
        is_admin = bool(user_roles and "admin" in user_roles)
        job: ExportJob | None = None

        if is_admin:
            job = self.export_repo.get_by_id(export_id)
        else:
            job = self.export_repo.get_by_user(export_id, user.id)

        if not job:
            raise ExportNotFoundError(export_id)

        now = datetime.now(UTC)
        if (job.expires_at and job.expires_at < now) or job.status == "expired":
            raise ExportExpiredError(export_id)

        # If job is still queued/running, in MVP/test synchronous generation:
        if job.status in ("queued", "running"):
            # Mark succeeded and compute row count
            job.status = "succeeded"
            job.finished_at = now
            self.session.commit()

        # Generate exported data from target reviews
        config = job.export_config or {}
        fields: list[str] = config.get("fields", ["review_text", "language", "sentiment"])
        scope: dict[str, Any] = config.get("scope", {})

        records: list[dict[str, Any]] = []
        if "game_id" in scope:
            game_id = uuid.UUID(str(scope["game_id"]))
            reviews = self.review_repo.get_reviews_by_game(game_id, limit=100)
            for r in reviews:
                record: dict[str, Any] = {}
                for f in fields:
                    if hasattr(r, f):
                        val = getattr(r, f)
                        if isinstance(val, datetime):
                            record[f] = val.isoformat()
                        else:
                            record[f] = val
                    elif f == "sentiment":
                        record[f] = "positive" if r.voted_up else "negative"
                    else:
                        record[f] = None
                records.append(record)

        if job.format == "json":
            content_bytes = json.dumps(records, indent=2).encode("utf-8")
            media_type = "application/json"
            filename = f"export_{export_id}.json"
        else:
            output = io.StringIO()
            if records:
                writer = csv.DictWriter(output, fieldnames=fields)
                writer.writeheader()
                for rec in records:
                    writer.writerow(rec)
            else:
                writer = csv.DictWriter(output, fieldnames=fields)
                writer.writeheader()
            content_bytes = output.getvalue().encode("utf-8")
            media_type = "text/csv"
            filename = f"export_{export_id}.csv"

        return filename, media_type, content_bytes

    def cancel_export(
        self,
        user: User,
        export_id: uuid.UUID,
        user_roles: list[str] | None = None,
    ) -> bool:
        """Cancel a queued or running export job."""
        is_admin = bool(user_roles and "admin" in user_roles)
        job: ExportJob | None = None

        if is_admin:
            job = self.export_repo.get_by_id(export_id)
        else:
            job = self.export_repo.get_by_user(export_id, user.id)

        if not job:
            raise ExportNotFoundError(export_id)

        return self.export_repo.cancel_export(export_id, job.requested_by_user_id)
