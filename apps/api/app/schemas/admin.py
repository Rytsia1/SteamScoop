"""Schemas for administrative operations, ingestion monitoring, and model activation."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AdminGameCreateRequest(BaseModel):
    """Payload for POST /admin/games."""

    steam_app_id: int = Field(gt=0, description="Official Steam App ID")
    name: str = Field(min_length=1, max_length=255)
    short_description: str | None = None
    genres: list[str] = Field(default_factory=list)
    release_date: date | None = None
    is_free: bool = False
    catalog_status: Literal["pending", "indexed", "failed", "disabled"] = "indexed"


class AdminGameUpdateRequest(BaseModel):
    """Payload for PATCH /admin/games/{game_id}."""

    name: str | None = None
    short_description: str | None = None
    catalog_status: Literal["pending", "indexed", "failed", "disabled"] | None = None
    is_active: bool | None = None


class AdminGameResponse(BaseModel):
    """Catalog game record for admin management."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    steam_app_id: int
    name: str
    catalog_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminIngestionJobCreateRequest(BaseModel):
    """Payload for POST /admin/games/{game_id}/ingestion-jobs."""

    job_type: Literal["historical", "incremental"]
    collection_config: dict[str, Any] = Field(
        default_factory=lambda: {
            "review_type": "all",
            "purchase_type": "all",
            "languages": ["all"],
            "overlap_days": 14,
        }
    )
    reason: str = Field(min_length=3, max_length=255)


class AdminIngestionJobResponse(BaseModel):
    """Admin representation of an ingestion job."""

    model_config = ConfigDict(from_attributes=True)

    job_id: uuid.UUID
    game_id: uuid.UUID
    job_type: str
    status: str
    target_reviews: int = 0
    collected_reviews: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @classmethod
    def from_model(cls, job: Any) -> AdminIngestionJobResponse:
        return cls(
            job_id=job.id,
            game_id=job.game_id,
            job_type=job.job_type,
            status=job.status,
            target_reviews=getattr(job, "reviews_seen", 0) or 0,
            collected_reviews=getattr(job, "reviews_inserted", 0) or 0,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )


class AdminPipelineRunResponse(BaseModel):
    """Admin representation of an ML/Analytics pipeline execution."""

    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    pipeline_type: str
    status: str
    model_version_snapshot: str | None = None
    input_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    started_at: datetime
    finished_at: datetime | None = None

    @classmethod
    def from_model(cls, run: Any) -> AdminPipelineRunResponse:
        return cls(
            run_id=run.id,
            pipeline_type=run.pipeline_type,
            status=run.status,
            model_version_snapshot=run.model_version_snapshot,
            input_count=run.input_count or 0,
            success_count=run.success_count or 0,
            failure_count=run.failure_count or 0,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )


class AdminModelResponse(BaseModel):
    """Model registry item for admin inspection."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    model_key: str
    version: str
    task: str
    framework: str
    is_active: bool
    created_at: datetime


class AdminModelActivateResponse(BaseModel):
    """Response payload for POST /admin/models/{model_id}/activate."""

    model_id: uuid.UUID
    task: str
    is_active: bool
    message: str
