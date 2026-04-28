import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variables for testing before importing src modules
os.environ["SECRET_KEY"] = "TEST_SECRET_KEY_REPLACE_ME"  # noqa: S105
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MAX_FAILED_ATTEMPTS"] = "3"
os.environ["LOCKOUT_DURATION_MINUTES"] = "5"

from src.api.database.session import Base, get_db  # noqa: E402
from src.api.main import app  # noqa: E402

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
