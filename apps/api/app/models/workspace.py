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


class User(Base):
    """Platform user account for research workspaces and administration."""

    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'pending', 'deleted')",
            name="ck_user_status",
        ),
        Index("ix_user_email_lower_unique", func.lower(text("email")), unique=True),
        Index("ix_user_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

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
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole",
        foreign_keys="[UserRole.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    owned_projects: Mapped[list["ResearchProject"]] = relationship(
        "ResearchProject", back_populates="owner"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"


class Role(Base):
    """Platform role definitions."""

    __tablename__ = "role"
    __table_args__ = (UniqueConstraint("role_key", name="uq_role_key"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_key: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    user_roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, role_key='{self.role_key}')>"


class UserRole(Base):
    """User-to-role assignment."""

    __tablename__ = "user_role"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE", name="fk_user_role_user_id"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE", name="fk_user_role_role_id"),
        primary_key=True,
    )
    granted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL", name="fk_user_role_granted_by_user_id"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")
    granted_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[granted_by_user_id])


class ResearchProject(Base):
    """User-owned research workspace."""

    __tablename__ = "research_project"
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('private', 'shared')",
            name="ck_research_project_visibility",
        ),
        CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_research_project_status",
        ),
        Index("ix_research_project_owner_updated", "owner_user_id", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="RESTRICT", name="fk_research_project_owner_user_id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, default="private", server_default="private"
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="active", server_default="active"
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
    owner: Mapped["User"] = relationship("User", back_populates="owned_projects")
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    games: Mapped[list["ProjectGame"]] = relationship(
        "ProjectGame",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    saved_analyses: Mapped[list["SavedAnalysis"]] = relationship(
        "SavedAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectMember(Base):
    """Workspace membership and project roles."""

    __tablename__ = "project_member"
    __table_args__ = (
        CheckConstraint(
            "project_role IN ('owner', 'editor', 'viewer')",
            name="ck_project_member_role",
        ),
        Index("ix_project_member_user_project", "user_id", "project_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_project.id",
            ondelete="CASCADE",
            name="fk_project_member_project_id",
        ),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE", name="fk_project_member_user_id"),
        primary_key=True,
    )
    project_role: Mapped[str] = mapped_column(
        String(16), nullable=False, default="viewer", server_default="viewer"
    )
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "user.id",
            ondelete="SET NULL",
            name="fk_project_member_invited_by_user_id",
        ),
        nullable=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="members")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    invited_by_user: Mapped["User | None"] = relationship("User", foreign_keys=[invited_by_user_id])


class ProjectGame(Base):
    """Games included in a research project."""

    __tablename__ = "project_game"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_project.id",
            ondelete="CASCADE",
            name="fk_project_game_project_id",
        ),
        primary_key=True,
    )
    game_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("game.id", ondelete="RESTRICT", name="fk_project_game_game_id"),
        primary_key=True,
    )
    added_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL", name="fk_project_game_added_by_user_id"),
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    project: Mapped["ResearchProject"] = relationship("ResearchProject", back_populates="games")
    game: Mapped["Game"] = relationship("Game")
    added_by_user: Mapped["User | None"] = relationship("User")


class SavedAnalysis(Base):
    """Reusable query/filter configuration for analysis."""

    __tablename__ = "saved_analysis"
    __table_args__ = (
        CheckConstraint(
            "jsonb_typeof(query_config) = 'object'",
            name="ck_saved_analysis_query_config_is_object",
        ),
        Index("ix_saved_analysis_project_updated", "project_id", "updated_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_project.id",
            ondelete="CASCADE",
            name="fk_saved_analysis_project_id",
        ),
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            name="fk_saved_analysis_created_by_user_id",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False)

    query_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
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
    project: Mapped["ResearchProject"] = relationship(
        "ResearchProject", back_populates="saved_analyses"
    )
    created_by_user: Mapped["User"] = relationship("User")
    snapshots: Mapped[list["AnalysisSnapshot"]] = relationship(
        "AnalysisSnapshot",
        back_populates="saved_analysis",
        cascade="all, delete-orphan",
    )


class AnalysisSnapshot(Base):
    """Immutable record of an analysis result at a point in time."""

    __tablename__ = "analysis_snapshot"
    __table_args__ = (
        UniqueConstraint(
            "saved_analysis_id",
            "snapshot_number",
            name="uq_analysis_snapshot_analysis_number",
        ),
        Index("ix_analysis_snapshot_saved_analysis_created", "saved_analysis_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saved_analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "saved_analysis.id",
            ondelete="CASCADE",
            name="fk_analysis_snapshot_saved_analysis_id",
        ),
        nullable=False,
    )
    snapshot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    data_cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    model_versions: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    filter_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    result_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    result_artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    saved_analysis: Mapped["SavedAnalysis"] = relationship(
        "SavedAnalysis", back_populates="snapshots"
    )


class ExportJob(Base):
    """Asynchronous analytical export lifecycle."""

    __tablename__ = "export_job"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'expired', 'cancelled')",
            name="ck_export_job_status",
        ),
        CheckConstraint(
            "format IN ('csv', 'json', 'xlsx')",
            name="ck_export_job_format",
        ),
        CheckConstraint(
            "row_count IS NULL OR row_count >= 0",
            name="ck_export_job_row_count",
        ),
        CheckConstraint(
            "expires_at IS NULL OR expires_at > created_at",
            name="ck_export_job_expires_at",
        ),
        Index("ix_export_job_user_created", "requested_by_user_id", "created_at"),
        Index(
            "ix_export_job_active",
            "status",
            "created_at",
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "user.id",
            ondelete="RESTRICT",
            name="fk_export_job_requested_by_user_id",
        ),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "research_project.id",
            ondelete="SET NULL",
            name="fk_export_job_project_id",
        ),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="queued", server_default="queued"
    )
    format: Mapped[str] = mapped_column(String(12), nullable=False)
    export_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=func.json_build_object()
    )
    row_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    artifact_uri: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Relationships
    requested_by_user: Mapped["User"] = relationship("User")
    project: Mapped["ResearchProject | None"] = relationship("ResearchProject")


class AuditLog(Base):
    """Append-only security and administration event log."""

    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint(
            "jsonb_typeof(metadata) = 'object'",
            name="ck_audit_log_metadata_is_object",
        ),
        Index("ix_audit_log_created", "created_at"),
        Index("ix_audit_log_actor_created", "actor_user_id", "created_at"),
        Index("ix_audit_log_resource_created", "resource_type", "resource_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="SET NULL", name="fk_audit_log_actor_user_id"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Explicit column name "metadata" in DB
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

    # Relationships
    actor_user: Mapped["User | None"] = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', actor={self.actor_user_id})>"
