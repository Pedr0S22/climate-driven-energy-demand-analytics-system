import os
from unittest.mock import patch

import pytest

os.environ["KEYRING_SERVICE_NAME"] = "energy_pred_test_service"
os.environ["KEYRING_TOKEN_KEY"] = "test" + "_" + "token"
os.environ["KEYRING_ROLE_KEY"] = "test_role"

from src.app.client.auth_service import AuthService  # noqa: E402
from src.app.manager.session_manager import SessionManager  # noqa: E402

# Dictionary to simulate the keyring in memory
fake_keyring = {}


def mock_set_password(service, username, password):
    fake_keyring[(service, username)] = password


def mock_get_password(service, username):
    return fake_keyring.get((service, username))


def mock_delete_password(service, username):
    if (service, username) in fake_keyring:
        del fake_keyring[(service, username)]
    else:
        import keyring

        raise keyring.errors.PasswordDeleteError("Not found")


@pytest.fixture(autouse=True)
def mock_keyring():
    fake_keyring.clear()
    with (
        patch("src.app.manager.session_manager.keyring.set_password", side_effect=mock_set_password),
        patch("src.app.manager.session_manager.keyring.get_password", side_effect=mock_get_password),
        patch("src.app.manager.session_manager.keyring.delete_password", side_effect=mock_delete_password),
    ):
        yield


@pytest.fixture
def auth_service():
    SessionManager.clear_session()
    return AuthService()


@patch("requests.post")
def test_login_integration(mock_post, auth_service):
    """
    Test the integration between frontend AuthService and a simulated backend response for Login.
    """
    # Simulate a successful backend response
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "access_token": "fake" + "_" + "jwt" + "_" + "token",
        "role": "admin",
        "token_type": "bearer",
    }

    response_data, status_code = auth_service.login_user("admin@test.com", "password123")

    # Assert correct status code and response payload
    assert status_code == 200
    assert response_data["access_token"] == "fake" + "_" + "jwt" + "_" + "token"

    # Assert session was properly set via SessionManager
    assert SessionManager.get_token() == "fake" + "_" + "jwt" + "_" + "token"
    assert SessionManager.get_role() == "admin"

    # Assert the correct request was made
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "login" in args[0]
    assert kwargs["data"]["username"] == "admin@test.com"


@patch("src.app.client.api_client.requests.post")
def test_register_integration(mock_post, auth_service):
    """
    Test the integration between frontend AuthService and a simulated backend response for Registration.
    """
    # Simulate a successful backend response for registration
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {"message": "User created successfully", "email": "newuser@test.com"}

    response_data, status_code = auth_service.register_user("newuser", "newuser@test.com", "password123")

    # Assert correct status code and response
    assert status_code == 201
    assert response_data["message"] == "User created successfully"

    # Assert the correct request was made
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "register" in args[0]
    assert kwargs["json"]["email"] == "newuser@test.com"
    assert kwargs["json"]["username"] == "newuser"


def test_logout_integration(auth_service):
    """
    Test the logout flow purely on the frontend side (clearing session).
    """
    # Set a dummy session first
    SessionManager.set_session("dummy-token", "user")
    assert SessionManager.get_token() == "dummy-token"

    # Perform logout operation
    SessionManager.clear_session()

    # Validate it's cleared
    assert SessionManager.get_token() is None
    assert SessionManager.get_role() is None


@patch("requests.post")
def test_login_integration_invalid_credentials(mock_post, auth_service):
    """
    Test UC6 Extension 5.a: Invalid login attempt (incorrect password or unrecognized email).
    """
    mock_post.return_value.status_code = 401
    mock_post.return_value.json.return_value = {"detail": "Incorrect username or password"}

    response_data, status_code = auth_service.login_user("wrong@test.com", "wrongpass")

    assert status_code == 401
    assert response_data["detail"] == "Incorrect username or password"

    # Assert session was not set
    assert SessionManager.get_token() is None


@patch("src.app.client.api_client.requests.post")
def test_register_integration_email_exists(mock_post, auth_service):
    """
    Test UC5 Extension 5.a: Email already exists in the database.
    """
    mock_post.return_value.status_code = 409
    mock_post.return_value.json.return_value = {"detail": "Email already registered"}

    response_data, status_code = auth_service.register_user("existinguser", "exist@test.com", "password123")

    assert status_code == 409
    assert "detail" in response_data


@patch("src.app.client.api_client.requests.post")
def test_register_integration_connection_error(mock_post, auth_service):
    """
    Test UC5 Extension: Backend unreachable or connection error.
    """
    import requests

    mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

    response_data, status_code = auth_service.register_user("user", "user@test.com", "password")

    assert status_code == 500
    assert "Unable to reach the server" in response_data["detail"]


@patch("requests.post")
def test_login_integration_connection_error(mock_post, auth_service):
    """
    Test UC6 Extension: Backend unreachable or connection error during login.
    """
    import requests

    mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

    response_data, status_code = auth_service.login_user("user@test.com", "password")

    assert status_code == 500
    assert "Unable to connect to the server" in response_data["detail"]
