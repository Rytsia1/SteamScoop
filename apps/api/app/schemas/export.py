"""Schemas for asynchronous data export requests and artifacts."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ExportCreateRequest(BaseModel):
    """Payload for POST /exports."""

    format: Literal["csv", "json"] = "csv"
    scope: dict[str, Any] = Field(
        description="Target resource scope (e.g. {'type': 'game_reviews', 'game_id': '...'})"
    )
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Query filters applied to export"
    )
    fields: list[str] = Field(min_length=1, max_length=20, description="Allowlisted export fields")


class ExportResponseData(BaseModel):
    """Representation of an asynchronous export job."""

    export_id: uuid.UUID
    status: Literal["queued", "running", "succeeded", "failed", "expired", "cancelled"]
    format: str
    row_count: int | None = None
    created_at: datetime
    finished_at: datetime | None = None
    expires_at: datetime | None = None
