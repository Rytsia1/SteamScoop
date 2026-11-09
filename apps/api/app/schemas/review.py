import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SentimentSummary(BaseModel):
    """Normalized sentiment prediction attached to a review."""

    label: str = Field(description="Sentiment classification: positive, negative, or neutral")
    confidence: float | None = Field(default=None, description="Confidence score in [0, 1]")
    model_version: str = Field(description="Model version key that produced the prediction")


class ReviewListItem(BaseModel):
    """Review item in a paginated game review list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    steam_review_id: int
    review_text: str
    language: str
    voted_up: bool = Field(description="Steam player recommendation: True if recommended")
    votes_up: int = Field(description="Helpful votes count")
    votes_funny: int = Field(description="Funny votes count")
    weighted_vote_score: Decimal | None = None
    comment_count: int
    steam_playtime_forever: int | None = Field(
        default=None, description="Total playtime in minutes"
    )
    steam_created_at: datetime | None = None
    sentiment: SentimentSummary | None = None


class ReviewDetail(BaseModel):
    """Detailed review record approved for public display."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    game_id: uuid.UUID
    steam_review_id: int
    review_text: str
    language: str
    voted_up: bool
    votes_up: int
    votes_funny: int
    weighted_vote_score: Decimal | None = None
    comment_count: int
    steam_playtime_at_review: int | None = None
    steam_playtime_forever: int | None = None
    steam_playtime_last_two_weeks: int | None = None
    steam_purchase: bool | None = None
    received_for_free: bool | None = None
    written_during_early_access: bool | None = None
    steam_created_at: datetime | None = None
    steam_updated_at: datetime | None = None
    first_collected_at: datetime
    last_seen_at: datetime
    sentiment: SentimentSummary | None = None


class ReviewQueryParams(BaseModel):
    """Validated query parameters for review browsing and filtering."""

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum reviews per page",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque keyset cursor token",
    )
    language: str | None = Field(
        default=None,
        max_length=16,
        description="Review language filter (e.g. 'en', 'schinese')",
    )
    steam_recommended: bool | None = Field(
        default=None,
        description="Filter by Steam recommendation flag (voted_up)",
    )
    sentiment: Literal["positive", "negative", "neutral"] | None = Field(
        default=None,
        description="Filter by ML sentiment classification label",
    )
    sort: Literal["created_at_desc", "created_at_asc", "votes_up_desc"] = Field(
        default="created_at_desc",
        description="Sort ordering",
    )
