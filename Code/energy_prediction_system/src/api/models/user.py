from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from src.api.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    account_regist_date = Column(DateTime(timezone=True), server_default=func.now())

    # Brute Force Protection (QA13)
    failed_login_att = Column(Integer, default=0)
    acc_locked_until = Column(DateTime(timezone=True), nullable=True)
    last_failed_att = Column(DateTime(timezone=True), nullable=True)


class Admin(Base):
    __tablename__ = "admin"

    users_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)


class Client(Base):
    __tablename__ = "client"

    users_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
