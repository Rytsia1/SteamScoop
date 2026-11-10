"""Master router aggregating all API v1 endpoint modules."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    auth,
    comparisons,
    exports,
    games,
    health,
    methodology,
    reviews,
    workspaces,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["System"])
api_v1_router.include_router(methodology.router, tags=["Methodology"])
api_v1_router.include_router(games.router, tags=["Games"])
api_v1_router.include_router(reviews.router, tags=["Reviews"])
api_v1_router.include_router(analytics.router, tags=["Analytics"])
api_v1_router.include_router(comparisons.router, tags=["Comparisons"])
api_v1_router.include_router(auth.router, tags=["Authentication"])
api_v1_router.include_router(workspaces.router, tags=["Workspaces"])
api_v1_router.include_router(exports.router, tags=["Exports"])
api_v1_router.include_router(admin.router, tags=["Administration"])
