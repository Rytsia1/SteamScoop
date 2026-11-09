import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.ml import MLModel, PipelineRun
    from app.models.review import Review


class SentimentPrediction(Base):
    """Versioned review-level sentiment prediction."""

    __tablename__ = "sentiment_prediction"
    __table_args__ = (
        UniqueConstraint(
            "review_id",
            "ml_model_id",
            "pipeline_run_id",
            name="uq_sentiment_prediction_review_model_run",
        ),
        CheckConstraint(
            "label IN ('positive', 'negative', 'neutral')",
            name="ck_sentiment_prediction_label",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence BETWEEN 0 AND 1)",
            name="ck_sentiment_prediction_confidence",
        ),
        Index("ix_sentiment_prediction_review_predicted", "review_id", "predicted_at"),
        Index(
            "ix_sentiment_prediction_current",
            "review_id",
            postgresql_where=text("is_current = TRUE"),
        ),
        Index("ix_sentiment_prediction_model_label", "ml_model_id", "label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "review.id",
            ondelete="RESTRICT",
            name="fk_sentiment_prediction_review_id",
        ),
        nullable=False,
    )
    ml_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ml_model.id",
            ondelete="RESTRICT",
            name="fk_sentiment_prediction_ml_model_id",
        ),
        nullable=False,
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "pipeline_run.id",
            ondelete="RESTRICT",
            name="fk_sentiment_prediction_pipeline_run_id",
        ),
        nullable=False,
    )

    label: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(6, 5), nullable=True)
    probabilities: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="sentiment_predictions")
    ml_model: Mapped["MLModel"] = relationship("MLModel", back_populates="sentiment_predictions")
    pipeline_run: Mapped["PipelineRun"] = relationship(
        "PipelineRun", back_populates="sentiment_predictions"
    )

    def __repr__(self) -> str:
        return f"<SentimentPrediction(id={self.id}, review={self.review_id}, label='{self.label}')>"
