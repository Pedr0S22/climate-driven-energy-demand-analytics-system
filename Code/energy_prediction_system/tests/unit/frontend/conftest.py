import os
import pytest
from unittest.mock import patch

# Mock environment variables needed for the Frontend (ex: SessionManager)
os.environ["KEYRING_SERVICE_NAME"] = "energy_pred_test_service"
os.environ["KEYRING_TOKEN_KEY"] = "test_token"
os.environ["KEYRING_ROLE_KEY"] = "test_role"

@pytest.fixture(autouse=True)
def mock_keyring():
    """
    Global fixture to mock the OS keyring for ALL frontend tests.
    This safely prevents CI/CD pipelines from hanging to ask for OS keychain passwords.
    """
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

    with patch('app.manager.session_manager.keyring.set_password', side_effect=mock_set_password), \
         patch('app.manager.session_manager.keyring.get_password', side_effect=mock_get_password), \
         patch('app.manager.session_manager.keyring.delete_password', side_effect=mock_delete_password):
        yield fake_keyring


@pytest.fixture
def mock_api_response():
    """
    A factory fixture that mocks 'requests.post' globally.
    Allows tests to easily simulate any HTTP code and JSON payload.
    """
    with patch('requests.post') as mock_post:
        def _create_response(status_code, json_data):
            mock_post.return_value.status_code = status_code
            mock_post.return_value.json.return_value = json_data
            return mock_post
        yield _create_response


@pytest.fixture
def mock_api_200(mock_api_response):
    """Global fixture: Simulates a successful 200 OK response."""
    return mock_api_response(status_code=200, json_data={"access_token": "fake_token", "role": "admin"})


@pytest.fixture
def mock_api_400(mock_api_response):
    """Global fixture: Simulates a 400 Bad Request validation error."""
    return mock_api_response(status_code=400, json_data={"detail": "Invalid Request format."})


@pytest.fixture
def mock_api_401(mock_api_response):
    """Global fixture: Simulates a 401 Unauthorized invalid credentials error."""
    return mock_api_response(status_code=401, json_data={"detail": "Incorrect credentials."})


@pytest.fixture
def mock_api_403(mock_api_response):
    """Global fixture: Simulates a 403 Forbidden account lockout error."""
    return mock_api_response(status_code=403, json_data={"detail": "Account locked or access denied."})


@pytest.fixture
def mock_api_409(mock_api_response):
    """Global fixture: Simulates a 409 Conflict duplicate email error."""
    return mock_api_response(status_code=409, json_data={"detail": "Email already registered."})


@pytest.fixture
def mock_api_500(mock_api_response):
    """Global fixture: Simulates a 500 Internal Server error."""
    return mock_api_response(status_code=500, json_data={"detail": "Internal Server Error"})
