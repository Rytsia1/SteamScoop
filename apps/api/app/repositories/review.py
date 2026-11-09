import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.cursor import decode_cursor, encode_cursor
from app.models.ml import MLModel
from app.models.review import Review
from app.models.sentiment import SentimentPrediction
from app.repositories.base import BaseRepository


class ReviewRepository(BaseRepository[Review]):
    """Repository handling Steam review persistence, idempotent upserts, and querying."""

    def __init__(self, session: Session) -> None:
        super().__init__(Review, session)

    def get_by_steam_review_id(self, game_id: uuid.UUID, steam_review_id: int) -> Review | None:
        """Fetch a single review by the composite idempotency key (game_id, steam_review_id)."""
        stmt = select(Review).where(
            Review.game_id == game_id,
            Review.steam_review_id == steam_review_id,
        )
        return self.session.scalars(stmt).first()

    def get_review_with_sentiment(
        self, review_id: uuid.UUID
    ) -> tuple[Review, SentimentPrediction | None, MLModel | None] | None:
        """Fetch review joined with its current sentiment prediction and ML model version."""
        stmt = (
            select(Review, SentimentPrediction, MLModel)
            .outerjoin(
                SentimentPrediction,
                and_(
                    SentimentPrediction.review_id == Review.id,
                    SentimentPrediction.is_current.is_(True),
                ),
            )
            .outerjoin(MLModel, SentimentPrediction.ml_model_id == MLModel.id)
            .where(Review.id == review_id)
        )
        row = self.session.execute(stmt).first()
        if not row:
            return None
        review, sentiment, model = row
        return review, sentiment, model

    def get_game_reviews_paginated(
        self,
        game_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None,
        language: str | None = None,
        steam_recommended: bool | None = None,
        sentiment: str | None = None,
        sort: str = "created_at_desc",
    ) -> tuple[
        Sequence[tuple[Review, SentimentPrediction | None, MLModel | None]],
        bool,
        str | None,
    ]:
        """Fetch keyset-paginated reviews for a game with optional filters and sentiment."""
        stmt = (
            select(Review, SentimentPrediction, MLModel)
            .outerjoin(
                SentimentPrediction,
                and_(
                    SentimentPrediction.review_id == Review.id,
                    SentimentPrediction.is_current.is_(True),
                ),
            )
            .outerjoin(MLModel, SentimentPrediction.ml_model_id == MLModel.id)
            .where(Review.game_id == game_id)
        )

        if language:
            stmt = stmt.where(Review.language == language)
        if steam_recommended is not None:
            stmt = stmt.where(Review.voted_up == steam_recommended)
        if sentiment:
            stmt = stmt.where(SentimentPrediction.label == sentiment)

        if sort == "created_at_asc":
            if cursor:
                cursor_ts_str, cursor_id = decode_cursor(cursor)
                cursor_dt = datetime.fromisoformat(cursor_ts_str) if cursor_ts_str else None
                if cursor_dt:
                    stmt = stmt.where(
                        or_(
                            Review.steam_created_at > cursor_dt,
                            and_(Review.steam_created_at == cursor_dt, Review.id > cursor_id),
                        )
                    )
            stmt = stmt.order_by(Review.steam_created_at.asc().nullsfirst(), Review.id.asc())
        elif sort == "votes_up_desc":
            if cursor:
                cursor_votes, cursor_id = decode_cursor(cursor)
                stmt = stmt.where(
                    or_(
                        Review.votes_up < cursor_votes,
                        and_(Review.votes_up == cursor_votes, Review.id < cursor_id),
                    )
                )
            stmt = stmt.order_by(Review.votes_up.desc(), Review.id.desc())
        else:  # created_at_desc (default)
            if cursor:
                cursor_ts_str, cursor_id = decode_cursor(cursor)
                cursor_dt = datetime.fromisoformat(cursor_ts_str) if cursor_ts_str else None
                if cursor_dt:
                    stmt = stmt.where(
                        or_(
                            Review.steam_created_at < cursor_dt,
                            and_(Review.steam_created_at == cursor_dt, Review.id < cursor_id),
                        )
                    )
            stmt = stmt.order_by(Review.steam_created_at.desc().nullslast(), Review.id.desc())

        # Fetch limit + 1
        rows = list(self.session.execute(stmt.limit(limit + 1)).all())
        has_more = len(rows) > limit
        items = rows[:limit]

        next_cursor = None
        if has_more and items:
            last_review, _, _ = items[-1]
            if sort == "created_at_asc":
                created_at = last_review.steam_created_at
                val = created_at.isoformat() if created_at else ""
                next_cursor = encode_cursor(val, last_review.id)
            elif sort == "votes_up_desc":
                next_cursor = encode_cursor(last_review.votes_up, last_review.id)
            else:
                created_at = last_review.steam_created_at
                val = created_at.isoformat() if created_at else ""
                next_cursor = encode_cursor(val, last_review.id)

        typed_items: list[tuple[Review, SentimentPrediction | None, MLModel | None]] = [
            (r, s, m) for r, s, m in items
        ]
        return typed_items, has_more, next_cursor

    def upsert_review(
        self,
        game_id: uuid.UUID,
        steam_review_id: int,
        review_text: str,
        voted_up: bool,
        commit: bool = True,
        **kwargs: Any,
    ) -> tuple[Review, bool]:
        """Idempotently insert or update a Review record for a game.

        Guarantees that re-fetching a review updates the existing row without creating
        duplicates, preserving the idempotency invariant (game_id, steam_review_id).

        Returns (review, is_created).
        """
        existing = self.get_by_steam_review_id(game_id, steam_review_id)
        if existing is not None:
            existing.review_text = review_text
            existing.voted_up = voted_up
            for key, value in kwargs.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.session.add(existing)
            if commit:
                self.session.commit()
                self.session.refresh(existing)
            else:
                self.session.flush()
            return existing, False

        review = Review(
            game_id=game_id,
            steam_review_id=steam_review_id,
            review_text=review_text,
            voted_up=voted_up,
            **kwargs,
        )
        self.session.add(review)
        if commit:
            self.session.commit()
            self.session.refresh(review)
        else:
            self.session.flush()
        return review, True

    def get_reviews_by_game(
        self,
        game_id: uuid.UUID,
        voted_up: bool | None = None,
        language: str | None = None,
        limit: int = 50,
        before_timestamp: datetime | None = None,
    ) -> Sequence[Review]:
        """Fetch chronologically descending reviews for a game supporting filters."""
        stmt = select(Review).where(Review.game_id == game_id)

        if voted_up is not None:
            stmt = stmt.where(Review.voted_up == voted_up)
        if language is not None:
            stmt = stmt.where(Review.language == language)
        if before_timestamp is not None:
            stmt = stmt.where(Review.steam_created_at < before_timestamp)

        stmt = stmt.order_by(Review.steam_created_at.desc().nullslast()).limit(limit)
        return self.session.scalars(stmt).all()

    def count_reviews_by_game(self, game_id: uuid.UUID) -> int:
        """Count total collected reviews for a game."""
        stmt = select(func.count(Review.id)).where(Review.game_id == game_id)
        return self.session.scalar(stmt) or 0
