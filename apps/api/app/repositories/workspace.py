"""Repository for research projects, project memberships, saved analyses, and snapshots."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.cursor import decode_cursor, encode_cursor
from app.models.workspace import (
    AnalysisSnapshot,
    ProjectGame,
    ProjectMember,
    ResearchProject,
    SavedAnalysis,
)
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[ResearchProject]):
    """Data access repository for research projects, analyses, and reproducibility snapshots."""

    def __init__(self, session: Session) -> None:
        super().__init__(ResearchProject, session)

    def list_user_projects(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[Sequence[ResearchProject], bool, str | None]:
        """Fetch accessible projects (owned, member, or shared) with cursor pagination."""
        stmt = (
            select(ResearchProject)
            .outerjoin(ProjectMember, ProjectMember.project_id == ResearchProject.id)
            .where(
                or_(
                    ResearchProject.owner_user_id == user_id,
                    ProjectMember.user_id == user_id,
                    ResearchProject.visibility == "shared",
                )
            )
            .distinct()
        )

        if cursor:
            cursor_val, cursor_id = decode_cursor(cursor)
            try:
                cursor_dt = datetime.fromisoformat(cursor_val)
                stmt = stmt.where(
                    or_(
                        ResearchProject.updated_at < cursor_dt,
                        and_(
                            ResearchProject.updated_at == cursor_dt,
                            ResearchProject.id > cursor_id,
                        ),
                    )
                )
            except Exception:
                pass

        stmt = stmt.order_by(ResearchProject.updated_at.desc(), ResearchProject.id.asc())
        stmt = stmt.limit(limit + 1)
        records = list(self.session.scalars(stmt).all())

        has_more = len(records) > limit
        items = records[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = encode_cursor(last.updated_at.isoformat(), last.id)

        return items, has_more, next_cursor

    def get_user_project_role(self, project_id: uuid.UUID, user_id: uuid.UUID) -> str | None:
        """Resolve user role on a project: 'owner', 'editor', 'viewer', or None."""
        project = self.session.get(ResearchProject, project_id)
        if not project:
            return None
        if project.owner_user_id == user_id:
            return "owner"

        member = self.session.scalars(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        ).first()

        if member:
            return member.project_role

        if project.visibility == "shared":
            return "viewer"

        return None

    def create_project(
        self,
        owner_user_id: uuid.UUID,
        name: str,
        description: str | None = None,
        visibility: str = "private",
    ) -> ResearchProject:
        """Create new research project workspace."""
        project = ResearchProject(
            owner_user_id=owner_user_id,
            name=name.strip(),
            description=description.strip() if description else None,
            visibility=visibility,
            status="active",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def update_project(
        self,
        project_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        visibility: str | None = None,
    ) -> ResearchProject | None:
        """Update existing project workspace."""
        project = self.session.get(ResearchProject, project_id)
        if not project:
            return None

        if name is not None:
            project.name = name.strip()
        if description is not None:
            project.description = description.strip()
        if visibility is not None:
            project.visibility = visibility

        project.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(project)
        return project

    def add_game(
        self, project_id: uuid.UUID, game_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectGame:
        """Idempotently add a game association to a project."""
        stmt = select(ProjectGame).where(
            ProjectGame.project_id == project_id,
            ProjectGame.game_id == game_id,
        )
        existing = self.session.scalars(stmt).first()
        if existing:
            return existing

        pg = ProjectGame(
            project_id=project_id,
            game_id=game_id,
            added_by_user_id=user_id,
            added_at=datetime.now(UTC),
        )
        self.session.add(pg)
        self.session.commit()
        self.session.refresh(pg)
        return pg

    def remove_game(self, project_id: uuid.UUID, game_id: uuid.UUID) -> bool:
        """Remove a game association from a project."""
        stmt = delete(ProjectGame).where(
            ProjectGame.project_id == project_id,
            ProjectGame.game_id == game_id,
        )
        result = self.session.execute(stmt)
        self.session.commit()
        rowcount = getattr(result, "rowcount", 0)
        return bool(rowcount and rowcount > 0)

    def list_project_games(self, project_id: uuid.UUID) -> Sequence[ProjectGame]:
        """List games associated with a research project."""
        stmt = select(ProjectGame).where(ProjectGame.project_id == project_id)
        return self.session.scalars(stmt).all()

    def list_saved_analyses(self, project_id: uuid.UUID) -> Sequence[SavedAnalysis]:
        """List saved analyses within a project."""
        stmt = (
            select(SavedAnalysis)
            .where(SavedAnalysis.project_id == project_id)
            .order_by(SavedAnalysis.updated_at.desc())
        )
        return self.session.scalars(stmt).all()

    def get_saved_analysis(self, analysis_id: uuid.UUID) -> SavedAnalysis | None:
        """Fetch a single saved analysis by ID."""
        return self.session.get(SavedAnalysis, analysis_id)

    def create_saved_analysis(
        self,
        project_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
        name: str,
        description: str | None,
        analysis_type: str,
        query_config: dict[str, Any],
    ) -> SavedAnalysis:
        """Create a new saved analysis configuration."""
        analysis = SavedAnalysis(
            project_id=project_id,
            created_by_user_id=created_by_user_id,
            name=name.strip(),
            description=description.strip() if description else None,
            analysis_type=analysis_type,
            query_config=query_config,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(analysis)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def update_saved_analysis(
        self,
        analysis_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        query_config: dict[str, Any] | None = None,
    ) -> SavedAnalysis | None:
        """Update existing saved analysis configuration."""
        analysis = self.session.get(SavedAnalysis, analysis_id)
        if not analysis:
            return None

        if name is not None:
            analysis.name = name.strip()
        if description is not None:
            analysis.description = description.strip()
        if query_config is not None:
            analysis.query_config = query_config

        analysis.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(analysis)
        return analysis

    def delete_saved_analysis(self, analysis_id: uuid.UUID) -> bool:
        """Delete saved analysis."""
        analysis = self.session.get(SavedAnalysis, analysis_id)
        if not analysis:
            return False
        self.session.delete(analysis)
        self.session.commit()
        return True

    def create_snapshot(
        self,
        saved_analysis_id: uuid.UUID,
        name: str,
        description: str | None = None,
        configuration_snapshot: dict[str, Any] | None = None,
        result_summary: dict[str, Any] | None = None,
    ) -> AnalysisSnapshot:
        """Create an immutable reproducibility snapshot for an analysis."""
        # Find next snapshot number
        max_num_stmt = select(func.max(AnalysisSnapshot.snapshot_number)).where(
            AnalysisSnapshot.saved_analysis_id == saved_analysis_id
        )
        current_max = self.session.scalars(max_num_stmt).first() or 0
        next_num = current_max + 1

        snapshot = AnalysisSnapshot(
            saved_analysis_id=saved_analysis_id,
            snapshot_number=next_num,
            data_cutoff_at=datetime.now(UTC),
            model_versions={"sentiment": "v1.0.0", "absa": "v1.0.0", "topic": "v1.0.0"},
            filter_snapshot=configuration_snapshot or {},
            result_summary=result_summary or {"status": "captured", "name": name},
            created_at=datetime.now(UTC),
        )
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot

    def list_snapshots(self, saved_analysis_id: uuid.UUID) -> Sequence[AnalysisSnapshot]:
        """List snapshots for a saved analysis."""
        stmt = (
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.saved_analysis_id == saved_analysis_id)
            .order_by(AnalysisSnapshot.snapshot_number.desc())
        )
        return self.session.scalars(stmt).all()
