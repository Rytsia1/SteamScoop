import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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
    from app.models.review import Review
    from app.models.sentiment import SentimentPrediction
    from app.models.topic import ReviewTopic, Topic


class MLModel(Base):
    """Registry of deployed and historical model versions."""

    __tablename__ = "ml_model"
    __table_args__ = (
        UniqueConstraint("model_key", "version", "task", name="uq_ml_model_key_version_task"),
        CheckConstraint(
            "task IN ('sentiment', 'absa', 'topic', 'language', 'embedding')",
            name="ck_ml_model_task",
        ),
        CheckConstraint(
            "jsonb_typeof(language_scope) = 'array'",
            name="ck_ml_model_language_scope_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(label_schema) = 'object'",
            name="ck_ml_model_label_schema_is_object",
        ),
        CheckConstraint(
            "jsonb_typeof(config) = 'object'",
            name="ck_ml_model_config_is_object",
        ),
        CheckConstraint(
            "jsonb_typeof(metrics) = 'object'",
            name="ck_ml_model_metrics_is_object",
        ),
        Index("ix_ml_model_task_active", "task", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_key: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    task: Mapped[str] = mapped_column(String(24), nullable=False)
    framework: Mapped[str] = mapped_column(String(40), nullable=False)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokenizer_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    language_scope: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=func.json_build_array()
    )
    label_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    pipeline_runs: Mapped[list["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="ml_model"
    )
    sentiment_predictions: Mapped[list["SentimentPrediction"]] = relationship(
        "SentimentPrediction", back_populates="ml_model"
    )
    aspect_predictions: Mapped[list["AspectPrediction"]] = relationship(
        "AspectPrediction", back_populates="ml_model"
    )
    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="ml_model")


class PipelineRun(Base):
    """One execution of an ML, NLP, or analytics pipeline."""

    __tablename__ = "pipeline_run"
    __table_args__ = (
        CheckConstraint(
            "pipeline_type IN ('sentiment', 'absa', 'topic', 'aggregation', 'full_nlp')",
            name="ck_pipeline_run_type",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_pipeline_run_status",
        ),
        CheckConstraint(
            "input_count >= 0 AND success_count >= 0 AND failure_count >= 0",
            name="ck_pipeline_run_counters",
        ),
        CheckConstraint(
            "finished_at IS NULL OR (started_at IS NOT NULL AND finished_at >= started_at)",
            name="ck_pipeline_run_timing",
        ),
        Index("ix_pipeline_run_type_status_created", "pipeline_type", "status", "created_at"),
        Index("ix_pipeline_run_game_created", "game_id", "created_at"),
        Index("ix_pipeline_run_model_created", "ml_model_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_type: Mapped[str] = mapped_column(String(24), nullable=False)
    ml_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ml_model.id", ondelete="RESTRICT", name="fk_pipeline_run_ml_model_id"),
        nullable=True,
    )
    game_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game.id", ondelete="RESTRICT", name="fk_pipeline_run_game_id"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="queued", server_default="queued"
    )
    input_filter: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    model_version_snapshot: Mapped[str | None] = mapped_column(String(40), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    input_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    success_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    failure_count: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )

    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    ml_model: Mapped["MLModel | None"] = relationship("MLModel", back_populates="pipeline_runs")
    game: Mapped["Game | None"] = relationship("Game")
    items: Mapped[list["PipelineRunItem"]] = relationship(
        "PipelineRunItem",
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
    )
    sentiment_predictions: Mapped[list["SentimentPrediction"]] = relationship(
        "SentimentPrediction", back_populates="pipeline_run"
    )
    aspect_predictions: Mapped[list["AspectPrediction"]] = relationship(
        "AspectPrediction", back_populates="pipeline_run"
    )
    review_topics: Mapped[list["ReviewTopic"]] = relationship(
        "ReviewTopic", back_populates="pipeline_run"
    )


class PipelineRunItem(Base):
    """Item-level processing outcome for an NLP pipeline run."""

    __tablename__ = "pipeline_run_item"
    __table_args__ = (
        UniqueConstraint("pipeline_run_id", "item_key", name="uq_pipeline_run_item_run_key"),
        CheckConstraint(
            "status IN ('succeeded', 'failed')",
            name="ck_pipeline_run_item_status",
        ),
        Index("ix_pipeline_run_item_run_status", "pipeline_run_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "pipeline_run.id",
            ondelete="CASCADE",
            name="fk_pipeline_run_item_pipeline_run_id",
        ),
        nullable=False,
    )
    review_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("review.id", ondelete="RESTRICT", name="fk_pipeline_run_item_review_id"),
        nullable=True,
    )
    item_key: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    pipeline_run: Mapped["PipelineRun"] = relationship("PipelineRun", back_populates="items")
    review: Mapped["Review | None"] = relationship("Review")
