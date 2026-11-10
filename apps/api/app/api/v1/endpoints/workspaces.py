"""Research workspace endpoints for projects, game selections, saved analyses, and snapshots."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.api.deps import (
    get_current_active_user,
    get_request_id,
    get_workspace_service,
)
from app.models.workspace import User
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.schemas.workspace import (
    ProjectAddGameRequest,
    ProjectCreateRequest,
    ProjectGameItem,
    ProjectResponse,
    ProjectUpdateRequest,
    SavedAnalysisCreateRequest,
    SavedAnalysisResponse,
    SavedAnalysisUpdateRequest,
    SnapshotCreateRequest,
    SnapshotResponse,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter()


# Projects CRUD
@router.get(
    "/projects",
    response_model=ResponseEnvelope[list[ProjectResponse]],
    summary="List Research Workspace Projects",
    description="Retrieve all projects owned by or shared with the authenticated researcher.",
)
async def list_projects(
    limit: int = Query(default=20, ge=1, le=100, description="Page limit"),
    cursor: str | None = Query(default=None, description="Pagination cursor"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[ProjectResponse]]:
    items, pagination = workspace_service.list_projects(
        user=current_user, limit=limit, cursor=cursor
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[ProjectResponse]](
        data=items,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
            pagination=pagination,
        ),
    )


@router.post(
    "/projects",
    response_model=ResponseEnvelope[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Research Project Workspace",
    description="Initialize a new private or shared research workspace project.",
)
async def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ProjectResponse]:
    proj = workspace_service.create_project(user=current_user, req=request)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ProjectResponse](
        data=proj,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/projects/{project_id}",
    response_model=ResponseEnvelope[ProjectResponse],
    summary="Get Research Project Details",
    description=(
        "Retrieve project workspace configuration. Enforces object-level authorization "
        "(returns 404 if private)."
    ),
)
async def get_project(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ProjectResponse]:
    proj = workspace_service.get_project(user=current_user, project_id=project_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ProjectResponse](
        data=proj,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.patch(
    "/projects/{project_id}",
    response_model=ResponseEnvelope[ProjectResponse],
    summary="Update Research Project",
    description=(
        "Update project name, description, or visibility setting. Requires owner or editor role."
    ),
)
async def update_project(
    request: ProjectUpdateRequest,
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ProjectResponse]:
    proj = workspace_service.update_project(user=current_user, project_id=project_id, req=request)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ProjectResponse](
        data=proj,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Research Project",
    description="Permanently remove research project workspace. Owner only.",
)
async def delete_project(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Response:
    workspace_service.delete_project(user=current_user, project_id=project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Project Games Association
@router.get(
    "/projects/{project_id}/games",
    response_model=ResponseEnvelope[list[ProjectGameItem]],
    summary="List Games in Project Workspace",
    description="Retrieve all games added to the specified research project.",
)
async def list_project_games(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[ProjectGameItem]]:
    items = workspace_service.list_project_games(user=current_user, project_id=project_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[ProjectGameItem]](
        data=items,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/projects/{project_id}/games",
    response_model=ResponseEnvelope[ProjectGameItem],
    summary="Add Game to Project Workspace",
    description="Associate an indexed game with a project workspace. Idempotent operation.",
)
async def add_game_to_project(
    request: ProjectAddGameRequest,
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ProjectGameItem]:
    item = workspace_service.add_game_to_project(
        user=current_user, project_id=project_id, game_id=request.game_id
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ProjectGameItem](
        data=item,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.delete(
    "/projects/{project_id}/games/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Game from Project Workspace",
    description="Disassociate a game from the specified research project.",
)
async def remove_game_from_project(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Response:
    workspace_service.remove_game_from_project(
        user=current_user, project_id=project_id, game_id=game_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Saved Analyses
@router.get(
    "/projects/{project_id}/analyses",
    response_model=ResponseEnvelope[list[SavedAnalysisResponse]],
    summary="List Saved Analyses in Project",
    description="Retrieve saved analysis queries within a project workspace.",
)
async def list_saved_analyses(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[SavedAnalysisResponse]]:
    items = workspace_service.list_saved_analyses(user=current_user, project_id=project_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[SavedAnalysisResponse]](
        data=items,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/projects/{project_id}/analyses",
    response_model=ResponseEnvelope[SavedAnalysisResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Saved Analysis",
    description="Save a structured analysis query configuration under a project.",
)
async def create_saved_analysis(
    request: SavedAnalysisCreateRequest,
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[SavedAnalysisResponse]:
    analysis = workspace_service.create_saved_analysis(
        user=current_user, project_id=project_id, req=request
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[SavedAnalysisResponse](
        data=analysis,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/projects/{project_id}/analyses/{analysis_id}",
    response_model=ResponseEnvelope[SavedAnalysisResponse],
    summary="Get Saved Analysis Details",
    description="Retrieve configuration and parameters of a saved analysis.",
)
async def get_saved_analysis(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    analysis_id: uuid.UUID = Path(..., description="Saved analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[SavedAnalysisResponse]:
    analysis = workspace_service.get_saved_analysis(
        user=current_user, project_id=project_id, analysis_id=analysis_id
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[SavedAnalysisResponse](
        data=analysis,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.patch(
    "/projects/{project_id}/analyses/{analysis_id}",
    response_model=ResponseEnvelope[SavedAnalysisResponse],
    summary="Update Saved Analysis",
    description="Modify parameters or metadata of a saved analysis query.",
)
async def update_saved_analysis(
    request: SavedAnalysisUpdateRequest,
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    analysis_id: uuid.UUID = Path(..., description="Saved analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[SavedAnalysisResponse]:
    analysis = workspace_service.update_saved_analysis(
        user=current_user, project_id=project_id, analysis_id=analysis_id, req=request
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[SavedAnalysisResponse](
        data=analysis,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.delete(
    "/projects/{project_id}/analyses/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Saved Analysis",
    description="Remove saved analysis configuration from project.",
)
async def delete_saved_analysis(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    analysis_id: uuid.UUID = Path(..., description="Saved analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
) -> Response:
    workspace_service.delete_saved_analysis(
        user=current_user, project_id=project_id, analysis_id=analysis_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Snapshots
@router.post(
    "/projects/{project_id}/analyses/{analysis_id}/snapshots",
    response_model=ResponseEnvelope[SnapshotResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Analysis Reproducibility Snapshot",
    description=(
        "Freeze current analytical filters, dataset cutoff watermark, and model parameters "
        "into an immutable snapshot."
    ),
)
async def create_snapshot(
    request: SnapshotCreateRequest,
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    analysis_id: uuid.UUID = Path(..., description="Saved analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[SnapshotResponse]:
    snapshot = workspace_service.create_snapshot(
        user=current_user, project_id=project_id, analysis_id=analysis_id, req=request
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[SnapshotResponse](
        data=snapshot,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/projects/{project_id}/analyses/{analysis_id}/snapshots",
    response_model=ResponseEnvelope[list[SnapshotResponse]],
    summary="List Analysis Snapshots",
    description="Retrieve all immutable reproducibility snapshots captured for a saved analysis.",
)
async def list_snapshots(
    project_id: uuid.UUID = Path(..., description="Project workspace UUID"),
    analysis_id: uuid.UUID = Path(..., description="Saved analysis UUID"),
    current_user: User = Depends(get_current_active_user),
    workspace_service: WorkspaceService = Depends(get_workspace_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[SnapshotResponse]]:
    snapshots = workspace_service.list_snapshots(
        user=current_user, project_id=project_id, analysis_id=analysis_id
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[SnapshotResponse]](
        data=snapshots,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )
