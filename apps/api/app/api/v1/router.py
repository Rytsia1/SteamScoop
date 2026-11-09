from fastapi import APIRouter

from app.api.v1.endpoints import games, health, reviews

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["System"])
api_v1_router.include_router(games.router, tags=["Games"])
api_v1_router.include_router(reviews.router, tags=["Reviews"])
