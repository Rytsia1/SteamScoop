import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestionJobConfig(BaseModel):
    """Configuration parameters for historical or incremental review ingestion."""

    model_config = ConfigDict(extra="ignore")

    languages: list[str] = Field(
        default_factory=lambda: ["all"],
        description="List of ISO-639 / Steam language codes or ['all']",
    )
    max_pages: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of review pages to process in this job run",
    )
    num_per_page: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Number of reviews requested per Steam API page (max 100)",
    )
    date_range_start: int | None = Field(
        default=None,
        ge=0,
        description="Optional Unix timestamp filter start boundary",
    )
    date_range_end: int | None = Field(
        default=None,
        ge=0,
        description="Optional Unix timestamp filter end boundary",
    )
    overlap_days: int = Field(
        default=14,
        ge=1,
        le=90,
        description="Overlap safety window in days for incremental review synchronization",
    )
    stream_key: str | None = Field(
        default=None,
        description="Unique stream partition key (e.g. 'historical:all' or 'incremental:all')",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to a JSON-compatible dictionary."""
        return self.model_dump(mode="json")


class IngestionJobResult(BaseModel):
    """Result summary of an executed review ingestion job."""

    model_config = ConfigDict(frozen=True)

    job_id: uuid.UUID
    game_id: uuid.UUID
    job_type: str
    status: str
    reviews_seen: int
    reviews_inserted: int
    reviews_updated: int
    pages_processed: int
    cursor: str | None = None
    watermark_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
