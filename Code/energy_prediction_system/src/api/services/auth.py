import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.config import settings
from src.api.core.security import get_password_hash, verify_password
from src.api.models.user import Admin, Client, User
from src.api.schemas.user import UserCreate, UserLogin

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate, is_admin: bool = False):
    # Check for duplicate email
    if get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Hash password
    hashed_password = get_password_hash(user_in.password)

    # Create User
    db_user = User(email=user_in.email, username=user_in.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create Role record
    if is_admin:
        role_record = Admin(users_id=db_user.id)
    else:
        role_record = Client(users_id=db_user.id)

    db.add(role_record)
    db.commit()

    return db_user


def authenticate_user(db: Session, login_data: UserLogin):
    user = get_user_by_email(db, login_data.email)

    # QA10: Generic message for all failures
    generic_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        raise generic_exception

    # Brute Force Protection (QA13)
    now = datetime.now(UTC)
    if user.acc_locked_until and user.acc_locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account locked due to multiple failed attempts. Please try again later.",
        )

    if not verify_password(login_data.password, user.password):
        # Increment failed attempts
        user.failed_login_att += 1
        user.last_failed_att = now

        if user.failed_login_att > settings.MAX_FAILED_ATTEMPTS:
            user.acc_locked_until = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to multiple failed attempts. Please try again later.",
            )

        db.commit()
        raise generic_exception

    # Reset failed attempts on success
    user.failed_login_att = 0
    user.acc_locked_until = None
    db.commit()

    return user


def get_user_role(db: Session, user_id: int) -> str:
    if db.query(Admin).filter(Admin.users_id == user_id).first():
        return "admin"
    return "client"
