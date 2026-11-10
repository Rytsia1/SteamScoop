"""Pydantic schemas for game analytics, sentiment distributions, aspects, and topics."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalyticsPoint(BaseModel):
    """Discrete time-series bucket point representing aggregated game reception."""

    model_config = ConfigDict(from_attributes=True)

    period_start: date = Field(description="Inclusive start date of aggregation bucket")
    period_end: date = Field(description="Exclusive end date of aggregation bucket")
    review_count: int = Field(ge=0, description="Total reviews in bucket")
    positive_count: int = Field(ge=0, description="Model-classified positive reviews")
    negative_count: int = Field(ge=0, description="Model-classified negative reviews")
    neutral_count: int = Field(ge=0, description="Model-classified neutral reviews")
    steam_recommended_count: int = Field(
        ge=0, description="Steam user positive recommendations (voted_up = True)"
    )
    steam_not_recommended_count: int = Field(
        ge=0, description="Steam user negative recommendations (voted_up = False)"
    )
    sentiment_score: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Normalized net sentiment score on [-1.0, 1.0]",
    )


class GameAnalyticsData(BaseModel):
    """Time-series response payload for GET /games/{game_id}/analytics."""

    game_id: uuid.UUID
    period: Literal["day", "week", "month"]
    model_version: str
    points: list[AnalyticsPoint]


class SentimentDistributionData(BaseModel):
    """Sentiment distribution response payload for GET /games/{game_id}/sentiment."""

    game_id: uuid.UUID
    model_version: str
    total_reviews: int = Field(ge=0, description="Total eligible reviews analyzed")
    classified_count: int = Field(
        ge=0, description="Reviews classified by sentiment (pos + neg + neu)"
    )
    unclassified_count: int = Field(
        ge=0, description="Unclassified / abstained / missing predictions"
    )
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)
    positive_rate: float = Field(ge=0.0, le=1.0, description="positive / classified_count")
    negative_rate: float = Field(ge=0.0, le=1.0, description="negative / classified_count")
    neutral_rate: float = Field(ge=0.0, le=1.0, description="neutral / classified_count")
    coverage_rate: float = Field(ge=0.0, le=1.0, description="classified_count / total_reviews")
    unclassified_rate: float = Field(
        ge=0.0, le=1.0, description="unclassified_count / total_reviews"
    )
    sentiment_score: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="(positive - negative) / classified_count",
    )
    timeline: list[AnalyticsPoint] | None = None


class AspectSummaryPoint(BaseModel):
    """Summary metrics for a discrete aspect discussed in player reviews."""

    aspect_key: str
    display_name: str
    mention_count: int = Field(ge=0, description="Total aspect mentions")
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)
    positive_rate: float = Field(ge=0.0, le=1.0, description="positive / mention_count")
    negative_rate: float = Field(ge=0.0, le=1.0, description="negative / mention_count")
    neutral_rate: float = Field(ge=0.0, le=1.0, description="neutral / mention_count")
    sentiment_score: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="(positive - negative) / mention_count",
    )
    prevalence: float = Field(ge=0.0, le=1.0, description="mention_count / total_reviews")


class GameAspectsData(BaseModel):
    """Aspect-based sentiment analysis response for GET /games/{game_id}/aspects."""

    game_id: uuid.UUID
    taxonomy_version: str
    model_version: str
    aspects: list[AspectSummaryPoint]
    total_aspect_mentions: int = Field(ge=0)
    unique_reviews_with_aspects: int = Field(ge=0)


class TopicSummaryPoint(BaseModel):
    """Discovered topic summary with prevalence and top terms."""

    topic_key: str
    label: str
    review_count: int = Field(ge=0, description="Primary assignments count")
    prevalence: float = Field(ge=0.0, le=1.0, description="review_count / total_assigned_reviews")
    avg_score: float = Field(ge=0.0, le=1.0, description="Mean topic assignment score")
    is_outlier: bool
    keywords: list[str] = Field(default_factory=list)


class GameTopicsData(BaseModel):
    """Topic model summary response for GET /games/{game_id}/topics."""

    game_id: uuid.UUID
    model_version: str
    topics: list[TopicSummaryPoint]
    total_assigned_reviews: int = Field(ge=0)
    outlier_count: int = Field(ge=0)
    outlier_rate: float = Field(ge=0.0, le=1.0)
