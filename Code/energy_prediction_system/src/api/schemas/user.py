from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    account_regist_date: datetime
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    status: int
    message: str
    timestamp: datetime


class TokenPayload(BaseModel):
    sub: str | None = None


class LogoutResponse(BaseModel):
    status: int
    message: str
    user_id: int
    timestamp: datetime
