"""Service implementing asynchronous data export creation, status checking, and retrieval."""

from __future__ import annotations

import contextlib
import csv
import io
import json
import logging
import os
import uuid
import xml.sax.saxutils
import zipfile
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    ExportCancelledError,
    ExportConcurrencyLimitError,
    ExportExpiredError,
    ExportFailedError,
    ExportLimitExceededError,
    ExportNotFoundError,
    ExportNotReadyError,
    GameNotFoundError,
    ProjectNotFoundError,
    ValidationException,
)
from app.models.aspect import AspectPrediction
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.models.topic import ReviewTopic, Topic
from app.models.workspace import AuditLog, ExportJob, User
from app.repositories.export import ExportRepository
from app.repositories.game import GameRepository
from app.repositories.review import ReviewRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.export import ExportCreateRequest, ExportResponseData

logger = logging.getLogger("steamscoop.services.export")
settings = get_settings()

ALLOWED_EXPORT_FIELDS: set[str] = {
    "review_text",
    "language",
    "voted_up",
    "steam_created_at",
    "sentiment",
    "sentiment_confidence",
    "aspects",
    "topics",
    "votes_up",
    "votes_funny",
    "playtime_forever",
    "playtime_at_review",
    "weighted_vote_score",
}


def generate_xlsx_bytes(headers: list[str], rows: list[list[Any]]) -> bytes:
    """Generate a valid OpenXML (.xlsx) spreadsheet workbook using standard library."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
            ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
            ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        zf.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/>
</Relationships>""",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
</Relationships>""",
        )
        zf.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="SteamScoop_Export" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>""",
        )

        sheet_lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            "<sheetData>",
        ]
        row_idx = 1
        # Header row
        sheet_lines.append(f'<row r="{row_idx}">')
        for h in headers:
            esc = xml.sax.saxutils.escape(str(h))
            sheet_lines.append(f'<c t="inlineStr"><is><t>{esc}</t></is></c>')
        sheet_lines.append("</row>")

        # Data rows
        for r in rows:
            row_idx += 1
            sheet_lines.append(f'<row r="{row_idx}">')
            for val in r:
                if val is None:
                    sheet_lines.append("<c/>")
                elif isinstance(val, bool):
                    sheet_lines.append(f'<c t="b"><v>{1 if val else 0}</v></c>')
                elif isinstance(val, (int, float)):
                    sheet_lines.append(f"<c><v>{val}</v></c>")
                else:
                    esc = xml.sax.saxutils.escape(str(val))
                    sheet_lines.append(f'<c t="inlineStr"><is><t>{esc}</t></is></c>')
            sheet_lines.append("</row>")

        sheet_lines.extend(["</sheetData>", "</worksheet>"])
        zf.writestr("xl/worksheets/sheet1.xml", "".join(sheet_lines))

    return buf.getvalue()


class ExportService:
    """Domain service for asynchronous analytical exports and lifecycle state."""

    def __init__(
        self,
        session: Session,
        export_repo: ExportRepository | None = None,
        game_repo: GameRepository | None = None,
        review_repo: ReviewRepository | None = None,
        workspace_repo: WorkspaceRepository | None = None,
    ) -> None:
        self.session = session
        self.export_repo = export_repo or ExportRepository(session)
        self.game_repo = game_repo or GameRepository(session)
        self.review_repo = review_repo or ReviewRepository(session)
        self.workspace_repo = workspace_repo or WorkspaceRepository(session)

    def _resolve_secure_storage_path(self, export_id: uuid.UUID, format_ext: str) -> str:
        """Resolve absolute filesystem path for an export artifact, preventing path traversal."""
        storage_dir = os.path.abspath(settings.EXPORT_STORAGE_PATH)
        os.makedirs(storage_dir, exist_ok=True)
        filename = f"{export_id}.{format_ext}"
        resolved = os.path.abspath(os.path.join(storage_dir, filename))

        if os.path.commonpath([resolved, storage_dir]) != storage_dir:
            raise ValidationException(
                field="export_id",
                issue="Path traversal attack detected on artifact storage destination.",
            )
        return resolved

    def _log_audit(
        self,
        actor_user_id: uuid.UUID,
        action: str,
        export_id: uuid.UUID,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append an entry to the audit log."""
        try:
            audit = AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                resource_type="export_job",
                resource_id=str(export_id),
                metadata_=metadata or {},
            )
            self.session.add(audit)
            self.session.commit()
        except Exception as exc:
            logger.warning("Failed to record audit log for %s (%s): %s", action, export_id, exc)

    def get_role_row_limit(self, user_roles: list[str] | None = None) -> int:
        """Resolve maximum row allowance based on user roles."""
        roles = set(user_roles or [])
        if "admin" in roles:
            return settings.EXPORT_ADMIN_ROW_LIMIT
        if "researcher" in roles:
            return settings.EXPORT_RESEARCHER_ROW_LIMIT
        return settings.EXPORT_DEFAULT_ROW_LIMIT

    def create_export(
        self,
        user: User,
        request: ExportCreateRequest,
        user_roles: list[str] | None = None,
    ) -> ExportResponseData:
        """Validate export parameters, enforce quotas, and enqueue asynchronous job."""
        # 1. Format validation
        if request.format not in ("csv", "json", "xlsx"):
            raise ValidationException(
                field="format",
                issue="Supported export formats are 'csv', 'json', and 'xlsx'.",
            )

        # 2. Fields validation
        invalid_fields = [f for f in request.fields if f not in ALLOWED_EXPORT_FIELDS]
        if invalid_fields:
            allowed = sorted(ALLOWED_EXPORT_FIELDS)
            raise ValidationException(
                field="fields",
                issue=f"Unsupported export fields: {invalid_fields}. Allowed fields: {allowed}",
            )

        # 3. Scope validation
        scope_type = request.scope.get("type")
        if scope_type not in ("game_reviews", "reviews", "project_reviews"):
            raise ValidationException(
                field="scope.type",
                issue=(
                    "Supported export scope types are 'game_reviews', "
                    "'reviews', or 'project_reviews'."
                ),
            )

        target_project_id: uuid.UUID | None = None
        if scope_type == "game_reviews":
            if "game_id" not in request.scope:
                raise ValidationException(
                    field="scope.game_id", issue="scope.game_id is required for game_reviews."
                )
            try:
                target_game_id = uuid.UUID(str(request.scope["game_id"]))
            except (ValueError, TypeError) as err:
                raise ValidationException(
                    field="scope.game_id", issue="game_id must be a valid UUID."
                ) from err

            game = self.game_repo.get_by_id(target_game_id)
            if not game:
                raise GameNotFoundError(target_game_id)

        elif scope_type == "project_reviews":
            if "project_id" not in request.scope:
                raise ValidationException(
                    field="scope.project_id",
                    issue="scope.project_id is required for project_reviews.",
                )
            try:
                target_project_id = uuid.UUID(str(request.scope["project_id"]))
            except (ValueError, TypeError) as err:
                raise ValidationException(
                    field="scope.project_id", issue="project_id must be a valid UUID."
                ) from err

            # Verify caller has project access (prevent leaking private project cohorts)
            project = self.workspace_repo.get_by_id(target_project_id)
            if not project:
                raise ProjectNotFoundError(target_project_id)

            is_admin = bool(user_roles and "admin" in user_roles)
            if not is_admin:
                role = self.workspace_repo.get_user_project_role(target_project_id, user.id)
                if not role:
                    raise ProjectNotFoundError(target_project_id)

        # 4. Filters & Date Range Validation
        filters = request.filters or {}
        from_str = filters.get("from")
        to_str = filters.get("to")
        if from_str or to_str:
            from_d: date | None = None
            to_d: date | None = None
            if from_str:
                try:
                    from_d = date.fromisoformat(str(from_str))
                except ValueError as err:
                    raise ValidationException(
                        field="filters.from", issue="Invalid ISO date format for 'from' filter."
                    ) from err
            if to_str:
                try:
                    to_d = date.fromisoformat(str(to_str))
                except ValueError as err:
                    raise ValidationException(
                        field="filters.to", issue="Invalid ISO date format for 'to' filter."
                    ) from err
            if from_d and to_d:
                if from_d > to_d:
                    raise ValidationException(
                        field="filters.from",
                        issue="'from' date cannot be after 'to' date.",
                    )
                if (to_d - from_d).days > 730:
                    raise ValidationException(
                        field="filters",
                        issue="Maximum allowable export date range is 730 days (2 years).",
                    )

        # 5. Concurrency quota check
        active_count = self.export_repo.count_active_jobs_by_user(user.id)
        if active_count >= settings.EXPORT_MAX_ACTIVE_PER_USER:
            raise ExportConcurrencyLimitError(
                active_count=active_count,
                limit=settings.EXPORT_MAX_ACTIVE_PER_USER,
            )

        # 6. Row limit quota validation
        role_limit = self.get_role_row_limit(user_roles)
        if request.row_limit is not None and request.row_limit > role_limit:
            raise ExportLimitExceededError(
                reason=(
                    f"Requested row limit {request.row_limit:,} exceeds your role allowance of "
                    f"{role_limit:,} rows."
                )
            )

        effective_row_limit = request.row_limit or role_limit

        # 7. Create queued job entity
        job = self.export_repo.create_export_job(
            requested_by_user_id=user.id,
            export_format=request.format,
            scope=request.scope,
            filters=request.filters,
            fields=request.fields,
            project_id=target_project_id,
            row_limit=effective_row_limit,
            ttl_days=settings.EXPORT_DEFAULT_TTL_DAYS,
        )

        # 8. Record audit log
        self._log_audit(
            actor_user_id=user.id,
            action="export.created",
            export_id=job.id,
            metadata={"format": job.format, "scope": job.export_config.get("scope")},
        )

        # 9. Queue Celery asynchronous task
        try:
            from app.workers.tasks import generate_export_artifact

            generate_export_artifact.delay(str(job.id))
        except Exception as exc:
            logger.warning("Could not dispatch Celery task for export %s: %s", job.id, exc)

        return ExportResponseData(
            export_id=job.id,
            status=job.status,  # type: ignore[arg-type]
            format=job.format,
            row_count=job.row_count,
            file_size_bytes=job.export_config.get("file_size_bytes"),
            error_code=job.error_code,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            expires_at=job.expires_at,
        )

    def generate_artifact(self, export_id: uuid.UUID) -> ExportJob:
        """Worker execution method to fetch data, generate artifact, and enforce limits."""
        job = self.export_repo.get_by_id(export_id)
        if not job or job.status in ("cancelled", "expired"):
            return job or ExportJob(id=export_id, status="failed")

        now = datetime.now(UTC)
        job.status = "running"
        job.started_at = now
        self.session.commit()

        config = job.export_config or {}
        scope = config.get("scope", {})
        filters = config.get("filters", {})
        fields = config.get("fields", ["review_text", "language", "sentiment"])
        row_limit = config.get("row_limit", settings.EXPORT_DEFAULT_ROW_LIMIT)

        try:
            # 1. Resolve target game IDs
            game_ids: list[uuid.UUID] = []
            if scope.get("type") == "game_reviews" and "game_id" in scope:
                game_ids = [uuid.UUID(str(scope["game_id"]))]
            elif scope.get("type") == "project_reviews" and "project_id" in scope:
                project_id = uuid.UUID(str(scope["project_id"]))
                project_games = self.workspace_repo.list_project_games(project_id)
                game_ids = [pg.game_id for pg in project_games]

            # 2. Build filtered reviews query joined with sentiment
            stmt = select(Review, SentimentPrediction).outerjoin(
                SentimentPrediction,
                and_(
                    SentimentPrediction.review_id == Review.id,
                    SentimentPrediction.is_current.is_(True),
                ),
            )

            if game_ids:
                stmt = stmt.where(Review.game_id.in_(game_ids))

            if "language" in filters:
                lang = filters["language"]
                if isinstance(lang, list):
                    stmt = stmt.where(Review.language.in_(lang))
                elif isinstance(lang, str):
                    stmt = stmt.where(Review.language == lang)

            if "voted_up" in filters:
                stmt = stmt.where(Review.voted_up == bool(filters["voted_up"]))

            if "sentiment" in filters and filters["sentiment"] != "all":
                stmt = stmt.where(SentimentPrediction.label == filters["sentiment"])

            if "from" in filters:
                from_dt = datetime.fromisoformat(str(filters["from"]))
                stmt = stmt.where(Review.steam_created_at >= from_dt)

            if "to" in filters:
                to_dt = datetime.fromisoformat(str(filters["to"]))
                stmt = stmt.where(Review.steam_created_at <= to_dt)

            # Order consistently and fetch row_limit + 1 to detect overflow
            stmt = stmt.order_by(Review.steam_created_at.desc().nullslast()).limit(row_limit + 1)
            results = self.session.execute(stmt).all()

            # 3. Check row limit overflow
            if len(results) > row_limit:
                job.status = "failed"
                job.error_code = "EXPORT_ROW_LIMIT_EXCEEDED"
                job.finished_at = datetime.now(UTC)
                self.session.commit()
                return job

            # 4. Extract data records
            records: list[dict[str, Any]] = []
            review_ids = [r.id for r, _ in results]

            # Pre-fetch aspects if requested
            aspects_by_review: dict[uuid.UUID, list[str]] = {}
            if "aspects" in fields and review_ids:
                aspect_stmt = select(AspectPrediction).where(
                    AspectPrediction.review_id.in_(review_ids),
                    AspectPrediction.is_current.is_(True),
                )
                for asp in self.session.scalars(aspect_stmt).all():
                    aspects_by_review.setdefault(asp.review_id, []).append(asp.aspect)

            # Pre-fetch topics if requested
            topics_by_review: dict[uuid.UUID, list[str]] = {}
            if "topics" in fields and review_ids:
                topic_stmt = (
                    select(ReviewTopic.review_id, Topic.label)
                    .join(Topic, ReviewTopic.topic_id == Topic.id)
                    .where(ReviewTopic.review_id.in_(review_ids))
                )
                for rev_id, top_label in self.session.execute(topic_stmt).all():
                    topics_by_review.setdefault(rev_id, []).append(top_label)

            for review, sentiment in results:
                row_dict: dict[str, Any] = {}
                for f in fields:
                    if f == "sentiment":
                        row_dict[f] = (
                            sentiment.label
                            if sentiment
                            else ("positive" if review.voted_up else "negative")
                        )
                    elif f == "sentiment_confidence":
                        row_dict[f] = float(sentiment.confidence) if sentiment else None
                    elif f == "aspects":
                        row_dict[f] = "; ".join(aspects_by_review.get(review.id, []))
                    elif f == "topics":
                        row_dict[f] = "; ".join(topics_by_review.get(review.id, []))
                    elif hasattr(review, f):
                        val = getattr(review, f)
                        if isinstance(val, datetime):
                            row_dict[f] = val.isoformat()
                        else:
                            row_dict[f] = val
                    else:
                        row_dict[f] = None
                records.append(row_dict)

            # 5. Format artifact bytes
            content_bytes: bytes
            if job.format == "json":
                content_bytes = json.dumps(records, indent=2, default=str).encode("utf-8")
            elif job.format == "xlsx":
                table_rows = [[rec.get(col) for col in fields] for rec in records]
                content_bytes = generate_xlsx_bytes(headers=fields, rows=table_rows)
            else:  # csv
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=fields)
                writer.writeheader()
                for rec in records:
                    writer.writerow(rec)
                content_bytes = out.getvalue().encode("utf-8")

            # 6. Check file-size limit
            if len(content_bytes) > settings.EXPORT_MAX_FILE_SIZE_BYTES:
                job.status = "failed"
                job.error_code = "EXPORT_FILE_SIZE_LIMIT_EXCEEDED"
                job.finished_at = datetime.now(UTC)
                self.session.commit()
                return job

            # 7. Write to secure private disk storage
            file_path = self._resolve_secure_storage_path(job.id, job.format)
            with open(file_path, "wb") as f:
                f.write(content_bytes)

            # 8. Mark job completed
            job.status = "succeeded"
            job.row_count = len(records)
            job.artifact_uri = file_path
            job.error_code = None
            job.finished_at = datetime.now(UTC)
            updated_config = dict(job.export_config)
            updated_config["file_size_bytes"] = len(content_bytes)
            job.export_config = updated_config

            self.session.commit()
            self.session.refresh(job)
            return job

        except Exception as exc:
            logger.exception("Failed during artifact generation for job %s: %s", export_id, exc)
            self.session.rollback()
            job = self.export_repo.get_by_id(export_id)
            if job:
                job.status = "failed"
                job.error_code = "GENERATION_FAILED"
                job.finished_at = datetime.now(UTC)
                self.session.commit()
            return job or ExportJob(id=export_id, status="failed")

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

        # Check expiration cutoff
        now = datetime.now(UTC)
        if job.expires_at and job.expires_at < now and job.status != "expired":
            job.status = "expired"
            if job.artifact_uri and os.path.exists(job.artifact_uri):
                with contextlib.suppress(OSError):
                    os.remove(job.artifact_uri)
            self.session.commit()

        file_size = (job.export_config or {}).get("file_size_bytes")

        return ExportResponseData(
            export_id=job.id,
            status=job.status,  # type: ignore[arg-type]
            format=job.format,
            row_count=job.row_count,
            file_size_bytes=file_size,
            error_code=job.error_code,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            expires_at=job.expires_at,
        )

    def download_export(
        self,
        user: User,
        export_id: uuid.UUID,
        user_roles: list[str] | None = None,
    ) -> tuple[str, str, bytes]:
        """Verify download authorization, validate artifact integrity, and return file bytes."""
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
        if (job.expires_at and job.expires_at < now) or job.status == "expired":
            if job.status != "expired":
                job.status = "expired"
                if job.artifact_uri and os.path.exists(job.artifact_uri):
                    with contextlib.suppress(OSError):
                        os.remove(job.artifact_uri)
                self.session.commit()
            raise ExportExpiredError(export_id)

        # Check cancellation
        if job.status == "cancelled":
            raise ExportCancelledError(export_id)

        # Check failed state
        if job.status == "failed":
            raise ExportFailedError(export_id, error_code=job.error_code)

        # If job is still queued or running, run generation synchronously if artifact is missing
        # (graceful fallback for testing or standalone API environments without Celery worker)
        if job.status in ("queued", "running") or not job.artifact_uri:
            job = self.generate_artifact(export_id)
            if job.status == "failed":
                raise ExportFailedError(export_id, error_code=job.error_code)
            if job.status != "succeeded":
                raise ExportNotReadyError(export_id, status=job.status)

        # Validate artifact file path and ensure no path traversal
        file_path = self._resolve_secure_storage_path(job.id, job.format)
        if not os.path.exists(file_path):
            # Regenerate if file was temporarily purged
            job = self.generate_artifact(export_id)
            if not os.path.exists(file_path):
                raise ExportNotFoundError(export_id)

        with open(file_path, "rb") as f:
            content = f.read()

        # Resolve MIME type
        if job.format == "json":
            media_type = "application/json; charset=utf-8"
        elif job.format == "xlsx":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            media_type = "text/csv; charset=utf-8"

        filename = f"export_{export_id}.{job.format}"

        # Record audit log
        self._log_audit(
            actor_user_id=user.id,
            action="export.downloaded",
            export_id=export_id,
            metadata={"format": job.format, "size_bytes": len(content)},
        )

        return filename, media_type, content

    def cancel_export(
        self,
        user: User,
        export_id: uuid.UUID,
        user_roles: list[str] | None = None,
    ) -> bool:
        """Cancel a queued or running export job or revoke an existing artifact."""
        is_admin = bool(user_roles and "admin" in user_roles)
        job: ExportJob | None = None

        if is_admin:
            job = self.export_repo.get_by_id(export_id)
        else:
            job = self.export_repo.get_by_user(export_id, user.id)

        if not job:
            raise ExportNotFoundError(export_id)

        cancelled_job = self.export_repo.cancel_export(
            export_id=export_id,
            user_id=user.id if not is_admin else None,
            is_admin=is_admin,
        )

        if not cancelled_job:
            return False

        # Clean up artifact file if it exists
        if cancelled_job.artifact_uri and os.path.exists(cancelled_job.artifact_uri):
            try:
                os.remove(cancelled_job.artifact_uri)
            except OSError as exc:
                logger.warning(
                    "Could not remove artifact for cancelled export %s: %s", export_id, exc
                )

        # Revoke Celery task if possible
        try:
            from app.workers.celery_app import celery_app

            celery_app.control.revoke(str(export_id), terminate=True)
        except Exception:
            pass

        self._log_audit(
            actor_user_id=user.id,
            action="export.cancelled",
            export_id=export_id,
        )

        return True

    def cleanup_expired_exports(self) -> int:
        """Scan expired export jobs, delete artifact files from disk, and update statuses."""
        now = datetime.now(UTC)
        expired_jobs = self.export_repo.get_expired_jobs(now)
        purged = 0

        for job in expired_jobs:
            if job.artifact_uri and os.path.exists(job.artifact_uri):
                try:
                    os.remove(job.artifact_uri)
                except OSError as exc:
                    logger.warning("Error purging expired file %s: %s", job.artifact_uri, exc)
            job.status = "expired"
            job.artifact_uri = None
            purged += 1

        if purged > 0:
            self.session.commit()
            logger.info("Purged %d expired export artifacts", purged)

        return purged
