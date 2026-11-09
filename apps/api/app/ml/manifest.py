from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SplitSummary(BaseModel):
    """Statistical summary for a single dataset partition (train, val, or test)."""

    model_config = ConfigDict(frozen=True)

    split_name: str
    sample_count: int = Field(ge=0)
    group_count: int = Field(ge=0, description="Unique duplicate/cluster groups in partition")
    sha256_hash: str = Field(description="SHA-256 checksum of split artifact")
    label_distribution: dict[str, int] = Field(default_factory=dict)
    aspect_distribution: dict[str, int] = Field(default_factory=dict)
    language_distribution: dict[str, int] = Field(default_factory=dict)
    length_statistics: dict[str, float] = Field(
        default_factory=dict,
        description="Character and word count percentiles (p10, p50, p90, mean)",
    )


class DatasetManifest(BaseModel):
    """Reproducible, immutable dataset manifest complying with ML_SPECIFICATION.md Section 13.1."""

    model_config = ConfigDict(frozen=True)

    dataset_id: str = Field(
        description="Unique dataset identifier (e.g. steamscoop-sentiment-benchmark)"
    )
    version: str = Field(description="Semantic version string (e.g. v1.0.0)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    description: str = Field(description="Detailed description of dataset purpose and scope")
    splits: dict[str, SplitSummary] = Field(
        description="Summaries of train, validation, and test partitions",
    )
    total_reviews: int = Field(ge=0)
    total_unique_groups: int = Field(ge=0)
    duplicate_rate: float = Field(ge=0.0, le=1.0)
    preprocessing_version: str
    quality_engine_version: str
    deduplication_version: str
    random_seed: int
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Lineage tracking: source game app IDs, date range, collection parameters",
    )
    licensing: dict[str, str] = Field(
        default_factory=lambda: {
            "source": "Steam Community public user reviews (Valve Corporation)",
            "license": "Publicly accessible player feedback collected via Steam API",
            "privacy_notice": (
                "Strictly excludes all SteamIDs, profile URLs, avatars, "
                "and player personal identification."
            ),
            "usage": "Internal benchmarking, model training, and analytical trend estimation.",
        }
    )
