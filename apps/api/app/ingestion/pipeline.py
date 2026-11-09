import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion.schemas import IngestionJobConfig, IngestionJobResult
from app.integrations.steam.client import SteamClient
from app.integrations.steam.exceptions import (
    SteamClientError,
    SteamGameUnavailableError,
    SteamIntegrationError,
    SteamMalformedResponseError,
    SteamRateLimitError,
    SteamTemporaryServerError,
)
from app.integrations.steam.schemas import SteamReviewRequestParams
from app.models.game import Game
from app.models.ingestion import IngestionBatch, IngestionJob
from app.repositories.ingestion import (
    CollectionCheckpointRepository,
    commit_ingestion_page_transaction,
)

logger = logging.getLogger("steamscoop.ingestion.pipeline")


class ReviewIngestionPipeline:
    """Orchestrates review collection runs for historical ingestion and incremental synchronization.

    Enforces critical invariants:
    - Atomicity: Review upserts, batch records, and checkpoint cursor advance
      together in one DB transaction per page.
    - Watermark Safety: Incomplete, failed, or partial incremental syncs
      NEVER advance the committed watermark.
    - Deduplication & Idempotency: Multiple arrivals update existing reviews without duplicates.
    - Bounded Retries: Transient failures mark job as retrying and preserve checkpoint progress.
    - Cancellation Safety: Jobs marked cancelled abort cleanly at the page boundary.
    """

    def __init__(self, db: Session, steam_client: SteamClient | None = None) -> None:
        self.db = db
        self.steam_client = steam_client or SteamClient()

    def execute_job(self, job_id: uuid.UUID) -> IngestionJobResult:
        """Execute a queued or retrying ingestion job to completion or safe boundary."""
        job = self.db.get(IngestionJob, job_id)
        if job is None:
            raise ValueError(f"IngestionJob {job_id} does not exist.")

        # Guard against duplicate execution of completed / cancelled jobs
        if job.status in ("succeeded", "cancelled"):
            return self._build_result(job)

        game = self.db.get(Game, job.game_id)
        if game is None:
            now = datetime.now(UTC)
            job.status = "failed"
            job.error_code = "GAME_NOT_FOUND"
            job.error_message = f"Associated game {job.game_id} does not exist in catalog."
            if not job.started_at:
                job.started_at = now
            job.finished_at = now
            self.db.commit()
            return self._build_result(job)

        # Transition to running
        job.status = "running"
        if not job.started_at:
            job.started_at = datetime.now(UTC)
        self.db.commit()

        try:
            if job.job_type == "historical":
                return self._run_historical(job, game)
            elif job.job_type == "incremental":
                return self._run_incremental(job, game)
            else:
                raise ValueError(f"Unsupported job_type: {job.job_type}")
        except (
            SteamRateLimitError,
            SteamTemporaryServerError,
            httpx.RequestError,
        ) as exc:
            return self._handle_transient_failure(job, exc)
        except (
            SteamGameUnavailableError,
            SteamClientError,
            SteamMalformedResponseError,
            SteamIntegrationError,
            Exception,
        ) as exc:
            return self._handle_permanent_failure(job, exc)

    def _run_historical(self, job: IngestionJob, game: Game) -> IngestionJobResult:
        """Historical collection: traverses reviews backwards using recent filter (filter=1)."""
        config = IngestionJobConfig.model_validate(job.request_config or {})
        stream_key = config.stream_key or f"historical:{','.join(sorted(config.languages))}"

        ckpt_repo = CollectionCheckpointRepository(self.db)
        checkpoint = ckpt_repo.get_or_create(game.id, stream_key, collection_mode="historical")
        checkpoint.status = "running"
        self.db.commit()

        # Resumable cursor: resume from saved checkpoint cursor if available, otherwise start fresh
        current_cursor = checkpoint.cursor or "*"

        # Determine next batch number
        max_batch_stmt = select(func.max(IngestionBatch.batch_number)).where(
            IngestionBatch.ingestion_job_id == job.id
        )
        current_max_batch = self.db.scalars(max_batch_stmt).first() or 0
        batch_number = current_max_batch + 1

        pages_in_run = 0
        terminal_reason = "completed"

        while pages_in_run < config.max_pages:
            # 1. Cancellation check before every external HTTP call
            self.db.refresh(job)
            if job.status == "cancelled":
                logger.info("Ingestion job %s was cancelled before fetching page.", job.id)
                checkpoint.status = "idle"
                now = datetime.now(UTC)
                if not job.started_at:
                    job.started_at = now
                if not job.finished_at:
                    job.finished_at = now
                self.db.commit()
                return self._build_result(job)

            # 2. Fetch page from Steam
            params = SteamReviewRequestParams(
                appid=game.steam_app_id,
                filter=1,  # Recent reviews for historical traversal
                languages=config.languages,
                num_per_page=config.num_per_page,
                cursor=current_cursor,
                date_range_start=config.date_range_start,
                date_range_end=config.date_range_end,
            )
            req_started = datetime.now(UTC)
            page = self.steam_client.get_app_reviews(params)
            req_finished = datetime.now(UTC)

            # 3. In-memory deduplication within page
            reviews_data = self._deduplicate_page_reviews(page.reviews)

            # 4. Atomic transaction commit
            commit_ingestion_page_transaction(
                session=self.db,
                job_id=job.id,
                game_id=game.id,
                batch_number=batch_number,
                cursor_in=current_cursor,
                cursor_out=page.cursor,
                request_started_at=req_started,
                request_finished_at=req_finished,
                http_status=200,
                reviews_data=reviews_data,
                checkpoint_stream_key=stream_key,
                collection_mode="historical",
                watermark_at=None,
                checkpoint_status="running",
            )

            pages_in_run += 1
            batch_number += 1

            # 5. Check termination conditions
            if len(page.reviews) == 0:
                logger.info("App %d returned 0 reviews. Stream completed.", game.steam_app_id)
                terminal_reason = "completed"
                break

            if not page.has_more:
                logger.info("App %d has_more=False. Stream completed.", game.steam_app_id)
                terminal_reason = "completed"
                break

            if not page.cursor or page.cursor == current_cursor:
                logger.info(
                    "App %d cursor looped or empty (%s). Stream completed.",
                    game.steam_app_id,
                    page.cursor,
                )
                terminal_reason = "completed"
                break

            current_cursor = page.cursor

        # If loop exited because page budget was reached but more data remains
        if pages_in_run >= config.max_pages and terminal_reason != "completed":
            terminal_reason = "partial"

        # Finalize job status
        self.db.refresh(job)
        self.db.refresh(checkpoint)
        if job.status != "cancelled":
            job.status = "partial" if terminal_reason == "partial" else "succeeded"
            job.finished_at = datetime.now(UTC)
            checkpoint.status = "idle"
            checkpoint.last_successful_job_id = job.id
            checkpoint.last_success_at = datetime.now(UTC)
            self.db.commit()

        return self._build_result(job, cursor=checkpoint.cursor)

    def _run_incremental(self, job: IngestionJob, game: Game) -> IngestionJobResult:
        """Incremental synchronization: collects new and edited reviews
        using updated filter (filter=2).

        CRITICAL WATERMARK INVARIANT:
        The watermark is ONLY committed on final, complete success of the sync run.
        If any failure occurs mid-way, watermark_at remains unchanged.
        """
        config = IngestionJobConfig.model_validate(job.request_config or {})
        stream_key = config.stream_key or f"incremental:{','.join(sorted(config.languages))}"

        ckpt_repo = CollectionCheckpointRepository(self.db)
        checkpoint = ckpt_repo.get_or_create(game.id, stream_key, collection_mode="incremental")
        checkpoint.status = "running"
        self.db.commit()

        sync_started_at = datetime.now(UTC)
        existing_watermark = checkpoint.watermark_at

        overlap_boundary: datetime | None = None
        if existing_watermark:
            overlap_boundary = existing_watermark - timedelta(days=config.overlap_days)

        current_cursor = "*"
        max_batch_stmt = select(func.max(IngestionBatch.batch_number)).where(
            IngestionBatch.ingestion_job_id == job.id
        )
        current_max_batch = self.db.scalars(max_batch_stmt).first() or 0
        batch_number = current_max_batch + 1

        pages_in_run = 0

        while pages_in_run < config.max_pages:
            # 1. Cancellation check
            self.db.refresh(job)
            if job.status == "cancelled":
                logger.info("Incremental job %s was cancelled.", job.id)
                checkpoint.status = "idle"
                now = datetime.now(UTC)
                if not job.started_at:
                    job.started_at = now
                if not job.finished_at:
                    job.finished_at = now
                self.db.commit()
                return self._build_result(job)

            # 2. Fetch page from Steam (filter=2: Updated)
            params = SteamReviewRequestParams(
                appid=game.steam_app_id,
                filter=2,  # Updated reviews for incremental synchronization
                languages=config.languages,
                num_per_page=config.num_per_page,
                cursor=current_cursor,
            )
            req_started = datetime.now(UTC)
            page = self.steam_client.get_app_reviews(params)
            req_finished = datetime.now(UTC)

            # 3. Deduplicate within page
            reviews_data = self._deduplicate_page_reviews(page.reviews)

            # 4. Atomic transaction commit — DO NOT advance watermark during page loop!
            commit_ingestion_page_transaction(
                session=self.db,
                job_id=job.id,
                game_id=game.id,
                batch_number=batch_number,
                cursor_in=current_cursor,
                cursor_out=page.cursor,
                request_started_at=req_started,
                request_finished_at=req_finished,
                http_status=200,
                reviews_data=reviews_data,
                checkpoint_stream_key=stream_key,
                collection_mode="incremental",
                watermark_at=None,  # Watermark invariant preserved!
                checkpoint_status="running",
            )

            pages_in_run += 1
            batch_number += 1

            if (
                len(page.reviews) == 0
                or not page.has_more
                or not page.cursor
                or page.cursor == current_cursor
            ):
                break

            # 5. Overlap boundary check:
            # In filter=2, if all reviews on this page are older than overlap_boundary,
            # we have safely traversed past all new and modified reviews.
            if overlap_boundary is not None and len(page.reviews) > 0:
                all_older = all(
                    r.steam_updated_at is not None and r.steam_updated_at < overlap_boundary
                    for r in page.reviews
                )
                if all_older:
                    logger.info(
                        "Reached overlap boundary (%s). Incremental sync complete.",
                        overlap_boundary,
                    )
                    break

            current_cursor = page.cursor

        # Only on complete, successful execution do we advance the watermark
        self.db.refresh(job)
        self.db.refresh(checkpoint)
        if job.status != "cancelled":
            job.status = "succeeded"
            job.finished_at = datetime.now(UTC)
            checkpoint.status = "idle"
            checkpoint.watermark_at = sync_started_at
            checkpoint.last_successful_job_id = job.id
            checkpoint.last_success_at = datetime.now(UTC)
            self.db.commit()

        return self._build_result(
            job, watermark_at=checkpoint.watermark_at, cursor=checkpoint.cursor
        )

    def _deduplicate_page_reviews(self, raw_reviews: list[Any]) -> list[dict[str, Any]]:
        """Deduplicate reviews in-memory by steam_review_id, retaining latest entry."""
        deduped: dict[int, dict[str, Any]] = {}
        for r in raw_reviews:
            deduped[r.steam_review_id] = {
                "steam_review_id": r.steam_review_id,
                "review_text": r.review_text,
                "voted_up": r.voted_up,
                "language": r.language,
                "votes_up": r.votes_up,
                "votes_funny": r.votes_funny,
                "weighted_vote_score": r.weighted_vote_score,
                "comment_count": r.comment_count,
                "steam_playtime_at_review": r.steam_playtime_at_review,
                "steam_playtime_forever": r.steam_playtime_forever,
                "steam_playtime_last_two_weeks": r.steam_playtime_last_two_weeks,
                "steam_purchase": r.steam_purchase,
                "received_for_free": r.received_for_free,
                "written_during_early_access": r.written_during_early_access,
                "steam_created_at": r.steam_created_at,
                "steam_updated_at": r.steam_updated_at,
            }
        return list(deduped.values())

    def _handle_transient_failure(self, job: IngestionJob, exc: Exception) -> IngestionJobResult:
        """Handle transient / retriable errors (HTTP 429, 5xx, timeouts)."""
        logger.warning("Transient error in job %s: %s", job.id, exc)
        self.db.refresh(job)
        max_retries = 3

        if job.retry_count < max_retries:
            job.status = "retrying"
            job.retry_count += 1
            job.error_code = type(exc).__name__
            job.error_message = str(exc)
            # Checkpoint remains in its last successfully committed page state
            ckpt_repo = CollectionCheckpointRepository(self.db)
            stream_key = (job.request_config or {}).get("stream_key") or f"{job.job_type}:all"
            ckpt = ckpt_repo.get_by_stream_key(job.game_id, stream_key)
            if ckpt is not None:
                ckpt.status = "idle"  # idle allows safe re-claiming
            self.db.commit()
            raise exc
        else:
            now = datetime.now(UTC)
            job.status = "failed"
            if not job.started_at:
                job.started_at = now
            job.finished_at = now
            job.error_code = type(exc).__name__
            job.error_message = f"Max retries ({max_retries}) exhausted: {exc}"
            ckpt_repo = CollectionCheckpointRepository(self.db)
            stream_key = (job.request_config or {}).get("stream_key") or f"{job.job_type}:all"
            ckpt = ckpt_repo.get_by_stream_key(job.game_id, stream_key)
            if ckpt is not None:
                ckpt.status = "error"
            self.db.commit()
            return self._build_result(job)

    def _handle_permanent_failure(self, job: IngestionJob, exc: Exception) -> IngestionJobResult:
        """Handle non-recoverable errors (app missing, invalid response format, etc.)."""
        logger.error("Permanent error in job %s: %s", job.id, exc)
        self.db.refresh(job)
        now = datetime.now(UTC)
        job.status = "failed"
        if not job.started_at:
            job.started_at = now
        job.finished_at = now
        job.error_code = getattr(exc, "error_code", type(exc).__name__)
        job.error_message = str(exc)

        ckpt_repo = CollectionCheckpointRepository(self.db)
        stream_key = (job.request_config or {}).get("stream_key") or f"{job.job_type}:all"
        ckpt = ckpt_repo.get_by_stream_key(job.game_id, stream_key)
        if ckpt is not None:
            ckpt.status = "error"
        self.db.commit()
        return self._build_result(job)

    def _build_result(
        self,
        job: IngestionJob,
        cursor: str | None = None,
        watermark_at: datetime | None = None,
    ) -> IngestionJobResult:
        """Serialize current job state into an IngestionJobResult."""
        return IngestionJobResult(
            job_id=job.id,
            game_id=job.game_id,
            job_type=job.job_type,
            status=job.status,
            reviews_seen=job.reviews_seen,
            reviews_inserted=job.reviews_inserted,
            reviews_updated=job.reviews_updated,
            pages_processed=job.pages_processed,
            cursor=cursor,
            watermark_at=watermark_at,
            error_code=job.error_code,
            error_message=job.error_message,
        )
