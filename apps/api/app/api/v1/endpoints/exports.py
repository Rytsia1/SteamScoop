"""Endpoints for asynchronous data exports and artifact retrieval."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path, Response, status

from app.api.deps import (
    get_current_active_user,
    get_export_service,
    get_request_id,
    get_user_repository,
)
from app.models.workspace import User
from app.repositories.user import UserRepository
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.schemas.export import ExportCreateRequest, ExportResponseData
from app.services.export_service import ExportService

router = APIRouter()


@router.post(
    "/exports",
    response_model=ResponseEnvelope[ExportResponseData],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue Asynchronous Data Export",
    description=(
        "Enqueue an asynchronous data export job in CSV, JSON, or XLSX format "
        "for reviews or analytics."
    ),
)
async def create_export(
    request: ExportCreateRequest,
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
    export_service: ExportService = Depends(get_export_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ExportResponseData]:
    roles = user_repo.get_user_roles(current_user.id)
    job_data = export_service.create_export(
        user=current_user, request=request, user_roles=roles
    )
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ExportResponseData](
        data=job_data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/exports/{export_id}",
    response_model=ResponseEnvelope[ExportResponseData],
    summary="Check Export Job Status",
    description="Retrieve execution status, row counts, and expiration metadata for an export job.",
)
async def get_export(
    export_id: uuid.UUID = Path(..., description="Export job UUID"),
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
    export_service: ExportService = Depends(get_export_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ExportResponseData]:
    roles = user_repo.get_user_roles(current_user.id)
    job_data = export_service.get_export(user=current_user, export_id=export_id, user_roles=roles)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ExportResponseData](
        data=job_data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/exports/{export_id}/download",
    summary="Download Completed Export Artifact",
    description=(
        "Stream the completed analytical dataset artifact. Returns 410 if artifact has expired."
    ),
)
async def download_export(
    export_id: uuid.UUID = Path(..., description="Export job UUID"),
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    roles = user_repo.get_user_roles(current_user.id)
    filename, media_type, content = export_service.download_export(
        user=current_user, export_id=export_id, user_roles=roles
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/exports/{export_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel Export Job",
    description="Cancel a queued or running export job.",
)
async def cancel_export(
    export_id: uuid.UUID = Path(..., description="Export job UUID"),
    current_user: User = Depends(get_current_active_user),
    user_repo: UserRepository = Depends(get_user_repository),
    export_service: ExportService = Depends(get_export_service),
) -> Response:
    roles = user_repo.get_user_roles(current_user.id)
    export_service.cancel_export(user=current_user, export_id=export_id, user_roles=roles)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
