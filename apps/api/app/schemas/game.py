import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GameListItem(BaseModel):
    """Compact summary of a game for catalog listing and search results."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    steam_app_id: int
    name: str
    header_image_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    release_date: date | None = None
    catalog_status: str
    is_active: bool


class GameDataCoverage(BaseModel):
    """Collection and dataset coverage metadata for a game."""

    latest_collection_at: datetime | None = None
    stored_reviews_count: int = 0
    language_scope: list[str] = Field(default_factory=lambda: ["all"])


class GameDetail(BaseModel):
    """Complete public game profile and coverage details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    steam_app_id: int
    name: str
    short_description: str | None = None
    header_image_url: str | None = None
    website_url: str | None = None
    developers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    release_date: date | None = None
    is_free: bool | None = None
    catalog_status: str
    is_active: bool
    data_coverage: GameDataCoverage = Field(default_factory=GameDataCoverage)
    created_at: datetime
    updated_at: datetime


class SteamRecommendationSummary(BaseModel):
    """Steam user recommendation statistics."""

    recommended_count: int = Field(ge=0)
    not_recommended_count: int = Field(ge=0)
    positive_rate: float = Field(ge=0.0, le=1.0)


class ModelSentimentSummary(BaseModel):
    """Model-inferred sentiment distribution for the game."""

    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)
    unclassified_count: int = Field(ge=0)
    positive_rate: float = Field(ge=0.0, le=1.0)
    model_version: str


class CoverageSummary(BaseModel):
    """Data collection coverage metadata."""

    collected_at: datetime | None = None
    sampled: bool = True
    language_scope: list[str] = Field(default_factory=lambda: ["all"])
    collection_policy: str = "weekly_hybrid_sample"


class GameOverviewData(BaseModel):
    """Main summary card and collection coverage for GET /games/{game_id}/overview."""

    game_id: uuid.UUID
    review_count: int = Field(ge=0)
    steam_recommendation: SteamRecommendationSummary
    model_sentiment: ModelSentimentSummary
    coverage: CoverageSummary


class GameQueryParams(BaseModel):
    """Validated query parameters for game search and listing."""

    q: str | None = Field(
        default=None,
        max_length=100,
        description="Search substring to match against game name",
    )
    genre: str | None = Field(
        default=None,
        max_length=50,
        description="Genre label filter",
    )
    catalog_status: str | None = Field(
        default="indexed",
        description="Catalog status filter",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Page limit (1 to 100)",
    )
    cursor: str | None = Field(
        default=None,
        description="Opaque base64 cursor token",
    )
    sort: Literal["name_asc", "name_desc", "recently_updated"] = Field(
        default="name_asc",
        description="Sort ordering",
    )
