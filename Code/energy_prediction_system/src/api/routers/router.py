from fastapi import APIRouter

from src.api.routers.endpoints import users

api_router = APIRouter()
api_router.include_router(users.router, prefix="/auth", tags=["auth"])
