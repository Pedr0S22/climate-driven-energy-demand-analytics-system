from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.core.security import get_current_user
from src.api.main import app

client = TestClient(app)


# Use dependency overrides for cleaner mocking of authentication
def get_mock_user():
    return MagicMock(email="test@example.com")


@patch("src.api.routers.endpoints.predictions.PredictionService.get_realtime_prediction")
def test_get_hourly_prediction_api(mock_get_prediction):
    """Test GET /api/predictions/hourly endpoint."""
    app.dependency_overrides[get_current_user] = get_mock_user

    # Mock service response
    mock_get_prediction.return_value = {
        "status": 200,
        "historical_load": [100.0, 101.0, 102.0],
        "load_predicted": [103.0, 104.0],
        "timestamps": [
            "2026-05-13T10:00:00Z",
            "2026-05-13T11:00:00Z",
            "2026-05-13T12:00:00Z",
            "2026-05-13T13:00:00Z",
            "2026-05-13T14:00:00Z",
        ],
        "top2_drivers": ["t2m", "hour"],
    }

    response = client.get(
        "/api/predictions/hourly?historical_points=3&predicted_points=2",
        headers={
            "Authorization": "Bearer fake_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["load_predicted"] == [103.0, 104.0]

    # Cleanup
    app.dependency_overrides.clear()


@patch("src.api.routers.endpoints.predictions.PredictionService.get_realtime_prediction")
def test_get_daily_prediction_api(mock_get_prediction):
    """Test GET /api/predictions/daily endpoint."""
    app.dependency_overrides[get_current_user] = get_mock_user

    mock_get_prediction.return_value = {
        "status": 200,
        "historical_load": [
            1000.0,
            1010.0,
            1020.0],
        "load_predicted": [
            1030.0,
            1040.0],
        "timestamps": [
            "2026-05-11",
            "2026-05-12",
            "2026-05-13",
            "2026-05-14",
            "2026-05-15"],
        "top2_drivers": [
            "t2m",
            "day_of_week"],
    }

    response = client.get(
        "/api/predictions/daily?historical_points=3&predicted_points=2",
        headers={
            "Authorization": "Bearer fake_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["load_predicted"] == [1030.0, 1040.0]

    app.dependency_overrides.clear()


def test_prediction_api_unauthorized():
    """Verify that predictions require authentication."""
    # Ensure overrides are clear
    app.dependency_overrides.clear()

    response = client.get("/api/predictions/hourly")
    assert response.status_code == 401  # Unauthorized
