import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import GameAnalytic
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[GameAnalytic]):
    """Repository managing aggregated game intelligence and temporal analytics."""

    def __init__(self, session: Session) -> None:
        super().__init__(GameAnalytic, session)

    def get_analytic(
        self,
        game_id: uuid.UUID,
        period_type: str,
        period_start: date,
        model_version_key: str = "baseline",
    ) -> GameAnalytic | None:
        """Fetch aggregate for a game, period type, period start, and model version."""
        stmt = select(GameAnalytic).where(
            GameAnalytic.game_id == game_id,
            GameAnalytic.period_type == period_type,
            GameAnalytic.period_start == period_start,
            GameAnalytic.model_version_key == model_version_key,
        )
        return self.session.scalars(stmt).first()

    def get_timeline(
        self,
        game_id: uuid.UUID,
        period_type: str,
        start_date: date | None = None,
        end_date: date | None = None,
        model_version_key: str = "baseline",
    ) -> Sequence[GameAnalytic]:
        """Fetch chronologically ordered aggregates for a game across a timeline."""
        stmt = select(GameAnalytic).where(
            GameAnalytic.game_id == game_id,
            GameAnalytic.period_type == period_type,
            GameAnalytic.model_version_key == model_version_key,
        )
        if start_date is not None:
            stmt = stmt.where(GameAnalytic.period_start >= start_date)
        if end_date is not None:
            stmt = stmt.where(GameAnalytic.period_start <= end_date)

        stmt = stmt.order_by(GameAnalytic.period_start.asc())
        return self.session.scalars(stmt).all()

    def upsert_analytic(
        self,
        game_id: uuid.UUID,
        period_type: str,
        period_start: date,
        period_end: date,
        model_version_key: str = "baseline",
        review_count: int = 0,
        positive_count: int = 0,
        negative_count: int = 0,
        neutral_count: int = 0,
        steam_recommended_count: int = 0,
        steam_not_recommended_count: int = 0,
        sentiment_score: Decimal | None = None,
        aspect_summary: dict[str, Any] | None = None,
        topic_summary: dict[str, Any] | None = None,
    ) -> tuple[GameAnalytic, bool]:
        """Idempotently create or update an aggregated metric record."""
        existing = self.get_analytic(
            game_id=game_id,
            period_type=period_type,
            period_start=period_start,
            model_version_key=model_version_key,
        )
        if existing is not None:
            existing.period_end = period_end
            existing.review_count = review_count
            existing.positive_count = positive_count
            existing.negative_count = negative_count
            existing.neutral_count = neutral_count
            existing.steam_recommended_count = steam_recommended_count
            existing.steam_not_recommended_count = steam_not_recommended_count
            existing.sentiment_score = sentiment_score
            existing.aspect_summary = aspect_summary or {}
            existing.topic_summary = topic_summary or {}
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing, False

        analytic = GameAnalytic(
            game_id=game_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            model_version_key=model_version_key,
            review_count=review_count,
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            steam_recommended_count=steam_recommended_count,
            steam_not_recommended_count=steam_not_recommended_count,
            sentiment_score=sentiment_score,
            aspect_summary=aspect_summary or {},
            topic_summary=topic_summary or {},
        )
        created = self.create(analytic)
        return created, True

