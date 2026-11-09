import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review
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
