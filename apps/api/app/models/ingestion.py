import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.game import Game
    from app.models.workspace import User


class IngestionJob(Base):
    """Durable logical collection job tracking collection lifecycle."""

    __tablename__ = "ingestion_job"
    __table_args__ = (
        CheckConstraint(
            "job_type IN ('historical', 'incremental')",
            name="ck_ingestion_job_type",
        ),
        CheckConstraint(
            "status IN ("
            "'queued', 'running', 'retrying', 'succeeded', 'partial', 'failed', 'cancelled'"
            ")",
            name="ck_ingestion_job_status",
        ),
        CheckConstraint(
            "reviews_seen >= 0 AND reviews_inserted >= 0 AND "
            "reviews_updated >= 0 AND pages_processed >= 0 AND retry_count >= 0",
            name="ck_ingestion_job_counters",
        ),
        CheckConstraint(
            "finished_at IS NULL OR (started_at IS NOT NULL AND finished_at >= started_at)",
            name="ck_ingestion_job_timing",
        ),
        Index("ix_ingestion_job_status_scheduled", "status", "scheduled_at"),
        Index("ix_ingestion_job_game_created", "game_id", "created_at"),
        Index(
            "uq_ingestion_job_active_game_job_type",
            "game_id",
            "job_type",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running', 'retrying')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game.id", ondelete="RESTRICT", name="fk_ingestion_job_game_id"),
        nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(24), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", server_default="queued"
    )
    source_api: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="steam_user_reviews_v1",
        server_default="steam_user_reviews_v1",
    )
    request_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "user.id",
            ondelete="SET NULL",
            name="fk_ingestion_job_requested_by_user_id",
        ),
        nullable=True,
    )

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reviews_seen: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    reviews_inserted: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    reviews_updated: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    pages_processed: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    game: Mapped["Game"] = relationship("Game", back_populates="ingestion_jobs")
    requested_by_user: Mapped["User | None"] = relationship("User")
    batches: Mapped[list["IngestionBatch"]] = relationship(
        "IngestionBatch",
        back_populates="ingestion_job",
        cascade="all, delete-orphan",
    )


class IngestionBatch(Base):
    """Per-page / per-batch result and cursor evidence for an ingestion job."""

    __tablename__ = "ingestion_batch"
    __table_args__ = (
        UniqueConstraint("ingestion_job_id", "batch_number", name="uq_ingestion_batch_job_batch"),
        CheckConstraint("batch_number > 0", name="ck_ingestion_batch_number_positive"),
        CheckConstraint(
            "source_count >= 0 AND inserted_count >= 0 AND "
            "updated_count >= 0 AND duplicate_count >= 0",
            name="ck_ingestion_batch_counts_non_negative",
        ),
        CheckConstraint(
            "batch_status IN ('succeeded', 'failed', 'empty', 'rate_limited')",
            name="ck_ingestion_batch_status",
        ),
        CheckConstraint(
            "http_status IS NULL OR (http_status BETWEEN 100 AND 599)",
            name="ck_ingestion_batch_http_status",
        ),
        Index("ix_ingestion_batch_job_batch", "ingestion_job_id", "batch_number"),
        Index("ix_ingestion_batch_game_created", "game_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingestion_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ingestion_job.id",
            ondelete="CASCADE",
            name="fk_ingestion_batch_ingestion_job_id",
        ),
        nullable=False,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game.id", ondelete="RESTRICT", name="fk_ingestion_batch_game_id"),
        nullable=False,
    )
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False)
    cursor_in: Mapped[str | None] = mapped_column(Text, nullable=True)
    cursor_out: Mapped[str | None] = mapped_column(Text, nullable=True)

    request_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    http_status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    source_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    inserted_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    updated_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    duplicate_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    batch_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="succeeded",
        server_default="succeeded",
    )
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    ingestion_job: Mapped["IngestionJob"] = relationship("IngestionJob", back_populates="batches")
    game: Mapped["Game"] = relationship("Game", back_populates="ingestion_batches")


class CollectionCheckpoint(Base):
    """Durable cursor and watermark by game and collection stream."""

    __tablename__ = "collection_checkpoint"
    __table_args__ = (
        UniqueConstraint("game_id", "stream_key", name="uq_collection_checkpoint_game_stream"),
        CheckConstraint(
            "collection_mode IN ('historical', 'incremental')",
            name="ck_checkpoint_mode",
        ),
        CheckConstraint(
            "status IN ('idle', 'running', 'paused', 'error')",
            name="ck_checkpoint_status",
        ),
        Index("ix_collection_checkpoint_status_updated", "status", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "game.id",
            ondelete="RESTRICT",
            name="fk_collection_checkpoint_game_id",
        ),
        nullable=False,
    )
    stream_key: Mapped[str] = mapped_column(String(120), nullable=False)
    collection_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    cursor: Mapped[str | None] = mapped_column(Text, nullable=True)
    watermark_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "ingestion_job.id",
            ondelete="SET NULL",
            name="fk_collection_checkpoint_last_successful_job_id",
        ),
        nullable=True,
    )
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="idle", server_default="idle"
    )

    # Explicit column name "metadata" in DB, avoiding conflict with SQLAlchemy Base.metadata
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default=func.json_build_object(),
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
    game: Mapped["Game"] = relationship("Game", back_populates="collection_checkpoints")
    last_successful_job: Mapped["IngestionJob | None"] = relationship("IngestionJob")
