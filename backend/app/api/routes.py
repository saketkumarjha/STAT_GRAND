from fastapi import APIRouter
from app.api.endpoints import search, occupations, analytics

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    search.router,
    prefix="/search",
    tags=["search"]
)

api_router.include_router(
    occupations.router,
    prefix="/occupations",
    tags=["occupations"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)