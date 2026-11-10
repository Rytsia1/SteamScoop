"""Domain service managing research workspaces, saved analyses, and snapshots."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    AnalysisNotFoundError,
    ForbiddenError,
    GameNotFoundError,
    ProjectNotFoundError,
    ResourceNotFoundError,
    UserNotFoundError,
)
from app.models.game import Game
from app.models.workspace import User
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.common import PaginationMeta
from app.schemas.workspace import (
    AnalysisSnapshotResponse,
    ProjectAddMemberRequest,
    ProjectCreateRequest,
    ProjectGameItem,
    ProjectMemberItem,
    ProjectResponse,
    ProjectUpdateRequest,
    SavedAnalysisCreateRequest,
    SavedAnalysisResponse,
    SavedAnalysisUpdateRequest,
    SnapshotCreateRequest,
)


class WorkspaceService:
    """Service orchestrating research project workspaces and reproducibility snapshots."""

    def __init__(
        self,
        session: Session,
        workspace_repo: WorkspaceRepository | None = None,
        user_repo: UserRepository | None = None,
    ) -> None:
        self.session = session
        self.workspace_repo = workspace_repo or WorkspaceRepository(session)
        self.user_repo = user_repo or UserRepository(session)

    def list_projects(
        self, user: User, limit: int = 20, cursor: str | None = None
    ) -> tuple[list[ProjectResponse], PaginationMeta]:
        """List accessible projects for the current user."""
        items, has_more, next_cursor = self.workspace_repo.list_user_projects(
            user_id=user.id, limit=limit, cursor=cursor
        )
        responses: list[ProjectResponse] = []
        for p in items:
            role = self.workspace_repo.get_user_project_role(p.id, user.id)
            resp = ProjectResponse.model_validate(p)
            resp.current_user_role = role
            responses.append(resp)

        pagination = PaginationMeta(limit=limit, has_more=has_more, next_cursor=next_cursor)
        return responses, pagination

    def create_project(self, user: User, req: ProjectCreateRequest) -> ProjectResponse:
        """Create new research project workspace."""
        proj = self.workspace_repo.create_project(
            owner_user_id=user.id,
            name=req.name,
            description=req.description,
            visibility=req.visibility,
        )
        resp = ProjectResponse.model_validate(proj)
        resp.current_user_role = "owner"
        return resp

    def get_project(self, user: User, project_id: uuid.UUID) -> ProjectResponse:
        """Fetch project details enforcing object-level authorization.

        Returns 404 rather than 403 when private to prevent resource existence disclosure.
        """
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        proj = self.workspace_repo.get(project_id)
        if not proj:
            raise ProjectNotFoundError(str(project_id))

        resp = ProjectResponse.model_validate(proj)
        resp.current_user_role = role
        return resp

    def update_project(
        self, user: User, project_id: uuid.UUID, req: ProjectUpdateRequest
    ) -> ProjectResponse:
        """Update research project. Owner or editor permission required."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can modify project details.")

        proj = self.workspace_repo.update_project(
            project_id=project_id,
            name=req.name,
            description=req.description,
            visibility=req.visibility,
        )
        if not proj:
            raise ProjectNotFoundError(str(project_id))

        resp = ProjectResponse.model_validate(proj)
        resp.current_user_role = role
        return resp

    def delete_project(self, user: User, project_id: uuid.UUID) -> None:
        """Delete/archive project. Owner only."""
        proj = self.workspace_repo.get(project_id)
        if not proj:
            raise ProjectNotFoundError(str(project_id))
        if proj.owner_user_id != user.id:
            raise ForbiddenError("Only the project owner can delete this project.")

        self.workspace_repo.delete(project_id)

    def list_project_games(self, user: User, project_id: uuid.UUID) -> list[ProjectGameItem]:
        """List games selected in a research project."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        games = self.workspace_repo.list_project_games(project_id)
        return [
            ProjectGameItem(
                project_id=pg.project_id,
                game_id=pg.game_id,
                added_at=pg.added_at,
            )
            for pg in games
        ]

    def add_game_to_project(
        self, user: User, project_id: uuid.UUID, game_id: uuid.UUID
    ) -> ProjectGameItem:
        """Add game to project workspace."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can add games.")

        game = self.session.get(Game, game_id)
        if not game:
            raise GameNotFoundError(str(game_id))

        pg = self.workspace_repo.add_game(project_id=project_id, game_id=game_id, user_id=user.id)
        return ProjectGameItem(
            project_id=pg.project_id,
            game_id=pg.game_id,
            added_at=pg.added_at,
        )

    def remove_game_from_project(
        self, user: User, project_id: uuid.UUID, game_id: uuid.UUID
    ) -> None:
        """Remove game from project workspace."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can remove games.")

        removed = self.workspace_repo.remove_game(project_id, game_id)
        if not removed:
            raise GameNotFoundError(str(game_id))

    def list_saved_analyses(self, user: User, project_id: uuid.UUID) -> list[SavedAnalysisResponse]:
        """List saved analyses within a project workspace."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        items = self.workspace_repo.list_saved_analyses(project_id)
        return [SavedAnalysisResponse.model_validate(a) for a in items]

    def create_saved_analysis(
        self, user: User, project_id: uuid.UUID, req: SavedAnalysisCreateRequest
    ) -> SavedAnalysisResponse:
        """Save a new analysis configuration."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can create analyses.")

        analysis = self.workspace_repo.create_saved_analysis(
            project_id=project_id,
            created_by_user_id=user.id,
            name=req.name,
            description=req.description,
            analysis_type=req.analysis_type,
            query_config=req.query_config,
        )
        return SavedAnalysisResponse.model_validate(analysis)

    def get_saved_analysis(
        self, user: User, project_id: uuid.UUID, analysis_id: uuid.UUID
    ) -> SavedAnalysisResponse:
        """Fetch saved analysis configuration."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        analysis = self.workspace_repo.get_saved_analysis(analysis_id)
        if not analysis or analysis.project_id != project_id:
            raise AnalysisNotFoundError(str(analysis_id))

        return SavedAnalysisResponse.model_validate(analysis)

    def update_saved_analysis(
        self,
        user: User,
        project_id: uuid.UUID,
        analysis_id: uuid.UUID,
        req: SavedAnalysisUpdateRequest,
    ) -> SavedAnalysisResponse:
        """Update saved analysis configuration."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can update analyses.")

        analysis = self.workspace_repo.get_saved_analysis(analysis_id)
        if not analysis or analysis.project_id != project_id:
            raise AnalysisNotFoundError(str(analysis_id))

        updated = self.workspace_repo.update_saved_analysis(
            analysis_id=analysis_id,
            name=req.name,
            description=req.description,
            query_config=req.query_config,
        )
        assert updated is not None
        return SavedAnalysisResponse.model_validate(updated)

    def delete_saved_analysis(
        self, user: User, project_id: uuid.UUID, analysis_id: uuid.UUID
    ) -> None:
        """Delete saved analysis."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can delete analyses.")

        analysis = self.workspace_repo.get_saved_analysis(analysis_id)
        if not analysis or analysis.project_id != project_id:
            raise AnalysisNotFoundError(str(analysis_id))

        self.workspace_repo.delete_saved_analysis(analysis_id)

    def create_snapshot(
        self,
        user: User,
        project_id: uuid.UUID,
        analysis_id: uuid.UUID,
        req: SnapshotCreateRequest,
    ) -> AnalysisSnapshotResponse:
        """Create immutable reproducibility snapshot for analysis."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role not in ["owner", "editor"]:
            raise ForbiddenError("Only project owners or editors can create snapshots.")

        analysis = self.workspace_repo.get_saved_analysis(analysis_id)
        if not analysis or analysis.project_id != project_id:
            raise AnalysisNotFoundError(str(analysis_id))

        snapshot = self.workspace_repo.create_snapshot(
            saved_analysis_id=analysis_id,
            name=req.name,
            description=req.description,
            configuration_snapshot=analysis.query_config,
            result_summary={"analysis_name": analysis.name, "captured_by": str(user.id)},
        )
        return AnalysisSnapshotResponse(
            id=snapshot.id,
            saved_analysis_id=snapshot.saved_analysis_id,
            name=req.name,
            description=req.description,
            configuration_snapshot=snapshot.filter_snapshot,
            result_summary=snapshot.result_summary,
            data_cutoff_at=snapshot.data_cutoff_at,
            created_at=snapshot.created_at,
        )

    def list_snapshots(
        self, user: User, project_id: uuid.UUID, analysis_id: uuid.UUID
    ) -> list[AnalysisSnapshotResponse]:
        """List snapshots for a saved analysis."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        analysis = self.workspace_repo.get_saved_analysis(analysis_id)
        if not analysis or analysis.project_id != project_id:
            raise AnalysisNotFoundError(str(analysis_id))

        snapshots = self.workspace_repo.list_snapshots(analysis_id)
        return [
            AnalysisSnapshotResponse(
                id=s.id,
                saved_analysis_id=s.saved_analysis_id,
                name=f"Snapshot #{s.snapshot_number}",
                description=None,
                configuration_snapshot=s.filter_snapshot,
                result_summary=s.result_summary,
                data_cutoff_at=s.data_cutoff_at,
                created_at=s.created_at,
            )
            for s in snapshots
        ]

    def get_snapshot(
        self,
        user: User,
        project_id: uuid.UUID,
        analysis_id: uuid.UUID,
        snapshot_id: uuid.UUID,
    ) -> AnalysisSnapshotResponse:
        """Fetch a single snapshot by ID ensuring project membership."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        analysis = self.workspace_repo.get_saved_analysis(analysis_id)
        if not analysis or analysis.project_id != project_id:
            raise AnalysisNotFoundError(str(analysis_id))

        snapshot = self.workspace_repo.get_snapshot(snapshot_id)
        if not snapshot or snapshot.saved_analysis_id != analysis_id:
            raise ResourceNotFoundError(f"Snapshot '{snapshot_id}' was not found.")

        return AnalysisSnapshotResponse(
            id=snapshot.id,
            saved_analysis_id=snapshot.saved_analysis_id,
            name=f"Snapshot #{snapshot.snapshot_number}",
            description=None,
            configuration_snapshot=snapshot.filter_snapshot,
            result_summary=snapshot.result_summary,
            data_cutoff_at=snapshot.data_cutoff_at,
            created_at=snapshot.created_at,
        )

    def list_project_members(
        self, user: User, project_id: uuid.UUID
    ) -> list[ProjectMemberItem]:
        """List collaborators in a research project."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if not role:
            raise ProjectNotFoundError(str(project_id))

        proj = self.workspace_repo.get(project_id)
        if not proj:
            raise ProjectNotFoundError(str(project_id))

        members = self.workspace_repo.list_project_members(project_id)
        items: list[ProjectMemberItem] = []

        # Add project owner
        owner = self.user_repo.get(proj.owner_user_id)
        items.append(
            ProjectMemberItem(
                project_id=proj.id,
                user_id=proj.owner_user_id,
                project_role="owner",
                joined_at=proj.created_at,
                email=owner.email if owner else None,
                display_name=owner.display_name if owner else "Project Owner",
            )
        )

        for m in members:
            if m.user_id == proj.owner_user_id:
                continue
            u = self.user_repo.get(m.user_id)
            items.append(
                ProjectMemberItem(
                    project_id=m.project_id,
                    user_id=m.user_id,
                    project_role=m.project_role,
                    joined_at=m.joined_at,
                    email=u.email if u else None,
                    display_name=u.display_name if u else "Collaborator",
                )
            )

        return items

    def add_project_member(
        self, user: User, project_id: uuid.UUID, req: ProjectAddMemberRequest
    ) -> ProjectMemberItem:
        """Add or invite a member to a research project. Enforces owner-only permission."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        if role != "owner":
            raise ForbiddenError("Only the project owner can invite or add members.")

        target_user: User | None = None
        if req.user_id:
            target_user = self.user_repo.get(req.user_id)
        elif req.email:
            target_user = self.user_repo.get_by_email(req.email)

        if not target_user:
            identifier = str(req.user_id or req.email)
            raise UserNotFoundError(identifier)

        proj = self.workspace_repo.get(project_id)
        if not proj:
            raise ProjectNotFoundError(str(project_id))

        if target_user.id == proj.owner_user_id:
            raise ForbiddenError("Owner already has full management privileges.")

        member = self.workspace_repo.add_project_member(
            project_id=project_id,
            user_id=target_user.id,
            project_role=req.project_role,
            invited_by_user_id=user.id,
        )

        return ProjectMemberItem(
            project_id=member.project_id,
            user_id=member.user_id,
            project_role=member.project_role,
            joined_at=member.joined_at,
            email=target_user.email,
            display_name=target_user.display_name,
        )

    def remove_project_member(
        self, user: User, project_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> None:
        """Remove a member collaborator from the project."""
        role = self.workspace_repo.get_user_project_role(project_id, user.id)
        proj = self.workspace_repo.get(project_id)
        if not proj:
            raise ProjectNotFoundError(str(project_id))

        if role != "owner" and user.id != target_user_id:
            raise ForbiddenError("Only project owners can remove other members.")

        if target_user_id == proj.owner_user_id:
            raise ForbiddenError("The project owner cannot be removed from the project.")

        removed = self.workspace_repo.remove_project_member(project_id, target_user_id)
        if not removed:
            raise UserNotFoundError(str(target_user_id))
