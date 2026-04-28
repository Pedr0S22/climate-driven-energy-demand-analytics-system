import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.api.core.security import create_access_token, get_current_user, require_role
from src.api.database.session import get_db
from src.api.models.user import User
from src.api.schemas.user import LogoutResponse, Token, UserCreate, UserLogin, UserResponse
from src.api.services import auth as auth_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = auth_service.get_user_role(db, current_user.id)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "account_regist_date": current_user.account_regist_date,
        "role": role,
    }


@router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
def admin_only():
    return {"message": "Welcome, Admin!"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    user = auth_service.create_user(db, user_in)
    return {
        "status": 201,
        "message": "User registered successfully",
        "user_id": user.id,
        "timestamp": datetime.now(UTC),
    }


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, login_data)
    role = auth_service.get_user_role(db, user.id)
    access_token = create_access_token(subject=user.email)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "status": 200,
        "message": "User logged successfully",
        "timestamp": datetime.now(UTC),
    }


@router.post("/logout", response_model=LogoutResponse)
def logout(current_user: User = Depends(get_current_user)):
    # In a stateless JWT system, logout is mostly client-side (discard token).
    # Here we log the event for security auditing.
    logger.info(f"User {current_user.email} logged out")
    return {
        "status": 200,
        "message": "Successfully logged out",
        "user_id": current_user.id,
        "timestamp": datetime.now(UTC),
    }
