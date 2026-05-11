from datetime import UTC

from fastapi import APIRouter

from src.api.routers.endpoints import models, simulations, users

UTC = UTC

api_router = APIRouter()

api_router.include_router(users.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(models.router, prefix="/models", tags=["Model Management"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["Simulations"])
