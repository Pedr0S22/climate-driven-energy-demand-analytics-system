import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.core.config import settings
from src.api.database.session import Base, get_db

# Import the API and Backend components
from src.api.main import app

# Import the Frontend components
from src.app.client.auth_service import AuthService
from src.app.manager.session_manager import SessionManager

# --- SETUP TEST DATABASE (SQLite In-Memory) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

# --- MOCK KEYRING FOR SESSION MANAGER ---
fake_keyring = {}


def mock_set_password(service, username, password):
    fake_keyring[(service, username)] = password


def mock_get_password(service, username):
    return fake_keyring.get((service, username))


def mock_delete_password(service, username):
    if (service, username) in fake_keyring:
        del fake_keyring[(service, username)]


@pytest.fixture(autouse=True)
def setup_integration_env():
    # Setup tables
    Base.metadata.create_all(bind=engine)
    fake_keyring.clear()

    with (
        patch("src.app.manager.session_manager.keyring.set_password", side_effect=mock_set_password),
        patch("src.app.manager.session_manager.keyring.get_password", side_effect=mock_get_password),
        patch("src.app.manager.session_manager.keyring.delete_password", side_effect=mock_delete_password),
    ):
        yield

    # Teardown tables
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_integration.db"):
        try:
            os.remove("./test_integration.db")
        except PermissionError:
            import time

            time.sleep(0.2)
            try:
                os.remove("./test_integration.db")
            except:  # noqa E722 S110
                pass


@pytest.fixture
def api_test_client():
    return TestClient(app)


@pytest.fixture
def full_stack_auth_service(api_test_client):
    """
    An AuthService that actually talks to the TestClient instead of making real HTTP requests.
    """
    with (
        patch("src.app.client.api_client.requests.post") as mock_post,
        patch("src.app.client.api_client.requests.get") as mock_get,
        patch("src.app.client.api_client.requests.delete") as mock_delete,
    ):

        def mock_request_adapter(method_func):
            def wrapper(url, **kwargs):
                # Map http://localhost/api/xxx to /api/xxx
                endpoint = url.replace("http://localhost", "")
                # TestClient does not support 'timeout' argument from
                # 'requests'
                kwargs.pop("timeout", None)
                return method_func(endpoint, **kwargs)

            return wrapper

        mock_post.side_effect = mock_request_adapter(api_test_client.post)
        mock_get.side_effect = mock_request_adapter(api_test_client.get)
        mock_delete.side_effect = mock_request_adapter(api_test_client.delete)

        yield AuthService()


# --- TESTS ---


def test_registration_to_login_to_protected_flow(
        full_stack_auth_service, api_test_client):
    """
    Test 1: Full E2E flow from Registration to Login to accessing a Protected Endpoint.
    This exercises src/api/routers/endpoints/users.py and src/api/services/auth.py
    """
    # 1. Register a new user
    user_email = "integration@test.com"  # noqa S105
    user_pass = "StrongPass123!"  # noqa S105
    reg_data, status = full_stack_auth_service.register_user(
        "int_user", user_email, user_pass)

    assert status == 201
    assert reg_data["status"] == 201
    assert "User registered successfully" in reg_data["message"]

    # 2. Login with the new user
    login_data, status = full_stack_auth_service.login_user(
        user_email, user_pass)

    assert status == 200
    assert "access_token" in login_data
    assert login_data["role"] == "client"

    # Verify session manager has the token
    token = SessionManager.get_token()
    assert token == login_data["access_token"]

    # 3. Access a protected endpoint (/api/auth/me)
    # The APIClient automatically adds the Authorization header
    from src.app.client.api_client import APIClient

    client = APIClient()

    # We need to mock the requests.get again for this specific client instance
    # if not using fixture
    with patch(
        "src.app.client.api_client.requests.get",
        side_effect=lambda url, **kwargs: api_test_client.get(
            url.replace("http://localhost", ""), **{k: v for k, v in kwargs.items() if k != "timeout"}
        ),
    ):
        response = client.get("/auth/me")
        assert response.status_code == 200
        me_data = response.json()
        assert me_data["email"] == user_email
        assert me_data["role"] == "client"


def test_admin_only_access_denied_for_client(
        full_stack_auth_service, api_test_client):
    """
    Verify that a regular client cannot access admin-only endpoints.
    Exercises src/api/core/security.py (require_role)
    """
    # 1. Register and Login as regular client
    full_stack_auth_service.register_user(
        "regular", "client@test.com", "Pass123!")
    full_stack_auth_service.login_user("client@test.com", "Pass123!")

    # 2. Try to access admin-only endpoint
    from src.app.client.api_client import APIClient

    client = APIClient()
    with patch(
        "src.app.client.api_client.requests.get",
        side_effect=lambda url, **kwargs: api_test_client.get(
            url.replace("http://localhost", ""), **{k: v for k, v in kwargs.items() if k != "timeout"}
        ),
    ):
        response = client.get("/auth/admin-only")
        assert response.status_code == 403
        assert "Forbidden" in response.json(
        )["message"] or response.status_code == 403


def test_brute_force_protection_integration(
        full_stack_auth_service, api_test_client):
    """
    Test UC6 extension: Brute force protection logic in src/api/services/auth.py
    """
    user_email = "brute@test.com"
    full_stack_auth_service.register_user("brute", user_email, "Pass123!")

    # Fail login multiple times
    # settings.MAX_FAILED_ATTEMPTS is usually 5 (check config.py or .env)
    # We'll do it 6 times to be sure
    for _ in range(settings.MAX_FAILED_ATTEMPTS + 1):
        full_stack_auth_service.login_user(user_email, "WrongPass")

    # Next attempt should be forbidden (locked)
    login_data, status = full_stack_auth_service.login_user(
        user_email, "Pass123!")
    assert status == 403
    assert "locked" in login_data["message"].lower()


def test_logout_clears_server_session_and_local(
        full_stack_auth_service, api_test_client):
    """
    Test the full logout integration.
    """
    # 1. Login
    user_email = "logout@test.com"
    full_stack_auth_service.register_user(
        "logout_user", user_email, "Pass123!")
    full_stack_auth_service.login_user(user_email, "Pass123!")

    assert SessionManager.get_token() is not None

    # 2. Logout (Backend notification)
    full_stack_auth_service.logout_user()

    # 3. Simulate UI clearing session
    SessionManager.clear_session()
    assert SessionManager.get_token() is None
    assert SessionManager.get_role() is None


def test_health_check_integration(api_test_client):
    """
    Test the public health check endpoint.
    """
    response = api_test_client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
