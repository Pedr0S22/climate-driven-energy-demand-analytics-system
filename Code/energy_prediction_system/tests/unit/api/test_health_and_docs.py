from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint returns 200 and correct structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "1.0.1"


def test_swagger_ui_accessible():
    """Test that Swagger UI is accessible at the new path."""
    response = client.get("/api/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_openapi_json_accessible():
    """Test that OpenAPI JSON is accessible at the new path."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "Climate-Driven Energy Demand Analytics System"


def test_redoc_accessible():
    """Test that ReDoc is accessible at the new path."""
    response = client.get("/api/redoc")
    assert response.status_code == 200
    assert "redoc" in response.text.lower()
