import json
import logging
from collections.abc import Iterator
from typing import Any

from app.integrations.steam.models import (
    NormalizedGameMetadata,
    ReviewPage,
)
from app.integrations.steam.normalizer import (
    parse_app_reviews_response,
    parse_store_appdetails_response,
)
from app.integrations.steam.schemas import SteamReviewRequestParams
from app.integrations.steam.transport import SteamTransport

logger = logging.getLogger("steamscoop.integrations.steam.client")

# Official canonical Steam API base endpoints
DEFAULT_REVIEWS_URL = "https://api.steampowered.com/IUserReviewsService/GetAppReviews/v1/"
DEFAULT_STORE_APPDETAILS_URL = "https://store.steampowered.com/api/appdetails"


class SteamClient:
    """High-level client providing isolated access to Steam review and store APIs.

    Orchestrates the HTTP transport, request serialization, and response normalization.
    """

    def __init__(
        self,
        transport: SteamTransport | None = None,
        reviews_url: str = DEFAULT_REVIEWS_URL,
        store_appdetails_url: str = DEFAULT_STORE_APPDETAILS_URL,
    ) -> None:
        self.transport = transport or SteamTransport()
        self.reviews_url = reviews_url
        self.store_appdetails_url = store_appdetails_url

    def close(self) -> None:
        """Close underlying transport connections."""
        self.transport.close()

    def __enter__(self) -> "SteamClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get_game_metadata(
        self, steam_app_id: int, language: str = "english"
    ) -> NormalizedGameMetadata:
        """Fetch and normalize public game metadata from Steam Store appdetails.

        Raises SteamGameUnavailableError if the app does not exist or was delisted.
        """
        logger.info("Fetching Steam Store metadata for App ID: %d", steam_app_id)
        params = {
            "appids": str(steam_app_id),
            "l": language,
            "cc": "us",
        }
        data = self.transport.get_json(self.store_appdetails_url, params=params)
        return parse_store_appdetails_response(data, steam_app_id)

    def get_app_reviews(self, params: SteamReviewRequestParams) -> ReviewPage:
        """Fetch and normalize a single page of user reviews using GetAppReviews/v1.

        Uses the documented input_json parameter format.
        """
        logger.debug(
            "Requesting reviews for App ID %d [filter=%d, cursor=%s]",
            params.appid,
            params.filter,
            params.cursor,
        )
        input_dict = params.to_input_json()
        query_params = {
            "input_json": json.dumps(input_dict),
        }
        data = self.transport.get_json(
            self.reviews_url,
            params=query_params,
            include_api_key=True,
        )
        return parse_app_reviews_response(
            payload=data,
            app_id=params.appid,
            current_cursor=params.cursor,
        )

    def iterate_recent_reviews(
        self,
        steam_app_id: int,
        max_pages: int = 10,
        num_per_page: int = 100,
        languages: list[str] | None = None,
        date_range_start: int | None = None,
        date_range_end: int | None = None,
    ) -> Iterator[ReviewPage]:
        """Generator yielding consecutive ReviewPages for historical traversal (filter=1: Recent).

        Terminates cleanly when Steam returns no more reviews, repeats cursor, or reaches max_pages.
        """
        cursor = "*"
        pages_fetched = 0

        while pages_fetched < max_pages:
            params = SteamReviewRequestParams(
                appid=steam_app_id,
                filter=1,  # Recent reviews for historical traversal
                languages=languages or ["all"],
                num_per_page=num_per_page,
                cursor=cursor,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
            )
            page = self.get_app_reviews(params)
            pages_fetched += 1
            yield page

            if not page.has_more or not page.cursor or page.cursor == cursor:
                logger.info(
                    "Completed review pagination for App ID %d after %d pages.",
                    steam_app_id,
                    pages_fetched,
                )
                break

            cursor = page.cursor

    def iterate_updated_reviews(
        self,
        steam_app_id: int,
        cursor: str = "*",
        max_pages: int = 5,
        num_per_page: int = 100,
        languages: list[str] | None = None,
    ) -> Iterator[ReviewPage]:
        """Generator yielding ReviewPages for incremental synchronization (filter=2: Updated)."""
        current_cursor = cursor
        pages_fetched = 0

        while pages_fetched < max_pages:
            params = SteamReviewRequestParams(
                appid=steam_app_id,
                filter=2,  # Updated reviews for incremental synchronization
                languages=languages or ["all"],
                num_per_page=num_per_page,
                cursor=current_cursor,
            )
            page = self.get_app_reviews(params)
            pages_fetched += 1
            yield page

            if (
                not page.has_more
                or not page.cursor
                or page.cursor == current_cursor
            ):
                break

            current_cursor = page.cursor

