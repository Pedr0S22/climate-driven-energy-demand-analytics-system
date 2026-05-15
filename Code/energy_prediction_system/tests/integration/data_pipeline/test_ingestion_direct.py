import io
import os
import zipfile
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest
from data_pipeline.cleaning import cleaning
from data_pipeline.ingestion import (
    data_retrieval,
    fetch_copernicus_data,
    fetch_entsoe_data,
    fetch_realtime_energy_load,
    fetch_realtime_weather,
)


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("ENTSOE_API_KEY", "fake_key")


def test_fetch_copernicus_data_success_path(tmp_path, monkeypatch):
    # Setup paths to use tmp_path
    raw_weather_dir = tmp_path / "data" / "raw" / "weather"
    raw_weather_dir.mkdir(parents=True, exist_ok=True)

    # Surgically mock os.path functions within the ingestion module only
    original_abspath = os.path.abspath
    monkeypatch.setattr("data_pipeline.ingestion.os.path.abspath", lambda x: str(
        tmp_path) if "ingestion.py" in str(x) or ".." in str(x) else original_abspath(x), )

    with patch("cdsapi.Client") as mock_cds:
        mock_client = MagicMock()
        mock_cds.return_value = mock_client

        # Create a fake zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            cols = [
                "valid_time",
                "t2m",
                "d2m",
                "skt",
                "stl1",
                "u10",
                "v10",
                "ssrd",
                "strd",
                "sp",
                "tp",
                "swvl1",
                "latitude",
                "longitude",
            ]
            data = [
                "2024-01-01 00:00:00",
                280.0,
                275.0,
                280.0,
                280.0,
                1.0,
                1.0,
                100.0,
                300.0,
                101300.0,
                0.0,
                0.3,
                40.4,
                -3.7,
            ]
            zip_file.writestr("test_weather.csv", ",".join(
                cols) + "\n" + ",".join(map(str, data)))

        def mock_download(path):
            with open(path, "wb") as f:
                f.write(zip_buffer.getvalue())

        mock_client.retrieve.return_value.download.side_effect = mock_download

        # Fix recursion in os.path.exists mock
        original_exists = os.path.exists

        def side_effect(p):
            if str(p).endswith(".zip"):
                return False
            return original_exists(p)

        with patch("data_pipeline.ingestion.os.path.exists", side_effect=side_effect):
            fetch_copernicus_data("2024-01-01", "2024-01-01")

    # Check if the file was created
    output_files = list(raw_weather_dir.glob("era5_timeseries_*.csv"))
    assert len(output_files) > 0


def test_fetch_entsoe_data_success_path(tmp_path, monkeypatch, mock_env):
    raw_energy_dir = tmp_path / "data" / "raw" / "energy"
    raw_energy_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("data_pipeline.ingestion.os.path.abspath", lambda x: str(
        tmp_path) if "ingestion.py" in str(x) or ".." in str(x) else x, )

    with patch("data_pipeline.ingestion.EntsoePandasClient") as mock_entsoe:
        mock_client = MagicMock()
        mock_entsoe.return_value = mock_client

        df = pd.DataFrame({"Load_MW": [1000.0]}, index=pd.date_range(
            "2024-01-01", periods=1, freq="h", tz="Europe/Madrid"))
        mock_client.query_load.return_value = df

        fetch_entsoe_data("2024-01-01", "2024-01-01")

    output_files = list(raw_energy_dir.glob("entsoe_ES_load_*.csv"))
    assert len(output_files) > 0


def test_fetch_realtime_energy_load_variants(tmp_path, monkeypatch, mock_env):
    raw_energy_dir = tmp_path / "data" / "raw" / "energy"
    raw_energy_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("data_pipeline.ingestion.os.path.abspath", lambda x: str(
        tmp_path) if "ingestion.py" in str(x) or ".." in str(x) else x, )

    with patch("data_pipeline.ingestion.EntsoePandasClient") as mock_entsoe:
        mock_client = MagicMock()
        mock_entsoe.return_value = mock_client

        # Variant 1: "Actual Load" column
        df1 = pd.DataFrame({"Actual Load": [1000.0]}, index=pd.date_range(
            "2024-01-01", periods=1, freq="h", tz="Europe/Madrid"))
        mock_client.query_load.return_value = df1
        fetch_realtime_energy_load(days=1)
        assert (raw_energy_dir / "realtime_load.csv").exists()

        # Variant 2: Single column without "Actual Load"
        df2 = pd.DataFrame({"Some Other Name": [2000.0]}, index=pd.date_range(
            "2024-01-01", periods=1, freq="h", tz="Europe/Madrid"))
        mock_client.query_load.return_value = df2
        fetch_realtime_energy_load(days=1)

        # Variant 3: Series
        series = pd.Series(
            [3000.0],
            index=pd.date_range(
                "2024-01-01",
                periods=1,
                freq="h",
                tz="Europe/Madrid"),
            name="Load")
        mock_client.query_load.return_value = series
        fetch_realtime_energy_load(days=1)


