import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.analytics import GameAnalytic
    from app.models.ingestion import CollectionCheckpoint, IngestionBatch, IngestionJob
    from app.models.review import Review


class Game(Base):
    """Steam game catalog identity and searchable metadata."""

    __tablename__ = "game"
    __table_args__ = (
        UniqueConstraint("steam_app_id", name="uq_game_steam_app_id"),
        CheckConstraint("steam_app_id > 0", name="ck_game_steam_app_id_positive"),
        CheckConstraint(
            "catalog_status IN ('pending', 'indexed', 'failed', 'disabled')",
            name="ck_game_catalog_status",
        ),
        CheckConstraint(
            "jsonb_typeof(developers) = 'array'",
            name="ck_game_developers_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(publishers) = 'array'",
            name="ck_game_publishers_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(genres) = 'array'",
            name="ck_game_genres_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(categories) = 'array'",
            name="ck_game_categories_is_array",
        ),
        Index("ix_game_catalog_status_is_active", "catalog_status", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    steam_app_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    header_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    developers: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=func.json_build_array()
    )
    publishers: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=func.json_build_array()
    )
    genres: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=func.json_build_array()
    )
    categories: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=func.json_build_array()
    )

    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_free: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    catalog_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    metadata_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships (Deletion policy: RESTRICT from parents)
    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="game")
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(
        "IngestionJob", back_populates="game"
    )
    ingestion_batches: Mapped[list["IngestionBatch"]] = relationship(
        "IngestionBatch", back_populates="game"
    )
    collection_checkpoints: Mapped[list["CollectionCheckpoint"]] = relationship(
        "CollectionCheckpoint", back_populates="game"
    )
    analytics: Mapped[list["GameAnalytic"]] = relationship("GameAnalytic", back_populates="game")

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, steam_app_id={self.steam_app_id}, name='{self.name}')>"
