from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ==========================================
# Steam Reviews API Schemas
# ==========================================


class SteamReviewRequestParams(BaseModel):
    """Parameters for Steam's IUserReviewsService/GetAppReviews/v1 endpoint."""

    model_config = ConfigDict(extra="forbid")

    appid: int = Field(gt=0, description="Steam Application ID")
    filter: int = Field(
        default=1,
        description="Filter type: 1 = Recent (historical), 2 = Updated (incremental)",
    )
    languages: list[str] = Field(
        default_factory=lambda: ["all"],
        description="List of language codes or ['all']",
    )
    review_type: int = Field(
        default=0,
        description="Review type: 0 = all, 1 = positive, 2 = negative",
    )
    purchase_type: int = Field(
        default=1,
        description="Purchase type: 0 = all, 1 = steam purchase",
    )
    num_per_page: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Batch size per page (maximum 100)",
    )
    cursor: str = Field(
        default="*",
        description="Continuation cursor token returned by previous page; initial is '*'",
    )
    date_range_start: int | None = Field(
        default=None,
        description="Optional Unix epoch timestamp for start boundary",
    )
    date_range_end: int | None = Field(
        default=None,
        description="Optional Unix epoch timestamp for end boundary",
    )

    def to_input_json(self) -> dict[str, Any]:
        """Convert to the canonical dictionary for Steam's input_json parameter."""
        payload: dict[str, Any] = {
            "appid": self.appid,
            "filter": self.filter,
            "languages": self.languages,
            "review_type": self.review_type,
            "purchase_type": self.purchase_type,
            "num_per_page": self.num_per_page,
            "cursor": self.cursor,
        }
        if self.date_range_start is not None and self.date_range_end is not None:
            payload["date_range_start"] = self.date_range_start
            payload["date_range_end"] = self.date_range_end
        return payload


class SteamAuthorSchema(BaseModel):
    """Raw author object in a Steam review (scrubbed of PII during normalization)."""

    model_config = ConfigDict(extra="ignore")

    steamid: str | None = None
    num_games_owned: int | None = None
    num_reviews: int | None = None
    playtime_forever: int | None = None
    playtime_last_two_weeks: int | None = None
    playtime_at_review: int | None = None
    last_played: int | None = None


class SteamRawReviewSchema(BaseModel):
    """Individual review record returned in Steam's GetAppReviews payload."""

    model_config = ConfigDict(extra="ignore")

    recommendationid: str | int = Field(description="Steam's unique review recommendation ID")
    author: SteamAuthorSchema = Field(default_factory=SteamAuthorSchema)
    language: str = "unknown"
    review: str = ""
    timestamp_created: int | None = None
    timestamp_updated: int | None = None
    voted_up: bool = True
    votes_up: int = 0
    votes_funny: int = 0
    weighted_vote_score: Decimal | float | str | None = None
    comment_count: int = 0
    steam_purchase: bool | None = None
    received_for_free: bool | None = None
    written_during_early_access: bool | None = None
    primarily_steam_deck: bool | None = None


class SteamQuerySummarySchema(BaseModel):
    """Summary statistics returned in the GetAppReviews response envelope."""

    model_config = ConfigDict(extra="ignore")

    num_reviews: int = 0
    review_score: int | None = None
    review_score_desc: str | None = None
    total_positive: int | None = None
    total_negative: int | None = None
    total_reviews: int | None = None


class SteamGetAppReviewsResponseSchema(BaseModel):
    """Inner response object of GetAppReviews."""

    model_config = ConfigDict(extra="ignore")

    reviews: list[SteamRawReviewSchema] = Field(default_factory=list)
    cursor: str | None = None
    query_summary: SteamQuerySummarySchema = Field(default_factory=SteamQuerySummarySchema)
    success: int = 1


class SteamGetAppReviewsEnvelopeSchema(BaseModel):
    """Outer wire response envelope from Steam Web API."""

    model_config = ConfigDict(extra="ignore")

    response: SteamGetAppReviewsResponseSchema


# ==========================================
# Steam Store Metadata Schemas (appdetails)
# ==========================================


class SteamStoreReleaseDateSchema(BaseModel):
    """Release date metadata in Store appdetails response."""

    model_config = ConfigDict(extra="ignore")

    coming_soon: bool = False
    date: str = ""


class SteamStoreGenreSchema(BaseModel):
    """Genre description entry."""

    model_config = ConfigDict(extra="ignore")

    id: str | int = ""
    description: str = ""


class SteamStoreCategorySchema(BaseModel):
    """Category description entry."""

    model_config = ConfigDict(extra="ignore")

    id: int | str = 0
    description: str = ""


class SteamStoreAppDetailsDataSchema(BaseModel):
    """Game metadata content from Store appdetails."""

    model_config = ConfigDict(extra="ignore")

    type: str | None = None
    name: str = ""
    steam_appid: int
    is_free: bool = False
    short_description: str | None = None
    header_image: str | None = None
    website: str | None = None
    developers: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    genres: list[SteamStoreGenreSchema] = Field(default_factory=list)
    categories: list[SteamStoreCategorySchema] = Field(default_factory=list)
    release_date: SteamStoreReleaseDateSchema = Field(default_factory=SteamStoreReleaseDateSchema)


class SteamStoreAppDetailsItemSchema(BaseModel):
    """Top-level item for each requested app ID in Store appdetails."""

    model_config = ConfigDict(extra="ignore")

    success: bool = False
    data: SteamStoreAppDetailsDataSchema | None = None