def test_fetch_realtime_weather_success_path(tmp_path, monkeypatch):
    raw_weather_dir = tmp_path / "data" / "raw" / "weather"
    raw_weather_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("data_pipeline.ingestion.os.path.abspath", lambda x: str(
        tmp_path) if "ingestion.py" in str(x) or ".." in str(x) else x, )

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2024-01-01T00:00"],
                "temperature_2m": [15.0],
                "dew_point_2m": [10.0],
                "surface_pressure": [1013.0],
                "precipitation": [0.0],
                "shortwave_radiation": [0.0],
                "terrestrial_radiation": [300.0],
                "skin_temperature": [14.0],
                "soil_temperature_0_to_7cm": [13.0],
                "soil_moisture_0_to_7cm": [0.2],
                "wind_speed_10m": [2.0],
                "wind_direction_10m": [180],
            }
        }
        mock_get.return_value = mock_response

        fetch_realtime_weather(days=1)
        assert (raw_weather_dir / "realtime_weather.csv").exists()


def test_ingestion_error_paths(mock_env, monkeypatch):
    # Invalid dates
    with pytest.raises(ValueError):
        fetch_copernicus_data("2024-01-02", "2024-01-01")
    with pytest.raises(ValueError):
        fetch_entsoe_data("2024-01-02", "2024-01-01")

    # No API Key
    monkeypatch.delenv("ENTSOE_API_KEY", raising=False)
    with patch("logging.error") as mock_log:
        fetch_entsoe_data("2024-01-01", "2024-01-01")
        assert any("ENTSOE_API_KEY not found" in str(call)
                   for call in mock_log.call_args_list)

    with patch("logging.error") as mock_log:
        fetch_realtime_energy_load(days=1)
        assert any("ENTSOE_API_KEY not found" in str(call)
                   for call in mock_log.call_args_list)


def test_ingestion_to_cleaning_flow(tmp_path, monkeypatch, mock_env):
    # Set up mock project structure
    project_root = tmp_path
    (project_root / "data" / "raw" / "energy").mkdir(parents=True)
    (project_root / "data" / "raw" / "weather").mkdir(parents=True)
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True)

    monkeypatch.setattr("data_pipeline.ingestion.os.path.abspath", lambda x: str(
        tmp_path) if "ingestion.py" in str(x) or ".." in str(x) else x, )
    monkeypatch.setattr("data_pipeline.cleaning.os.path.abspath", lambda x: str(
        tmp_path) if "cleaning.py" in str(x) or ".." in str(x) else x, )

    # 1. Mock Ingestion
    with (
        patch("cdsapi.Client") as mock_cds,
        patch("data_pipeline.ingestion.EntsoePandasClient") as mock_entsoe,
        patch("data_pipeline.ingestion.backup_project_data"),
    ):
        # Copernicus Mock
        mock_cds_client = MagicMock()
        mock_cds.return_value = mock_cds_client
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            cols = [
                "valid_time",
                "t2m",
                "d2m",
                "sp",
                "tp",
                "ssrd",
                "strd",
                "skt",
                "stl1",
                "swvl1",
                "u10",
                "v10",
                "latitude",
                "longitude",
            ]
            data = [
                "2024-01-01 00:00:00",
                285.0,
                280.0,
                101000.0,
                0.0,
                500.0,
                300.0,
                284.0,
                282.0,
                0.3,
                2.0,
                1.0,
                40.4,
                -3.7,
            ]
            zip_file.writestr("weather.csv", ",".join(
                cols) + "\n" + ",".join(map(str, data)))

        mock_cds_client.retrieve.return_value.download.side_effect = lambda path: open(
            path, "wb").write(zip_buffer.getvalue())

        # ENTSO-E Mock
        mock_entsoe_client = MagicMock()
        mock_entsoe.return_value = mock_entsoe_client
        df_energy = pd.DataFrame({"Load_MW": [25000.0, 26000.0]}, index=pd.date_range(
            "2024-01-01", periods=2, freq="h", tz="Europe/Madrid"))
        mock_entsoe_client.query_load.return_value = df_energy

        # Run Ingestion
        data_retrieval("2024-01-01", "2024-01-01")

    # 2. Run Cleaning
    raw_energy_dir = project_root / "data" / "raw" / "energy"
    raw_weather_dir = project_root / "data" / "raw" / "weather"

    # Run cleaning pipeline
    cleaning_output = cleaning(
        energy_dir=str(raw_energy_dir),
        weather_dir=str(raw_weather_dir),
        train_data=True,
        output_dir=str(processed_dir))

    # Extract the DataFrame from the tuple.
    # (Assuming the DataFrame you want to test is the first item in the tuple)
    df_final = cleaning_output[0]

    # If your cleaning function specifically returns two DataFrames (e.g., X and y),
    # you can unpack it directly like this:
    # df_final, df_target = cleaning(...)

    assert df_final is not None
    assert not df_final.empty
    assert "Load_MW" in df_final.columns
    assert "t2m" in df_final.columns


def test_fetch_copernicus_bad_zip_retry(tmp_path, monkeypatch):
    monkeypatch.setattr("data_pipeline.ingestion.os.path.abspath", lambda x: str(
        tmp_path) if "ingestion.py" in str(x) or ".." in str(x) else x, )

    with patch("cdsapi.Client") as mock_cds:
        mock_client = MagicMock()
        mock_cds.return_value = mock_client
        mock_client.retrieve.return_value.download.return_value = None

        with patch("data_pipeline.ingestion.os.makedirs"):
            with patch("data_pipeline.ingestion.os.path.exists", return_value=False):
                with patch("zipfile.ZipFile", side_effect=zipfile.BadZipFile("Bad zip")):
                    with patch("data_pipeline.ingestion.time.sleep"):
                        with patch("builtins.open", mock_open(read_data="Error")):
                            fetch_copernicus_data("2024-01-01", "2024-01-01")
                            assert mock_client.retrieve.call_count == 3
