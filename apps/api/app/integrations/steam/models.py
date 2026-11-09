from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NormalizedReview(BaseModel):
    """Clean, privacy-compliant review entity ready for domain persistence.

    Author personal identification (SteamID, profile URL, avatar) is strictly omitted.
    """

    model_config = ConfigDict(frozen=True)

    steam_review_id: int = Field(gt=0, description="Unique Steam recommendation identifier")
    language: str = Field(description="ISO language code or Steam language identifier")
    review_text: str = Field(description="Untrusted player review text")
    voted_up: bool = Field(description="Steam player recommendation: True if recommended")
    votes_up: int = Field(ge=0, default=0, description="Helpful votes count")
    votes_funny: int = Field(ge=0, default=0, description="Funny votes count")
    weighted_vote_score: Decimal | None = Field(
        default=None, ge=0, description="Steam helpfulness weighted score"
    )
    comment_count: int = Field(ge=0, default=0, description="Total developer or player comments")
    steam_playtime_at_review: int | None = Field(
        default=None, ge=0, description="Playtime in minutes at review submission"
    )
    steam_playtime_forever: int | None = Field(
        default=None, ge=0, description="Total playtime in minutes recorded by Steam"
    )
    steam_playtime_last_two_weeks: int | None = Field(
        default=None, ge=0, description="Recent two-week playtime in minutes"
    )
    steam_purchase: bool | None = Field(
        default=None, description="True if game was purchased on Steam directly"
    )
    received_for_free: bool | None = Field(
        default=None, description="True if reviewer marked product was received for free"
    )
    written_during_early_access: bool | None = Field(
        default=None, description="True if review was submitted during Early Access"
    )
    steam_created_at: datetime | None = Field(
        default=None, description="Timezone-aware UTC timestamp when review was created"
    )
    steam_updated_at: datetime | None = Field(
        default=None, description="Timezone-aware UTC timestamp when review was last edited"
    )


class ReviewPage(BaseModel):
    """Normalized page of reviews returned from an ingestion traversal request."""

    model_config = ConfigDict(frozen=True)

    reviews: list[NormalizedReview] = Field(default_factory=list)
    cursor: str | None = Field(
        default=None, description="Continuation token for the next page"
    )
    has_more: bool = Field(
        default=False, description="True if additional pages are available to consume"
    )
    total_reviews_in_query: int = Field(
        default=0, ge=0, description="Number of reviews matched by Steam query filter"
    )
    query_summary: dict[str, Any] = Field(
        default_factory=dict, description="Diagnostic summary statistics from Steam"
    )


class NormalizedGameMetadata(BaseModel):
    """Clean, catalog-ready game metadata entity parsed from Steam Store."""

    model_config = ConfigDict(frozen=True)

    steam_app_id: int = Field(gt=0, description="Official Steam Application ID")
    name: str = Field(min_length=1, description="Official title of the game")
    short_description: str | None = Field(default=None, description="Short summary description")
    header_image_url: str | None = Field(
        default=None, description="Primary banner/header image URL"
    )
    website_url: str | None = Field(default=None, description="Official website or store link")
    developers: list[str] = Field(default_factory=list, description="Game development studios")
    publishers: list[str] = Field(default_factory=list, description="Publishing entities")
    genres: list[str] = Field(default_factory=list, description="Normalized genre taxonomy tags")
    categories: list[str] = Field(
        default_factory=list, description="Store categories (e.g. Single-player)"
    )
    release_date: date | None = Field(
        default=None, description="Parsed canonical commercial release date"
    )
    is_free: bool | None = Field(default=None, description="True if the game is Free-to-Play")
