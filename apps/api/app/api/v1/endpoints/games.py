import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_game_service, get_request_id, get_review_service
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.schemas.game import (
    GameDetail,
    GameListItem,
    GameOverviewData,
    GameQueryParams,
    GameSortOption,
)
from app.schemas.review import ReviewListItem, ReviewQueryParams
from app.services.game_service import GameService
from app.services.review_service import ReviewService

router = APIRouter()


@router.get(
    "/games",
    response_model=ResponseEnvelope[list[GameListItem]],
    summary="Search and List Indexed Games",
    description=(
        "Search the indexed Steam game catalog with optional genre filtering, "
        "sorting, and keyset cursor pagination."
    ),
)
async def list_games(
    q: str | None = Query(
        default=None, max_length=100, description="Search term matching game name"
    ),
    genre: str | None = Query(default=None, max_length=50, description="Exact genre filter"),
    catalog_status: Literal["indexed", "pending"] = Query(
        default="indexed", description="Catalog status (ignored when upcoming=true)"
    ),
    is_free: bool | None = Query(default=None, description="Free-to-play filter"),
    year_from: int | None = Query(
        default=None, ge=1970, le=2100, description="Released on or after this year"
    ),
    year_to: int | None = Query(
        default=None, ge=1970, le=2100, description="Released on or before this year"
    ),
    upcoming: bool = Query(default=False, description="Only games with a future release date"),
    sort: GameSortOption = Query(default="name_asc", description="Sort ordering"),
    limit: int = Query(default=20, ge=1, le=100, description="Page limit"),
    cursor: str | None = Query(default=None, description="Opaque pagination cursor token"),
    game_service: GameService = Depends(get_game_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[GameListItem]]:
    params = GameQueryParams(
        q=q,
        genre=genre,
        catalog_status=catalog_status,
        is_free=is_free,
        year_from=year_from,
        year_to=year_to,
        upcoming=upcoming,
        sort=sort,
        limit=limit,
        cursor=cursor,
    )
    items, pagination = game_service.search_games(params)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[GameListItem]](
        data=items,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
            pagination=pagination,
        ),
    )


@router.get(
    "/games/genres",
    response_model=ResponseEnvelope[list[str]],
    summary="List Catalog Genres",
    description="Distinct genre labels across publicly indexed games, sorted alphabetically.",
)
async def list_game_genres(
    game_service: GameService = Depends(get_game_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[str]]:
    return ResponseEnvelope[list[str]](
        data=game_service.list_genres(),
        error=None,
        meta=MetaEnvelope(request_id=request_id, timestamp=datetime.now(UTC).isoformat()),
    )


@router.get(
    "/games/{game_id}",
    response_model=ResponseEnvelope[GameDetail],
    summary="Get Game Details by ID",
    description=(
        "Retrieve complete public metadata and review data coverage for an "
        "indexed game by internal UUID."
    ),
)
async def get_game(
    game_id: uuid.UUID = Path(..., description="Unique internal game UUID"),
    game_service: GameService = Depends(get_game_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[GameDetail]:
    game = game_service.get_game_by_id(game_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[GameDetail](
        data=game,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/games/{game_id}/overview",
    response_model=ResponseEnvelope[GameOverviewData],
    summary="Get Game Overview Summary",
    description=(
        "Retrieve unified game overview combining game metadata, Steam recommendation rates, "
        "ML sentiment summary, and analytical review coverage."
    ),
)
async def get_game_overview(
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    game_service: GameService = Depends(get_game_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[GameOverviewData]:
    overview = game_service.get_game_overview(game_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[GameOverviewData](
        data=overview,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/games/by-steam-id/{steam_app_id}",
    response_model=ResponseEnvelope[GameDetail],
    summary="Get Game Details by Steam App ID",
    description="Retrieve public metadata and review coverage using official Steam application ID.",
)
async def get_game_by_steam_app_id(
    steam_app_id: int = Path(..., gt=0, description="Official Steam Application ID"),
    game_service: GameService = Depends(get_game_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[GameDetail]:
    game = game_service.get_game_by_steam_app_id(steam_app_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[GameDetail](
        data=game,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/games/{game_id}/reviews",
    response_model=ResponseEnvelope[list[ReviewListItem]],
    summary="Explore Game Reviews",
    description=(
        "Paginated explorer for game reviews with sentiment classification, "
        "language filter, and recommendation filter."
    ),
)
async def list_game_reviews(
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    limit: int = Query(default=20, ge=1, le=100, description="Page limit"),
    cursor: str | None = Query(default=None, description="Opaque pagination cursor token"),
    language: str | None = Query(default=None, max_length=16, description="Review language code"),
    steam_recommended: bool | None = Query(
        default=None, description="Steam user recommendation flag (voted_up)"
    ),
    sentiment: Literal["positive", "negative", "neutral"] | None = Query(
        default=None, description="ML sentiment classification label"
    ),
    sort: Literal["created_at_desc", "created_at_asc", "votes_up_desc"] = Query(
        default="created_at_desc", description="Sort ordering"
    ),
    review_service: ReviewService = Depends(get_review_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[ReviewListItem]]:
    params = ReviewQueryParams(
        limit=limit,
        cursor=cursor,
        language=language,
        steam_recommended=steam_recommended,
        sentiment=sentiment,
        sort=sort,
    )
    items, pagination = review_service.get_game_reviews(game_id, params)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[ReviewListItem]](
        data=items,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
            pagination=pagination,
        ),
    )
