import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response, status

from app.core.config import get_settings
from app.core.redis import check_redis_connection
from app.db.session import check_database_connection
from app.schemas.common import (
    DependencyStatus,
    ErrorInfo,
    HealthData,
    MetaEnvelope,
    ResponseEnvelope,
)

router = APIRouter()


@router.get(
    "/health",
    response_model=ResponseEnvelope[HealthData],
    summary="System Health & Subsystem Status",
    description=(
        "Returns service availability, application version, environment, and dependency statuses."
    ),
)
async def check_health(request: Request) -> ResponseEnvelope[HealthData]:
    settings = get_settings()
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"
    now_utc = datetime.now(UTC).isoformat()

    db_ok = check_database_connection()
    redis_ok = check_redis_connection()

    overall_status = "healthy" if (db_ok and redis_ok) else "degraded"

    return ResponseEnvelope[HealthData](
        data=HealthData(
            status=overall_status,
            version=settings.APP_VERSION,
            app_env=settings.APP_ENV,
            timestamp=now_utc,
            dependencies=DependencyStatus(
                database="connected" if db_ok else "unreachable",
                redis="connected" if redis_ok else "unreachable",
            ),
        ),
        error=None,
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )


@router.get(
    "/health/liveness",
    summary="Liveness Probe",
    description="Lightweight liveness check for container orchestrators.",
)
async def liveness_probe() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/health/readiness",
    response_model=ResponseEnvelope[HealthData],
    summary="Readiness Probe",
    description="Readiness check verifying that database and redis dependencies are operational.",
)
async def readiness_probe(request: Request, response: Response) -> ResponseEnvelope[HealthData]:
    settings = get_settings()
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"
    now_utc = datetime.now(UTC).isoformat()

    db_ok = check_database_connection()
    redis_ok = check_redis_connection()

    is_ready = db_ok and redis_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ResponseEnvelope[HealthData](
        data=HealthData(
            status="healthy" if is_ready else "unhealthy",
            version=settings.APP_VERSION,
            app_env=settings.APP_ENV,
            timestamp=now_utc,
            dependencies=DependencyStatus(
                database="connected" if db_ok else "unreachable",
                redis="connected" if redis_ok else "unreachable",
            ),
        ),
        error=None
        if is_ready
        else ErrorInfo(
            code="SERVICE_UNAVAILABLE",
            message="Required service dependencies (database or redis) are unreachable.",
            request_id=request_id,
        ),
        meta=MetaEnvelope(
            request_id=request_id,
            timestamp=now_utc,
        ),
    )
