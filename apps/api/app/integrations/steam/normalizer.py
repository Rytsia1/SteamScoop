import logging
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError

from app.integrations.steam.exceptions import (
    SteamGameUnavailableError,
    SteamMalformedResponseError,
)
from app.integrations.steam.models import (
    NormalizedGameMetadata,
    NormalizedReview,
    ReviewPage,
)
from app.integrations.steam.schemas import (
    SteamGetAppReviewsEnvelopeSchema,
    SteamStoreAppDetailsItemSchema,
)

logger = logging.getLogger("steamscoop.integrations.steam.normalizer")

# Recognized date formatting patterns across Steam regional responses
_DATE_FORMATS = [
    "%d %b, %Y",  # 17 Sep, 2020
    "%b %d, %Y",  # Sep 17, 2020
    "%d %b %Y",  # 17 Sep 2020
    "%d %B, %Y",  # 17 September, 2020
    "%B %d, %Y",  # September 17, 2020
    "%Y-%m-%d",  # 2020-09-17
]


def parse_steam_release_date(date_str: str) -> date | None:
    """Safely parse a human-readable Steam store release date string."""
    cleaned = date_str.strip()
    if not cleaned or "coming" in cleaned.lower() or "tba" in cleaned.lower():
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    # Fallback: Month Year format e.g. "September 2020" or "Sep 2020"
    for fmt in ["%B %Y", "%b %Y"]:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return date(dt.year, dt.month, 1)
        except ValueError:
            continue

    logger.debug("Could not parse Steam release date string: %r", date_str)
    return None


def parse_app_reviews_response(
    payload: dict[str, Any],
    app_id: int,
    current_cursor: str | None = None,
) -> ReviewPage:
    """Parse and normalize Steam GetAppReviews response envelope.

    Ensures author PII is completely excluded and all numeric types are strictly bounded.
    """
    try:
        envelope = SteamGetAppReviewsEnvelopeSchema.model_validate(payload)
    except ValidationError as val_err:
        raise SteamMalformedResponseError(
            message="GetAppReviews response failed schema validation.",
            details=val_err.errors(),
        ) from val_err

    resp = envelope.response

    # success: 1 indicates normal success; success: 2 often indicates no data or non-existent app
    if resp.success != 1 and not resp.reviews:
        if resp.query_summary.total_reviews == 0:
            return ReviewPage(
                reviews=[],
                cursor=None,
                has_more=False,
                total_reviews_in_query=0,
                query_summary=resp.query_summary.model_dump(),
            )
        raise SteamGameUnavailableError(
            steam_app_id=app_id,
            message=(
                f"Steam API returned success={resp.success} with no reviews for App ID {app_id}."
            ),
        )

    normalized_reviews: list[NormalizedReview] = []
    for raw in resp.reviews:
        # Validate recommendation id
        try:
            review_id = int(raw.recommendationid)
        except (ValueError, TypeError):
            logger.warning(
                "Skipping review with non-numeric recommendationid: %r", raw.recommendationid
            )
            continue

        if review_id <= 0:
            continue

        # Review text: enforce non-empty content
        text = raw.review.strip() if raw.review else ""
        if not text:
            # Skip reviews without content to preserve database integrity
            continue

        # Weighted vote score decimal normalization
        score: Decimal | None = None
        if raw.weighted_vote_score is not None:
            try:
                score_candidate = Decimal(str(raw.weighted_vote_score))
                if score_candidate >= 0:
                    score = score_candidate
            except (InvalidOperation, TypeError):
                score = None

        # Playtime sanitization
        author = raw.author
        playtime_rev = (
            author.playtime_at_review
            if author.playtime_at_review is not None and author.playtime_at_review >= 0
            else None
        )
        playtime_all = (
            author.playtime_forever
            if author.playtime_forever is not None and author.playtime_forever >= 0
            else None
        )
        playtime_2w = (
            author.playtime_last_two_weeks
            if author.playtime_last_two_weeks is not None and author.playtime_last_two_weeks >= 0
            else None
        )

        # Timestamps
        created_at = (
            datetime.fromtimestamp(raw.timestamp_created, tz=UTC)
            if raw.timestamp_created and raw.timestamp_created > 0
            else None
        )
        updated_at = (
            datetime.fromtimestamp(raw.timestamp_updated, tz=UTC)
            if raw.timestamp_updated and raw.timestamp_updated > 0
            else None
        )

        normalized_reviews.append(
            NormalizedReview(
                steam_review_id=review_id,
                language=raw.language or "unknown",
                review_text=text,
                voted_up=bool(raw.voted_up),
                votes_up=max(0, int(raw.votes_up or 0)),
                votes_funny=max(0, int(raw.votes_funny or 0)),
                weighted_vote_score=score,
                comment_count=max(0, int(raw.comment_count or 0)),
                steam_playtime_at_review=playtime_rev,
                steam_playtime_forever=playtime_all,
                steam_playtime_last_two_weeks=playtime_2w,
                steam_purchase=raw.steam_purchase,
                received_for_free=raw.received_for_free,
                written_during_early_access=raw.written_during_early_access,
                steam_created_at=created_at,
                steam_updated_at=updated_at,
            )
        )

    # Determine pagination termination
    raw_next_cursor = (resp.cursor or "").strip()
    next_cursor = raw_next_cursor if raw_next_cursor and raw_next_cursor != "*" else None

    # Steam loops or repeats the identical cursor when terminal page is reached
    has_more = (
        len(normalized_reviews) > 0 and next_cursor is not None and next_cursor != current_cursor
    )

    return ReviewPage(
        reviews=normalized_reviews,
        cursor=next_cursor,
        has_more=has_more,
        total_reviews_in_query=resp.query_summary.total_reviews or 0,
        query_summary=resp.query_summary.model_dump(),
    )


