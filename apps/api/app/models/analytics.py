import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.game import Game


class GameAnalytic(Base):
    """Precomputed, versioned aggregate metrics for a game and time bucket."""

    __tablename__ = "game_analytic"
    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "period_type",
            "period_start",
            "model_version_key",
            name="uq_game_analytic_period",
        ),
        CheckConstraint(
            "period_type IN ('day', 'week', 'month')",
            name="ck_game_analytic_period_type",
        ),
        CheckConstraint("period_end > period_start", name="ck_game_analytic_period_dates"),
        CheckConstraint(
            "review_count >= 0 AND positive_count >= 0 AND negative_count >= 0 AND "
            "neutral_count >= 0 AND steam_recommended_count >= 0 AND "
            "steam_not_recommended_count >= 0",
            name="ck_game_analytic_counts_non_negative",
        ),
        CheckConstraint(
            "positive_count + negative_count + neutral_count <= review_count",
            name="ck_game_analytic_sentiment_counts_sum",
        ),
        CheckConstraint(
            "steam_recommended_count + steam_not_recommended_count <= review_count",
            name="ck_game_analytic_steam_rec_sum",
        ),
        CheckConstraint(
            "sentiment_score IS NULL OR (sentiment_score BETWEEN -1 AND 1)",
            name="ck_game_analytic_sentiment_score_range",
        ),
        Index("ix_game_analytic_period_start", "period_type", "period_start"),
        Index("ix_game_analytic_game_period_start", "game_id", "period_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game.id", ondelete="RESTRICT", name="fk_game_analytic_game_id"),
        nullable=False,
    )
    period_type: Mapped[str] = mapped_column(String(12), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    model_version_key: Mapped[str] = mapped_column(
        String(120), nullable=False, default="baseline", server_default="baseline"
    )

    review_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    positive_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    negative_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    neutral_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )

    steam_recommended_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    steam_not_recommended_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )

    sentiment_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 5), nullable=True)
    aspect_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    topic_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="analytics")

    def __repr__(self) -> str:
        return (
            f"<GameAnalytic(id={self.id}, game_id={self.game_id}, "
            f"period={self.period_type}:{self.period_start})>"
        )
