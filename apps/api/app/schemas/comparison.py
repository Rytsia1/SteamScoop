"""Schemas for bounded game comparison requests and responses."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, Field, field_validator


class ComparisonPeriod(BaseModel):
    """Optional date window filter for game comparison."""

    model_config = {"populate_by_name": True}

    from_date: date | None = Field(
        default=None,
        validation_alias="from",
        serialization_alias="from",
    )
    to_date: date | None = Field(
        default=None,
        validation_alias="to",
        serialization_alias="to",
    )


ALLOWED_COMPARISON_METRICS = {
    "review_volume",
    "steam_recommendation",
    "model_sentiment",
    "aspect_sentiment",
}


class ComparisonRequest(BaseModel):
    """Payload for POST /comparisons."""

    game_ids: list[uuid.UUID] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="List of 2 to 5 unique game IDs to compare",
    )
    period: ComparisonPeriod | None = None
    metrics: list[str] = Field(
        default_factory=lambda: [
            "review_volume",
            "steam_recommendation",
            "model_sentiment",
            "aspect_sentiment",
        ],
        description="Allowlisted metrics to include in comparison",
    )
    model_version: str = Field(default="baseline", description="Published model version key")

    @field_validator("game_ids")
    @classmethod
    def validate_unique_game_ids(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(v) != len(set(v)):
            raise ValueError("game_ids must contain unique game IDs.")
        return v

    @field_validator("metrics")
    @classmethod
    def validate_allowed_metrics(cls, v: list[str]) -> list[str]:
        invalid = [m for m in v if m not in ALLOWED_COMPARISON_METRICS]
        if invalid:
            allowed = sorted(ALLOWED_COMPARISON_METRICS)
            raise ValueError(f"Invalid metric keys: {invalid}. Allowed metrics are: {allowed}")
        return v


class GameComparisonResult(BaseModel):
    """Metric values for a single game in comparison response."""

    game_id: uuid.UUID
    name: str
    review_volume: int | None = None
    steam_recommendation_rate: float | None = None
    model_positive_rate: float | None = None
    sentiment_score: float | None = None
    aspect_sentiment: dict[str, float] | None = None


class ComparisonResponseData(BaseModel):
    """Response payload for POST /comparisons."""

    games: list[GameComparisonResult]
    period: ComparisonPeriod | None = None
    model_version: str