def parse_store_appdetails_response(payload: dict[str, Any], app_id: int) -> NormalizedGameMetadata:
    """Parse and normalize Steam Store appdetails response for a single App ID."""
    app_key = str(app_id)
    if app_key not in payload:
        raise SteamGameUnavailableError(
            steam_app_id=app_id,
            message=f"Steam Store appdetails payload does not contain App ID {app_id}.",
        )

    app_payload = payload[app_key]
    try:
        item = SteamStoreAppDetailsItemSchema.model_validate(app_payload)
    except ValidationError as val_err:
        raise SteamMalformedResponseError(
            message=f"Store appdetails for App ID {app_id} failed schema validation.",
            details=val_err.errors(),
        ) from val_err

    if not item.success or item.data is None:
        raise SteamGameUnavailableError(
            steam_app_id=app_id,
            message=f"Game {app_id} is unavailable or delisted on Steam Store (success=false).",
        )

    data = item.data
    name = data.name.strip()
    if not name:
        raise SteamMalformedResponseError(f"Game {app_id} returned empty name in metadata.")

    # Deduplicate and clean genres & categories
    genres = [g.description.strip() for g in data.genres if g.description and g.description.strip()]
    categories = [
        c.description.strip() for c in data.categories if c.description and c.description.strip()
    ]
    developers = [d.strip() for d in data.developers if d.strip()]
    publishers = [p.strip() for p in data.publishers if p.strip()]

    release_date = parse_steam_release_date(data.release_date.date) if data.release_date else None

    return NormalizedGameMetadata(
        steam_app_id=data.steam_appid or app_id,
        name=name,
        short_description=data.short_description.strip() if data.short_description else None,
        header_image_url=data.header_image.strip() if data.header_image else None,
        website_url=data.website.strip() if data.website else None,
        developers=developers,
        publishers=publishers,
        genres=genres,
        categories=categories,
        release_date=release_date,
        is_free=data.is_free,
    )
