"""Public API endpoints for game analytics, sentiment trends, aspects, and topics."""

import uuid
from datetime import UTC, date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_analytics_service, get_request_id
from app.schemas.analytics import (
    GameAnalyticsData,
    GameAspectsData,
    GameTopicsData,
    SentimentDistributionData,
)
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get(
    "/games/{game_id}/analytics",
    response_model=ResponseEnvelope[GameAnalyticsData],
    summary="Get Time-Bucketed Game Analytics",
    description=(
        "Returns precomputed, version-aware time-series analytics points for a game. "
        "Allows period selection by day, week, or month, and filtering by date range."
    ),
)
async def get_game_analytics(
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    period: Literal["day", "week", "month"] = Query(
        default="week", description="Time aggregation interval"
    ),
    from_date: date | None = Query(
        default=None, alias="from", description="Inclusive start date (YYYY-MM-DD)"
    ),
    to_date: date | None = Query(
        default=None, alias="to", description="Exclusive end date (YYYY-MM-DD)"
    ),
    model_version: str = Query(
        default="baseline", description="Published model/selection version key"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[GameAnalyticsData]:
    data = analytics_service.get_game_analytics(
        game_id=game_id,
        period_type=period,
        from_date=from_date,
        to_date=to_date,
        model_version_key=model_version,
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[GameAnalyticsData](
        data=data,
        error=None,
        meta=MetaEnvelope(request_id=request_id, timestamp=now_utc),
    )


@router.get(
    "/games/{game_id}/sentiment",
    response_model=ResponseEnvelope[SentimentDistributionData],
    summary="Get Sentiment Distribution and Breakdown",
    description=(
        "Returns comprehensive sentiment distribution counts, rates, coverage, "
        "and normalized sentiment score with explicit denominators."
    ),
)
async def get_game_sentiment(
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    from_date: date | None = Query(
        default=None, alias="from", description="Inclusive start date (YYYY-MM-DD)"
    ),
    to_date: date | None = Query(
        default=None, alias="to", description="Exclusive end date (YYYY-MM-DD)"
    ),
    model_version: str = Query(
        default="baseline", description="Published model/selection version key"
    ),
    include_trend: bool = Query(
        default=False, description="Whether to include time-series trend points"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[SentimentDistributionData]:
    data = analytics_service.get_game_sentiment_distribution(
        game_id=game_id,
        from_date=from_date,
        to_date=to_date,
        model_version_key=model_version,
        include_trend=include_trend,
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[SentimentDistributionData](
        data=data,
        error=None,
        meta=MetaEnvelope(request_id=request_id, timestamp=now_utc),
    )


@router.get(
    "/games/{game_id}/aspects",
    response_model=ResponseEnvelope[GameAspectsData],
    summary="Get Aspect-Based Sentiment Analysis",
    description=(
        "Returns aspect mention volume and sentiment polarities across the controlled "
        "aspect taxonomy, sorted by mention volume or negative rate."
    ),
)
async def get_game_aspects(
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    from_date: date | None = Query(
        default=None, alias="from", description="Inclusive start date (YYYY-MM-DD)"
    ),
    to_date: date | None = Query(
        default=None, alias="to", description="Exclusive end date (YYYY-MM-DD)"
    ),
    model_version: str = Query(
        default="baseline", description="Published model/selection version key"
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max aspect items returned"),
    sort: Literal["mentions_desc", "negative_rate_desc", "positive_rate_desc"] = Query(
        default="mentions_desc", description="Aspect sort ordering"
    ),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[GameAspectsData]:
    data = analytics_service.get_game_aspects(
        game_id=game_id,
        from_date=from_date,
        to_date=to_date,
        model_version_key=model_version,
        limit=limit,
        sort=sort,
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[GameAspectsData](
        data=data,
        error=None,
        meta=MetaEnvelope(request_id=request_id, timestamp=now_utc),
    )


@router.get(
    "/games/{game_id}/topics",
    response_model=ResponseEnvelope[GameTopicsData],
    summary="Get Discovered Topics and Prevalence",
    description=(
        "Returns topic modeling summaries, representative terms, and review assignment "
        "prevalence for the game corpus."
    ),
)
async def get_game_topics(
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    model_version: str = Query(
        default="baseline", description="Published model/selection version key"
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Max topics returned"),
    include_outliers: bool = Query(default=False, description="Include outlier cluster in results"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[GameTopicsData]:
    data = analytics_service.get_game_topics(
        game_id=game_id,
        model_version_key=model_version,
        limit=limit,
        include_outliers=include_outliers,
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[GameTopicsData](
        data=data,
        error=None,
        meta=MetaEnvelope(request_id=request_id, timestamp=now_utc),
    )
