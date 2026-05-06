from fastapi import APIRouter

from src.api.routers.endpoints import users, models

api_router = APIRouter()
api_router.include_router(users.router, prefix="/auth", tags=["auth"])

api_router.include_router(models.router, prefix="/models", tags=["Model Management"])