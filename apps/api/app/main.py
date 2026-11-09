import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.schemas.common import ErrorDetail, ErrorInfo, MetaEnvelope, ResponseEnvelope

logger = logging.getLogger("steamscoop.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL, json_format=(settings.APP_ENV == "production"))
    logger.info(
        "Starting %s v%s in [%s] mode",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG or settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.DEBUG or settings.APP_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.DEBUG or settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # Middleware: Request Correlation ID
    @app.middleware("http")
    async def request_correlation_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        incoming_id = request.headers.get("X-Request-ID")
        # Validate or generate safe request ID
        if (
            incoming_id
            and incoming_id.replace("-", "").replace("_", "").isalnum()
            and len(incoming_id) <= 64
        ):
            request_id = incoming_id
        else:
            request_id = f"req_{uuid.uuid4().hex[:12]}"

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Middleware: CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Global Exception Handler: Validation Errors
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
        now_utc = datetime.now(UTC).isoformat()

        details = [
            ErrorDetail(
                field=" -> ".join(str(loc) for loc in err.get("loc", [])),
                issue=err.get("msg", "Validation error"),
            )
            for err in exc.errors()
        ]

        error_envelope = ResponseEnvelope[None](
            data=None,
            error=ErrorInfo(
                code="VALIDATION_ERROR",
                message="The request parameters or body failed schema validation.",
                details=details,
                request_id=request_id,
            ),
            meta=MetaEnvelope(request_id=request_id, timestamp=now_utc),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_envelope.model_dump(),
        )

    # Global Exception Handler: Unhandled Exceptions
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
        now_utc = datetime.now(UTC).isoformat()

        logger.exception("Unhandled server error [request_id=%s]: %s", request_id, str(exc))

        error_envelope = ResponseEnvelope[None](
            data=None,
            error=ErrorInfo(
                code="INTERNAL_ERROR",
                message="An unexpected internal server error occurred. Please try again later.",
                details=None,
                request_id=request_id,
            ),
            meta=MetaEnvelope(request_id=request_id, timestamp=now_utc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_envelope.model_dump(),
        )

    # Root probe health endpoint for container orchestrators
    @app.get("/health", include_in_schema=False)
    async def root_health() -> dict[str, str]:
        return {"status": "ok"}

    # Include Versioned API Routes
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_application()
