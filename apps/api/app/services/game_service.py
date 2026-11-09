import uuid

from app.core.exceptions import GameNotFoundError
from app.repositories.game import GameRepository
from app.schemas.common import PaginationMeta
from app.schemas.game import GameDataCoverage, GameDetail, GameListItem, GameQueryParams


class GameService:
    """Domain service encapsulating catalog business logic and game discovery."""

    def __init__(self, game_repo: GameRepository) -> None:
        self.game_repo = game_repo

    def get_game_by_id(self, game_id: uuid.UUID) -> GameDetail:
        """Fetch complete public game details by internal UUID.

        Raises GameNotFoundError if the game does not exist or is inactive.
        """
        game = self.game_repo.get_active_game_by_id(game_id)
        if game is None:
            raise GameNotFoundError(str(game_id))

        latest_time, review_count, languages = self.game_repo.get_game_data_coverage(game_id)
        coverage = GameDataCoverage(
            latest_collection_at=latest_time,
            stored_reviews_count=review_count,
            language_scope=languages,
        )

        return GameDetail(
            id=game.id,
            steam_app_id=game.steam_app_id,
            name=game.name,
            short_description=game.short_description,
            header_image_url=game.header_image_url,
            website_url=game.website_url,
            developers=game.developers,
            publishers=game.publishers,
            genres=game.genres,
            categories=game.categories,
            release_date=game.release_date,
            is_free=game.is_free,
            catalog_status=game.catalog_status,
            is_active=game.is_active,
            data_coverage=coverage,
            created_at=game.created_at,
            updated_at=game.updated_at,
        )

    def get_game_by_steam_app_id(self, steam_app_id: int) -> GameDetail:
        """Fetch game details by official Steam Application ID."""
        game = self.game_repo.get_by_steam_app_id(steam_app_id)
        if game is None or not game.is_active:
            raise GameNotFoundError(steam_app_id)

        latest_time, review_count, languages = self.game_repo.get_game_data_coverage(game.id)
        coverage = GameDataCoverage(
            latest_collection_at=latest_time,
            stored_reviews_count=review_count,
            language_scope=languages,
        )

        return GameDetail(
            id=game.id,
            steam_app_id=game.steam_app_id,
            name=game.name,
            short_description=game.short_description,
            header_image_url=game.header_image_url,
            website_url=game.website_url,
            developers=game.developers,
            publishers=game.publishers,
            genres=game.genres,
            categories=game.categories,
            release_date=game.release_date,
            is_free=game.is_free,
            catalog_status=game.catalog_status,
            is_active=game.is_active,
            data_coverage=coverage,
            created_at=game.created_at,
            updated_at=game.updated_at,
        )

    def search_games(self, params: GameQueryParams) -> tuple[list[GameListItem], PaginationMeta]:
        """Search and list catalog games with filtering and keyset pagination."""
        games, has_more, next_cursor = self.game_repo.search_catalog(
            q=params.q,
            genre=params.genre,
            catalog_status="indexed",
            sort=params.sort,
            cursor=params.cursor,
            limit=params.limit,
        )

        items = [
            GameListItem(
                id=g.id,
                steam_app_id=g.steam_app_id,
                name=g.name,
                header_image_url=g.header_image_url,
                genres=g.genres,
                release_date=g.release_date,
                catalog_status=g.catalog_status,
                is_active=g.is_active,
            )
            for g in games
        ]

        pagination = PaginationMeta(
            limit=params.limit,
            has_more=has_more,
            next_cursor=next_cursor,
        )
        return items, pagination
