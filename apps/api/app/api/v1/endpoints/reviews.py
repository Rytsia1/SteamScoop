import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Path

from app.api.deps import get_request_id, get_review_service
from app.schemas.common import MetaEnvelope, ResponseEnvelope
from app.schemas.review import ReviewDetail
from app.services.review_service import ReviewService

router = APIRouter()


@router.get(
    "/reviews/{review_id}",
    response_model=ResponseEnvelope[ReviewDetail],
    summary="Get Review Details",
    description=(
        "Retrieve approved public details for an individual review, "
        "including attached sentiment prediction."
    ),
)
async def get_review(
    review_id: uuid.UUID = Path(..., description="Unique internal review UUID"),
    review_service: ReviewService = Depends(get_review_service),
    request_id: str = Depends(get_request_id),
) -> ResponseEnvelope[ReviewDetail]:
    review = review_service.get_review(review_id)
    now_utc = datetime.now(UTC).isoformat()

    return ResponseEnvelope[ReviewDetail](
        data=review,
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )
