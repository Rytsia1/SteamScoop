"""FastAPI dependency injection providers for repositories, domain services, security,
and correlation IDs.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.workspace import User
from app.repositories.analytics import AnalyticsRepository
from app.repositories.aspect import AspectRepository
from app.repositories.export import ExportRepository
from app.repositories.game import GameRepository
from app.repositories.ingestion import IngestionJobRepository
from app.repositories.pipeline_run import PipelineRunRepository
from app.repositories.review import ReviewRepository
from app.repositories.sentiment import SentimentRepository
from app.repositories.topic import TopicRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.services.admin_service import AdminService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.comparison_service import ComparisonService
from app.services.export_service import ExportService
from app.services.game_service import GameService
from app.services.methodology_service import MethodologyService
from app.services.review_service import ReviewService
from app.services.workspace_service import WorkspaceService


# Repositories
def get_game_repository(db: Session = Depends(get_db)) -> GameRepository:
    """Dependency provider for GameRepository."""
    return GameRepository(db)


def get_review_repository(db: Session = Depends(get_db)) -> ReviewRepository:
    """Dependency provider for ReviewRepository."""
    return ReviewRepository(db)


def get_analytics_repository(db: Session = Depends(get_db)) -> AnalyticsRepository:
    """Dependency provider for AnalyticsRepository."""
    return AnalyticsRepository(db)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency provider for UserRepository."""
    return UserRepository(db)


def get_workspace_repository(db: Session = Depends(get_db)) -> WorkspaceRepository:
    """Dependency provider for WorkspaceRepository."""
    return WorkspaceRepository(db)


def get_export_repository(db: Session = Depends(get_db)) -> ExportRepository:
    """Dependency provider for ExportRepository."""
    return ExportRepository(db)


def get_ingestion_job_repository(db: Session = Depends(get_db)) -> IngestionJobRepository:
    """Dependency provider for IngestionJobRepository."""
    return IngestionJobRepository(db)


def get_pipeline_run_repository(db: Session = Depends(get_db)) -> PipelineRunRepository:
    """Dependency provider for PipelineRunRepository."""
    return PipelineRunRepository(db)


# Domain Services
def get_game_service(
    game_repo: GameRepository = Depends(get_game_repository),
) -> GameService:
    """Dependency provider for GameService."""
    return GameService(game_repo=game_repo)


def get_review_service(
    game_repo: GameRepository = Depends(get_game_repository),
    review_repo: ReviewRepository = Depends(get_review_repository),
) -> ReviewService:
    """Dependency provider for ReviewService."""
    return ReviewService(game_repo=game_repo, review_repo=review_repo)


def get_analytics_service(
    db: Session = Depends(get_db),
    analytics_repo: AnalyticsRepository = Depends(get_analytics_repository),
    review_repo: ReviewRepository = Depends(get_review_repository),
) -> AnalyticsService:
    """Dependency provider for AnalyticsService."""
    return AnalyticsService(
        session=db,
        analytics_repo=analytics_repo,
        review_repo=review_repo,
        sentiment_repo=SentimentRepository(db),
        aspect_repo=AspectRepository(db),
        topic_repo=TopicRepository(db),
    )


def get_methodology_service(db: Session = Depends(get_db)) -> MethodologyService:
    """Dependency provider for MethodologyService."""
    return MethodologyService(session=db)


def get_comparison_service(
    db: Session = Depends(get_db),
) -> ComparisonService:
    """Dependency provider for ComparisonService."""
    return ComparisonService(session=db)


def get_auth_service(
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService(session=db, user_repo=user_repo)


def get_workspace_service(
    db: Session = Depends(get_db),
    workspace_repo: WorkspaceRepository = Depends(get_workspace_repository),
) -> WorkspaceService:
    """Dependency provider for WorkspaceService."""
    return WorkspaceService(session=db, workspace_repo=workspace_repo)


def get_export_service(
    db: Session = Depends(get_db),
    export_repo: ExportRepository = Depends(get_export_repository),
    game_repo: GameRepository = Depends(get_game_repository),
    review_repo: ReviewRepository = Depends(get_review_repository),
) -> ExportService:
    """Dependency provider for ExportService."""
    return ExportService(
        session=db,
        export_repo=export_repo,
        game_repo=game_repo,
        review_repo=review_repo,
    )


def get_admin_service(
    db: Session = Depends(get_db),
    game_repo: GameRepository = Depends(get_game_repository),
    ingestion_job_repo: IngestionJobRepository = Depends(get_ingestion_job_repository),
    pipeline_run_repo: PipelineRunRepository = Depends(get_pipeline_run_repository),
) -> AdminService:
    """Dependency provider for AdminService."""
    return AdminService(
        session=db,
        game_repo=game_repo,
        ingestion_job_repo=ingestion_job_repo,
        pipeline_run_repo=pipeline_run_repo,
    )


# Context and Security Dependencies
def get_request_id(request: Request) -> str:
    """Extract or generate request correlation ID from request state."""
    return getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"


def _extract_token(request: Request) -> str | None:
    """Extract bearer token from Authorization header or session_token cookie."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    return request.cookies.get("session_token")


def get_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Authenticate request using bearer token or session cookie."""
    token = _extract_token(request)
    if not token:
        raise UnauthorizedError(
            message="Authentication credentials were not provided.",
            code="UNAUTHENTICATED",
        )

    user = auth_service.get_user_from_token(token)
    if not user:
        raise UnauthorizedError(
            message="Invalid or expired authentication session.",
            code="UNAUTHENTICATED",
        )

    return user


def get_current_active_user(
    user: User = Depends(get_current_user),
) -> User:
    """Validate authenticated user is active."""
    if user.status != "active":
        raise UnauthorizedError(
            message="Account is inactive or suspended.",
            code="ACCOUNT_INACTIVE",
        )
    return user


def get_optional_current_user(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User | None:
    """Attempt optional authentication for public routes."""
    token = _extract_token(request)
    if not token:
        return None
    try:
        return auth_service.get_user_from_token(token)
    except Exception:
        return None


def require_role(role_name: str) -> Callable[..., Any]:
    """Dependency factory checking that authenticated user possesses the required role."""

    def role_checker(
        user: User = Depends(get_current_active_user),
        user_repo: UserRepository = Depends(get_user_repository),
    ) -> User:
        roles = user_repo.get_user_roles(user.id)
        if role_name not in roles and "admin" not in roles:
            raise ForbiddenError(
                message=f"Operation requires '{role_name}' permissions.",
                code="FORBIDDEN",
            )
        return user

    return role_checker
