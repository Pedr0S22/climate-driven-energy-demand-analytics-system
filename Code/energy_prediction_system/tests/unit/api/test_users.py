from src.api.core.config import settings


def test_register_user(client):
    response = client.post(
        "/api/auth/register", json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User registered successfully"
    assert "user_id" in data


def test_register_duplicate_email(client):
    user_data = {"username": "user1", "email": "dup@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 409
    assert response.json()["message"] == "Email already registered"


def test_login_success(client):
    user_data = {"username": "loginuser", "email": "login@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)

    response = client.post("/api/auth/login", json={"email": "login@example.com", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "client"


def test_login_invalid_credentials(client):
    user_data = {"username": "wrongpass", "email": "wrong@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)

    response = client.post("/api/auth/login", json={"email": "wrong@example.com", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid credentials"


def test_login_lockout(client):
    user_data = {"username": "lockuser", "email": "lock@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)

    # Fail 3 times (settings.MAX_FAILED_ATTEMPTS)
    for _ in range(settings.MAX_FAILED_ATTEMPTS):
        response = client.post("/api/auth/login", json={"email": "lock@example.com", "password": "wrongpassword"})
        assert response.status_code == 401

    # 4th attempt should be locked (QA13)
    response = client.post("/api/auth/login", json={"email": "lock@example.com", "password": "wrongpassword"})
    assert response.status_code == 403
    assert "Account locked" in response.json()["message"]


def test_logout(client):
    user_data = {"username": "logoutuser", "email": "logout@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)
    login_resp = client.post("/api/auth/login", json={"email": "logout@example.com", "password": "password123"})
    token = login_resp.json()["access_token"]

    response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
    assert "user_id" in response.json()


def test_get_me(client):
    user_data = {"username": "meuser", "email": "me@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)
    login_resp = client.post("/api/auth/login", json={"email": "me@example.com", "password": "password123"})
    token = login_resp.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
    assert response.json()["role"] == "client"


def test_rbac_client_access_admin_denied(client):
    user_data = {"username": "clientuser", "email": "client@example.com", "password": "password123"}
    client.post("/api/auth/register", json=user_data)
    login_resp = client.post("/api/auth/login", json={"email": "client@example.com", "password": "password123"})
    token = login_resp.json()["access_token"]

    response = client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["message"] == "Insufficient privileges"


def test_rbac_admin_access_allowed(client, db):
    from src.api.schemas.user import UserCreate
    from src.api.services.auth import create_user

    # Manually create an admin user
    admin_in = UserCreate(username="adminuser", email="admin@example.com", password="password123")
    create_user(db, admin_in, is_admin=True)

    login_resp = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "password123"})
    token = login_resp.json()["access_token"]

    response = client.get("/api/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome, Admin!"


def test_validation_error(client):
    # Password too short
    response = client.post(
        "/api/auth/register", json={"username": "test", "email": "test@example.com", "password": "short"}
    )
    assert response.status_code == 400
    assert response.json()["message"] == "Validation Error"
