import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import GameNotFoundError, ReviewNotFoundError
from app.models.aspect import Aspect, AspectPrediction
from app.models.ml import MLModel
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.models.topic import ReviewTopic, Topic
from app.repositories.game import GameRepository
from app.repositories.review import ReviewRepository
from app.schemas.common import PaginationMeta
from app.schemas.review import (
    ReviewAspectIntel,
    ReviewDetail,
    ReviewIntelligenceData,
    ReviewListItem,
    ReviewQueryParams,
    ReviewTopicIntel,
    SentimentSummary,
)


class ReviewService:
    """Domain service encapsulating review retrieval, filtering, and sentiment attachment."""

    def __init__(
        self,
        game_repo: GameRepository,
        review_repo: ReviewRepository,
        session: Session | None = None,
    ) -> None:
        self.game_repo = game_repo
        self.review_repo = review_repo
        self.session = session or review_repo.session

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

    def get_review_intelligence(self, review_id: uuid.UUID) -> ReviewIntelligenceData:
        """Fetch combined sentiment, aspect, and topic intelligence for review."""
        review = self.session.get(Review, review_id)
        if not review:
            raise ReviewNotFoundError(str(review_id))

        # 1. Fetch current sentiment prediction
        sent_stmt = (
            select(SentimentPrediction, MLModel)
            .outerjoin(MLModel, SentimentPrediction.ml_model_id == MLModel.id)
            .where(
                SentimentPrediction.review_id == review_id,
                SentimentPrediction.is_current.is_(True),
            )
        )
        sent_row = self.session.execute(sent_stmt).first()
        sentiment_summary: SentimentSummary | None = None
        if sent_row:
            sp, m = sent_row
            sentiment_summary = SentimentSummary(
                label=sp.label,
                confidence=float(sp.confidence) if sp.confidence is not None else None,
                model_version=m.version if m else "v1.0.0",
            )

        # 2. Fetch aspect predictions
        asp_stmt = (
            select(AspectPrediction, Aspect)
            .join(Aspect, AspectPrediction.aspect_id == Aspect.id)
            .where(AspectPrediction.review_id == review_id)
            .order_by(AspectPrediction.confidence.desc().nullslast())
        )
        asp_rows = self.session.execute(asp_stmt).all()
        aspect_intel = [
            ReviewAspectIntel(
                aspect_key=asp.aspect_key,
                display_name=asp.display_name,
                sentiment=ap.sentiment_label,
                confidence=float(ap.confidence) if ap.confidence is not None else None,
                evidence_text=ap.evidence_text,
                start_offset=ap.start_offset,
                end_offset=ap.end_offset,
            )
            for ap, asp in asp_rows
        ]

        # 3. Fetch topic assignments
        top_stmt = (
            select(ReviewTopic, Topic, MLModel)
            .join(Topic, ReviewTopic.topic_id == Topic.id)
            .outerjoin(MLModel, Topic.ml_model_id == MLModel.id)
            .where(ReviewTopic.review_id == review_id)
            .order_by(ReviewTopic.is_primary.desc(), ReviewTopic.score.desc().nullslast())
        )
        top_rows = self.session.execute(top_stmt).all()
        topic_intel = [
            ReviewTopicIntel(
                topic_id=rt.topic_id,
                topic_key=top.topic_key,
                label=top.label,
                score=float(rt.score) if rt.score is not None else None,
                model_version=m.version if m else "v1.0.0",
                is_primary=rt.is_primary,
            )
            for rt, top, m in top_rows
        ]

        return ReviewIntelligenceData(
            review_id=review_id,
            sentiment=sentiment_summary,
            aspects=aspect_intel,
            topics=topic_intel,
        )
