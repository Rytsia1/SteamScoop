"""Public API endpoints for analytical methodology, model cards, and dataset documentation."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.api.deps import get_methodology_service, get_request_id
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.schemas.methodology import DatasetDocumentationItem, MethodologyResponse, ModelCardItem
from app.services.methodology_service import MethodologyService

router = APIRouter()


@router.get(
    "/methodology",
    response_model=ResponseEnvelope[MethodologyResponse],
    summary="Get Platform Methodology and Data Policies",
    description=(
        "Retrieve formal data collection policies, analytical definitions, "
        "and operational metric formulas."
    ),
)
async def get_methodology(
    methodology_service: MethodologyService = Depends(get_methodology_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[MethodologyResponse]:
    data = methodology_service.get_methodology()
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[MethodologyResponse](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/methodology/models",
    response_model=ResponseEnvelope[list[ModelCardItem]],
    summary="List Published ML Model Cards",
    description=(
        "Retrieve published model cards, task descriptions, training corpora, "
        "and evaluation metrics."
    ),
)
async def list_model_cards(
    methodology_service: MethodologyService = Depends(get_methodology_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[ModelCardItem]]:
    data = methodology_service.get_model_cards()
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[ModelCardItem]](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/methodology/datasets",
    response_model=ResponseEnvelope[list[DatasetDocumentationItem]],
    summary="List Dataset Documentation and Provenance",
    description=(
        "Retrieve dataset provenance, versioning manifests, split ratios, "
        "and licensing information."
    ),
)
async def list_datasets(
    methodology_service: MethodologyService = Depends(get_methodology_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[list[DatasetDocumentationItem]]:
    data = methodology_service.get_datasets()
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[list[DatasetDocumentationItem]](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )
