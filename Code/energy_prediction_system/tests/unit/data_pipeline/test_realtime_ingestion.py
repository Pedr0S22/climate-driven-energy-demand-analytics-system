from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from data_pipeline.ingestion import fetch_realtime_energy_load, fetch_realtime_weather


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ENTSOE_API_KEY", "fake_api_key")


@patch("data_pipeline.ingestion.EntsoePandasClient")
@patch("data_pipeline.ingestion.os.replace")
@patch("data_pipeline.ingestion.pd.DataFrame.to_csv")
def test_fetch_realtime_energy_load_success(
        mock_to_csv,
        mock_replace,
        mock_entsoe_client,
        mock_env_vars):
    """Verify that fetch_realtime_energy_load correctly handles raw data from ENTSO-E."""
    mock_client_instance = MagicMock()
    mock_entsoe_client.return_value = mock_client_instance

    # Mock return data
    data = {"Actual Load": [100.0, 105.0]}
    df = pd.DataFrame(
        data,
        index=pd.date_range(
            "2026-05-13",
            periods=2,
            freq="h"))
    mock_client_instance.query_load.return_value = df

    fetch_realtime_energy_load(days=1)

    mock_client_instance.query_load.assert_called_once()
    mock_replace.assert_called_once()
    # Verify it renamed columns if needed (it does in the code)


@patch("data_pipeline.ingestion.requests.get")
@patch("data_pipeline.ingestion.os.replace")
def test_fetch_realtime_weather_success(mock_replace, mock_get):
    """Verify that fetch_realtime_weather correctly handles raw data from Open-Meteo."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "hourly": {
            "time": ["2026-05-13T00:00", "2026-05-13T01:00"],
            "temperature_2m": [15.0, 16.0],
            "dew_point_2m": [10.0, 11.0],
            "surface_pressure": [1013.0, 1012.0],
            "precipitation": [0.0, 0.1],
            "shortwave_radiation": [0.0, 100.0],
            "terrestrial_radiation": [300.0, 310.0],
            "skin_temperature": [14.0, 15.0],
            "soil_temperature_0_to_7cm": [13.0, 13.5],
            "soil_moisture_0_to_7cm": [0.2, 0.21],
            "wind_speed_10m": [2.0, 2.5],
            "wind_direction_10m": [180, 190],
        }
    }
    mock_get.return_value = mock_response

    # We need to mock pd.DataFrame.to_csv to avoid writing to disk
    with patch("pandas.DataFrame.to_csv") as mock_to_csv:  # noqa F841
        fetch_realtime_weather(days=1)

    mock_get.assert_called_once()
    mock_replace.assert_called_once()


@patch("data_pipeline.ingestion.requests.get")
def test_fetch_realtime_weather_error_handling(mock_get):
    """Verify fetch_realtime_weather handles API errors (e.g., 500)."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception(
        "Internal Server Error")
    mock_get.return_value = mock_response

    # Should not crash, just log error and potentially retry (we mock 1 attempt or just the failure)
    # The code has a retry loop, so we might want to mock MAX_RETRIES failures
    mock_get.side_effect = [mock_response] * 3

    fetch_realtime_weather(days=1)
    assert mock_get.call_count == 3
