import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.aspect import AspectPrediction
    from app.models.game import Game
    from app.models.sentiment import SentimentPrediction
    from app.models.topic import ReviewTopic


class Review(Base):
    """Normalized Steam review record."""

    __tablename__ = "review"
    __table_args__ = (
        UniqueConstraint("game_id", "steam_review_id", name="uq_review_game_steam_review"),
        CheckConstraint("steam_review_id > 0", name="ck_review_steam_review_id_positive"),
        CheckConstraint("votes_up >= 0", name="ck_review_votes_up_non_negative"),
        CheckConstraint("votes_funny >= 0", name="ck_review_votes_funny_non_negative"),
        CheckConstraint("comment_count >= 0", name="ck_review_comment_count_non_negative"),
        CheckConstraint(
            "steam_playtime_at_review IS NULL OR steam_playtime_at_review >= 0",
            name="ck_review_playtime_at_review_non_negative",
        ),
        CheckConstraint(
            "steam_playtime_forever IS NULL OR steam_playtime_forever >= 0",
            name="ck_review_playtime_forever_non_negative",
        ),
        CheckConstraint(
            "steam_playtime_last_two_weeks IS NULL OR steam_playtime_last_two_weeks >= 0",
            name="ck_review_playtime_last_two_weeks_non_negative",
        ),
        CheckConstraint(
            "weighted_vote_score IS NULL OR weighted_vote_score >= 0",
            name="ck_review_weighted_vote_score_non_negative",
        ),
        CheckConstraint(
            "length(trim(review_text)) > 0",
            name="ck_review_text_not_empty",
        ),
        Index("ix_review_game_steam_created", "game_id", "steam_created_at"),
        Index("ix_review_game_voted_created", "game_id", "voted_up", "steam_created_at"),
        Index("ix_review_game_lang_created", "game_id", "language", "steam_created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game.id", ondelete="RESTRICT", name="fk_review_game_id"),
        nullable=False,
    )
    steam_review_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    language: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unknown", server_default="unknown"
    )
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    voted_up: Mapped[bool] = mapped_column(Boolean, nullable=False)
    votes_up: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    votes_funny: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    weighted_vote_score: Mapped[Decimal | None] = mapped_column(Numeric(12, 8), nullable=True)
    comment_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    steam_playtime_at_review: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steam_playtime_forever: Mapped[int | None] = mapped_column(Integer, nullable=True)
    steam_playtime_last_two_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)

    steam_purchase: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    received_for_free: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    written_during_early_access: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    steam_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    steam_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Privacy: raw payload scrubbed of author identifiers
    source_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    first_collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="reviews")
    sentiment_predictions: Mapped[list["SentimentPrediction"]] = relationship(
        "SentimentPrediction", back_populates="review"
    )
    aspect_predictions: Mapped[list["AspectPrediction"]] = relationship(
        "AspectPrediction", back_populates="review"
    )
    review_topics: Mapped[list["ReviewTopic"]] = relationship(
        "ReviewTopic", back_populates="review"
    )

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, game={self.game_id}, steam_id={self.steam_review_id})>"
