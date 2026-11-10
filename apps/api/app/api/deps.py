import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.analytics import AnalyticsRepository
from app.repositories.aspect import AspectRepository
from app.repositories.game import GameRepository
from app.repositories.review import ReviewRepository
from app.repositories.sentiment import SentimentRepository
from app.repositories.topic import TopicRepository
from app.services.analytics_service import AnalyticsService
from app.services.game_service import GameService
from app.services.review_service import ReviewService


def get_game_repository(db: Session = Depends(get_db)) -> GameRepository:
    """Dependency provider for GameRepository."""
    return GameRepository(db)


def get_review_repository(db: Session = Depends(get_db)) -> ReviewRepository:
    """Dependency provider for ReviewRepository."""
    return ReviewRepository(db)


def get_analytics_repository(db: Session = Depends(get_db)) -> AnalyticsRepository:
    """Dependency provider for AnalyticsRepository."""
    return AnalyticsRepository(db)


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


def get_request_id(request: Request) -> str:
    """Extract or generate request correlation ID from request state."""
    return getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex[:12]}"
