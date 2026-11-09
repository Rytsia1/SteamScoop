import uuid

from app.core.exceptions import GameNotFoundError, ReviewNotFoundError
from app.repositories.game import GameRepository
from app.repositories.review import ReviewRepository
from app.schemas.common import PaginationMeta
from app.schemas.review import (
    ReviewDetail,
    ReviewListItem,
    ReviewQueryParams,
    SentimentSummary,
)


class ReviewService:
    """Domain service encapsulating review retrieval, filtering, and sentiment attachment."""

    def __init__(self, game_repo: GameRepository, review_repo: ReviewRepository) -> None:
        self.game_repo = game_repo
        self.review_repo = review_repo

    def get_review(self, review_id: uuid.UUID) -> ReviewDetail:
        """Fetch complete public details for a single review by UUID.

        Raises ReviewNotFoundError if the review record does not exist.
        """
        row = self.review_repo.get_review_with_sentiment(review_id)
        if row is None:
            raise ReviewNotFoundError(str(review_id))

        review, sentiment, model = row
        sentiment_summary = None
        if sentiment is not None:
            sentiment_summary = SentimentSummary(
                label=sentiment.label,
                confidence=(
                    float(sentiment.confidence) if sentiment.confidence is not None else None
                ),
                model_version=model.model_key if model else "unknown",
            )

        return ReviewDetail(
            id=review.id,
            game_id=review.game_id,
            steam_review_id=review.steam_review_id,
            review_text=review.review_text,
            language=review.language,
            voted_up=review.voted_up,
            votes_up=review.votes_up,
            votes_funny=review.votes_funny,
            weighted_vote_score=review.weighted_vote_score,
            comment_count=review.comment_count,
            steam_playtime_at_review=review.steam_playtime_at_review,
            steam_playtime_forever=review.steam_playtime_forever,
            steam_playtime_last_two_weeks=review.steam_playtime_last_two_weeks,
            steam_purchase=review.steam_purchase,
            received_for_free=review.received_for_free,
            written_during_early_access=review.written_during_early_access,
            steam_created_at=review.steam_created_at,
            steam_updated_at=review.steam_updated_at,
            first_collected_at=review.first_collected_at,
            last_seen_at=review.last_seen_at,
            sentiment=sentiment_summary,
        )

    def get_game_reviews(
        self, game_id: uuid.UUID, params: ReviewQueryParams
    ) -> tuple[list[ReviewListItem], PaginationMeta]:
        """Fetch a paginated slice of reviews for a game, validating game existence.

        Raises GameNotFoundError if the target game does not exist or is inactive.
        """
        game = self.game_repo.get_active_game_by_id(game_id)
        if game is None:
            raise GameNotFoundError(str(game_id))

        rows, has_more, next_cursor = self.review_repo.get_game_reviews_paginated(
            game_id=game_id,
            limit=params.limit,
            cursor=params.cursor,
            language=params.language,
            steam_recommended=params.steam_recommended,
            sentiment=params.sentiment,
            sort=params.sort,
        )

        items: list[ReviewListItem] = []
        for review, sentiment, model in rows:
            sentiment_summary = None
            if sentiment is not None:
                sentiment_summary = SentimentSummary(
                    label=sentiment.label,
                    confidence=float(sentiment.confidence)
                    if sentiment.confidence is not None
                    else None,
                    model_version=model.model_key if model else "unknown",
                )

            items.append(
                ReviewListItem(
                    id=review.id,
                    steam_review_id=review.steam_review_id,
                    review_text=review.review_text,
                    language=review.language,
                    voted_up=review.voted_up,
                    votes_up=review.votes_up,
                    votes_funny=review.votes_funny,
                    weighted_vote_score=review.weighted_vote_score,
                    comment_count=review.comment_count,
                    steam_playtime_forever=review.steam_playtime_forever,
                    steam_created_at=review.steam_created_at,
                    sentiment=sentiment_summary,
                )
            )

        pagination = PaginationMeta(
            limit=params.limit,
            has_more=has_more,
            next_cursor=next_cursor,
        )
        return items, pagination
