import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import GameNotFoundError
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.repositories.game import GameRepository
from app.schemas.common import PaginationMeta
from app.schemas.game import (
    CoverageSummary,
    GameDataCoverage,
    GameDetail,
    GameListItem,
    GameOverviewData,
    GameQueryParams,
    ModelSentimentSummary,
    SteamRecommendationSummary,
)


class GameService:
    """Domain service encapsulating catalog business logic and game discovery."""

    def __init__(self, game_repo: GameRepository, session: Session | None = None) -> None:
        self.game_repo = game_repo
        self.session = session or game_repo.session

    def get_game_by_id(self, game_id: uuid.UUID) -> GameDetail:
        """Fetch complete public game details by internal UUID."""
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

    def get_game_overview(
        self,
        game_id: uuid.UUID,
        from_date: date | None = None,
        to_date: date | None = None,
        model_version: str = "baseline",
    ) -> GameOverviewData:
        """Fetch summary metrics and collection coverage for GET /games/{game_id}/overview."""
        game = self.game_repo.get_active_game_by_id(game_id)
        if game is None:
            raise GameNotFoundError(str(game_id))

        # 1. Query Steam reviews and recommendation metrics
        review_query = select(Review).where(Review.game_id == game_id)
        timestamp_col = func.coalesce(Review.steam_created_at, Review.created_at)
        if from_date:
            review_query = review_query.where(timestamp_col >= from_date)
        if to_date:
            review_query = review_query.where(timestamp_col < to_date)

        reviews = list(self.session.scalars(review_query).all())
        review_count = len(reviews)

        rec_count = sum(1 for r in reviews if r.voted_up is True)
        not_rec_count = sum(1 for r in reviews if r.voted_up is False)
        rec_sum = rec_count + not_rec_count
        steam_pos_rate = round(rec_count / rec_sum, 4) if rec_sum > 0 else 0.0

        # 2. Query Sentiment predictions
        review_ids = [r.id for r in reviews]
        pos_sent = 0
        neg_sent = 0
        neu_sent = 0

        if review_ids:
            sent_query = select(SentimentPrediction).where(
                SentimentPrediction.review_id.in_(review_ids),
                SentimentPrediction.is_current.is_(True),
            )
            for sp in self.session.scalars(sent_query).all():
                lbl = (sp.label or "").lower()
                if lbl == "positive":
                    pos_sent += 1
                elif lbl == "negative":
                    neg_sent += 1
                elif lbl == "neutral":
                    neu_sent += 1

        classified_count = pos_sent + neg_sent + neu_sent
        unclassified_count = max(0, review_count - classified_count)
        model_pos_rate = round(pos_sent / classified_count, 4) if classified_count > 0 else 0.0

        latest_time, _, languages = self.game_repo.get_game_data_coverage(game_id)

        return GameOverviewData(
            game_id=game_id,
            review_count=review_count,
            steam_recommendation=SteamRecommendationSummary(
                recommended_count=rec_count,
                not_recommended_count=not_rec_count,
                positive_rate=steam_pos_rate,
            ),
            model_sentiment=ModelSentimentSummary(
                positive_count=pos_sent,
                negative_count=neg_sent,
                neutral_count=neu_sent,
                unclassified_count=unclassified_count,
                positive_rate=model_pos_rate,
                model_version=model_version,
            ),
            coverage=CoverageSummary(
                collected_at=latest_time,
                sampled=True,
                language_scope=languages or ["all"],
                collection_policy="weekly_hybrid_sample",
            ),
        )
