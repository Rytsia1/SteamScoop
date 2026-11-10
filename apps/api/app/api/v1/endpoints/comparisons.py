"""Public API endpoint for multi-game analytical comparisons."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from app.api.deps import get_comparison_service, get_request_id
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.schemas.comparison import ComparisonRequest, ComparisonResponseData
from app.services.comparison_service import ComparisonService

router = APIRouter()


@router.post(
    "/comparisons",
    response_model=ResponseEnvelope[ComparisonResponseData],
    summary="Compare Multiple Games Across Analytical Metrics",
    description=(
        "Executes a bounded, read-only analytical comparison across 2 to 5 indexed games. "
        "Allows metric allowlisting (sentiment, aspects, topics, volume) and temporal alignment."
    ),
)
async def compare_games(
    request: ComparisonRequest,
    comparison_service: ComparisonService = Depends(get_comparison_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ComparisonResponseData]:
    data = comparison_service.compare_games(request)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ComparisonResponseData](
        data=data,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )

