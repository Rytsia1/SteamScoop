"""Administrative operations for catalog curation, ingestion orchestration, and model activation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.deps import get_admin_service, get_request_id, require_role
from app.models.workspace import User
from app.schemas.admin import (
    AdminGameCreateRequest,
    AdminGameResponse,
    AdminGameUpdateRequest,
    AdminIngestionJobCreateRequest,
    AdminIngestionJobResponse,
    AdminModelActivateResponse,
    AdminModelResponse,
    AdminPipelineRunResponse,
)
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.services.admin_service import AdminService

router = APIRouter()


# Game Catalog
@router.get(
    "/admin/games",
    response_model=ResponseEnvelope[list[AdminGameResponse]],
    summary="List Controlled Catalog Games",
    description="Retrieve managed catalog games and their indexing states.",
)
async def list_admin_games(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[AdminGameResponse]]:
    games = admin_service.list_catalog_games(limit=limit, offset=offset)
    data = [AdminGameResponse.model_validate(g) for g in games]
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[AdminGameResponse]](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/admin/games",
    response_model=ResponseEnvelope[AdminGameResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Game to Managed Catalog",
    description="Add a new game to the platform catalog by official Steam App ID.",
)
async def create_admin_game(
    request: AdminGameCreateRequest,
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminGameResponse]:
    game = admin_service.create_catalog_game(request)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminGameResponse](
        data=AdminGameResponse.model_validate(game),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.patch(
    "/admin/games/{game_id}",
    response_model=ResponseEnvelope[AdminGameResponse],
    summary="Update Managed Catalog Game",
    description="Update metadata, catalog indexing state, or active status.",
)
async def update_admin_game(
    request: AdminGameUpdateRequest,
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminGameResponse]:
    game = admin_service.update_catalog_game(game_id, request)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminGameResponse](
        data=AdminGameResponse.model_validate(game),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


# Ingestion Jobs
@router.post(
    "/admin/games/{game_id}/ingestion-jobs",
    response_model=ResponseEnvelope[AdminIngestionJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue Historical or Incremental Review Ingestion",
    description="Queue an ingestion job for a target game. Fails with 409 if active job exists.",
)
async def queue_ingestion_job(
    request: AdminIngestionJobCreateRequest,
    game_id: uuid.UUID = Path(..., description="Target game UUID"),
    admin_user: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminIngestionJobResponse]:
    job = admin_service.queue_ingestion_job(game_id, request, user_id=admin_user.id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminIngestionJobResponse](
        data=AdminIngestionJobResponse.from_model(job),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/admin/ingestion-jobs",
    response_model=ResponseEnvelope[list[AdminIngestionJobResponse]],
    summary="List Ingestion Jobs",
    description="Retrieve collection jobs filtered by game, job type, or execution status.",
)
async def list_ingestion_jobs(
    game_id: uuid.UUID | None = Query(default=None),
    job_type: str | None = Query(default=None),
    job_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[AdminIngestionJobResponse]]:
    jobs = admin_service.list_ingestion_jobs(
        game_id=game_id, job_type=job_type, status=job_status, limit=limit
    )
    data = [AdminIngestionJobResponse.from_model(j) for j in jobs]
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[AdminIngestionJobResponse]](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/admin/ingestion-jobs/{job_id}",
    response_model=ResponseEnvelope[AdminIngestionJobResponse],
    summary="Get Ingestion Job Details",
    description="Retrieve execution details, review counters, and timestamps for an ingestion job.",
)
async def get_ingestion_job(
    job_id: uuid.UUID = Path(..., description="Ingestion job UUID"),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminIngestionJobResponse]:
    job = admin_service.get_ingestion_job(job_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminIngestionJobResponse](
        data=AdminIngestionJobResponse.from_model(job),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/admin/ingestion-jobs/{job_id}/retry",
    response_model=ResponseEnvelope[AdminIngestionJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry Ingestion Job",
    description="Enqueue a retry for a failed or cancelled collection job.",
)
async def retry_ingestion_job(
    job_id: uuid.UUID = Path(..., description="Ingestion job UUID"),
    admin_user: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminIngestionJobResponse]:
    retry_job = admin_service.retry_ingestion_job(job_id, user_id=admin_user.id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminIngestionJobResponse](
        data=AdminIngestionJobResponse.from_model(retry_job),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/admin/ingestion-jobs/{job_id}/cancel",
    response_model=ResponseEnvelope[AdminIngestionJobResponse],
    summary="Cancel Ingestion Job",
    description="Cancel a running or queued collection job.",
)
async def cancel_ingestion_job(
    job_id: uuid.UUID = Path(..., description="Ingestion job UUID"),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminIngestionJobResponse]:
    job = admin_service.cancel_ingestion_job(job_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminIngestionJobResponse](
        data=AdminIngestionJobResponse.from_model(job),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


# ML Pipeline Runs
@router.get(
    "/admin/pipeline-runs",
    response_model=ResponseEnvelope[list[AdminPipelineRunResponse]],
    summary="List ML Pipeline Runs",
    description="Retrieve diagnostic metrics and status for ML batch inference runs.",
)
async def list_pipeline_runs(
    pipeline_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[AdminPipelineRunResponse]]:
    runs = admin_service.list_pipeline_runs(pipeline_type=pipeline_type, limit=limit)
    data = [AdminPipelineRunResponse.from_model(r) for r in runs]
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[AdminPipelineRunResponse]](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/admin/pipeline-runs/{run_id}",
    response_model=ResponseEnvelope[AdminPipelineRunResponse],
    summary="Get ML Pipeline Run Details",
    description=(
        "Retrieve execution details, failure counts, and metrics for a specific pipeline execution."
    ),
)
async def get_pipeline_run(
    run_id: uuid.UUID = Path(..., description="Pipeline run UUID"),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminPipelineRunResponse]:
    run = admin_service.get_pipeline_run(run_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[AdminPipelineRunResponse](
        data=AdminPipelineRunResponse.from_model(run),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


# ML Models
@router.get(
    "/admin/models",
    response_model=ResponseEnvelope[list[AdminModelResponse]],
    summary="List Registered ML Models",
    description="Retrieve all registered ML models and their active flags.",
)
async def list_models(
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[AdminModelResponse]]:
    models = admin_service.list_models()
    data = [AdminModelResponse.model_validate(m) for m in models]
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[AdminModelResponse]](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.post(
    "/admin/models/{model_id}/activate",
    response_model=ResponseEnvelope[AdminModelActivateResponse],
    summary="Activate Approved Model Version",
    description="Atomically set this model active for its task and deactivate previous versions.",
)
async def activate_model(
    model_id: uuid.UUID = Path(..., description="Target model UUID"),
    _admin: User = Depends(require_role("admin")),
    admin_service: AdminService = Depends(get_admin_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[AdminModelActivateResponse]:
    model = admin_service.activate_model(model_id)
    now_utc = datetime.now(UTC).isoformat()
    msg = (
        f"Model version '{model.version}' ({model.model_key}) "
        f"successfully activated for task '{model.task}'."
    )

    return ResponseEnvelope[AdminModelActivateResponse](
        data=AdminModelActivateResponse(
            model_id=model.id,
            task=model.task,
            is_active=model.is_active,
            message=msg,
        ),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )
