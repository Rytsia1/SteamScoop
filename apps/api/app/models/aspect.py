import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.ml import MLModel, PipelineRun
    from app.models.review import Review


class Aspect(Base):
    """Controlled aspect taxonomy for aspect-based sentiment analysis."""

    __tablename__ = "aspect"
    __table_args__ = (
        UniqueConstraint("aspect_key", name="uq_aspect_key"),
        CheckConstraint(
            "parent_aspect_id IS NULL OR parent_aspect_id <> id",
            name="ck_aspect_prevent_self_parent",
        ),
        Index("ix_aspect_parent_aspect_id", "parent_aspect_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aspect_key: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_aspect_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("aspect.id", ondelete="RESTRICT", name="fk_aspect_parent_aspect_id"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
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
    parent_aspect: Mapped["Aspect | None"] = relationship(
        "Aspect", remote_side=[id], back_populates="sub_aspects"
    )
    sub_aspects: Mapped[list["Aspect"]] = relationship("Aspect", back_populates="parent_aspect")
    predictions: Mapped[list["AspectPrediction"]] = relationship(
        "AspectPrediction", back_populates="aspect"
    )

    def __repr__(self) -> str:
        return f"<Aspect(id={self.id}, aspect_key='{self.aspect_key}')>"


class AspectPrediction(Base):
    """Review-level aspect and polarity result."""

    __tablename__ = "aspect_prediction"
    __table_args__ = (
        UniqueConstraint(
            "review_id",
            "aspect_id",
            "ml_model_id",
            "pipeline_run_id",
            name="uq_aspect_prediction_review_aspect_model_run",
        ),
        CheckConstraint(
            "sentiment_label IN ('positive', 'negative', 'neutral')",
            name="ck_aspect_prediction_label",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence BETWEEN 0 AND 1)",
            name="ck_aspect_prediction_confidence",
        ),
        CheckConstraint(
            "(start_offset IS NULL AND end_offset IS NULL) OR "
            "(start_offset IS NOT NULL AND end_offset IS NOT NULL AND "
            "start_offset >= 0 AND end_offset >= start_offset)",
            name="ck_aspect_prediction_offsets",
        ),
        Index("ix_aspect_prediction_review_model", "review_id", "ml_model_id"),
        Index("ix_aspect_prediction_aspect_label", "aspect_id", "sentiment_label"),
        Index("ix_aspect_prediction_run", "pipeline_run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "review.id",
            ondelete="RESTRICT",
            name="fk_aspect_prediction_review_id",
        ),
        nullable=False,
    )
    aspect_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "aspect.id",
            ondelete="RESTRICT",
            name="fk_aspect_prediction_aspect_id",
        ),
        nullable=False,
    )
    ml_model_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ml_model.id",
            ondelete="RESTRICT",
            name="fk_aspect_prediction_ml_model_id",
        ),
        nullable=False,
    )
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "pipeline_run.id",
            ondelete="RESTRICT",
            name="fk_aspect_prediction_pipeline_run_id",
        ),
        nullable=False,
    )

    sentiment_label: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(6, 5), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    review: Mapped["Review"] = relationship("Review", back_populates="aspect_predictions")
    aspect: Mapped["Aspect"] = relationship("Aspect", back_populates="predictions")
    ml_model: Mapped["MLModel"] = relationship("MLModel", back_populates="aspect_predictions")
    pipeline_run: Mapped["PipelineRun"] = relationship(
        "PipelineRun", back_populates="aspect_predictions"
    )

    def __repr__(self) -> str:
        return f"<AspectPrediction(id={self.id}, review={self.review_id}, aspect={self.aspect_id})>"
