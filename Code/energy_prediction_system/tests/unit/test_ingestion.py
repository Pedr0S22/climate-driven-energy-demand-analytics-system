import pytest
import pandas as pd
import zipfile
from unittest.mock import patch, MagicMock, mock_open

from ingestion import fetch_copernicus_data, fetch_entsoe_data
from gdrive_sync import backup_project_data, upload_file_to_drive


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ENTSOE_API_KEY", "fake_api_key")
    monkeypatch.setenv("WEATHER_DRIVE_FOLDER_ID", "fake_weather_id")
    monkeypatch.setenv("ENERGY_DRIVE_FOLDER_ID", "fake_energy_id")


@patch("ingestion.os.path.exists")
@patch("ingestion.EntsoePandasClient")
def test_fetch_entsoe_single_day(mock_entsoe_client, mock_exists, mock_env_vars):
    """Test single day ingestion logic (start_date == end_date)"""
    mock_exists.return_value = False

    mock_client_instance = MagicMock()
    mock_entsoe_client.return_value = mock_client_instance

    mock_df = MagicMock()
    mock_client_instance.query_load.return_value = mock_df

    fetch_entsoe_data("2023-01-01", "2023-01-01")

    # Verify the 1-day timedelta to capture the full single day
    mock_client_instance.query_load.assert_called_once()
    _, kwargs = mock_client_instance.query_load.call_args
    assert kwargs["start"] == pd.Timestamp("2023-01-01", tz="Europe/Madrid")
    assert kwargs["end"] == pd.Timestamp("2023-01-02", tz="Europe/Madrid")
    mock_df.to_csv.assert_called_once()


@patch("ingestion.os.path.exists")
@patch("ingestion.EntsoePandasClient")
def test_fetch_entsoe_date_range(mock_entsoe_client, mock_exists, mock_env_vars):
    """Test small/large date range ingestion logic"""
    mock_exists.return_value = False
    mock_client_instance = MagicMock()
    mock_entsoe_client.return_value = mock_client_instance

    # Passing a large range of a whole year
    fetch_entsoe_data("2022-01-01", "2022-12-31")

    mock_client_instance.query_load.assert_called_once()
    _, kwargs = mock_client_instance.query_load.call_args
    assert kwargs["start"] == pd.Timestamp("2022-01-01", tz="Europe/Madrid")
    assert kwargs["end"] == pd.Timestamp("2023-01-01", tz="Europe/Madrid")


@patch("ingestion.time.sleep", return_value=None)
@patch("ingestion.os.path.exists")
@patch("ingestion.EntsoePandasClient")
def test_fetch_entsoe_retry_mechanism(mock_entsoe_client, mock_exists, mock_sleep, mock_env_vars):
    """Test that the script retries 3 times upon failure with exponential backoff"""
    mock_exists.return_value = False
    mock_client_instance = MagicMock()
    mock_entsoe_client.return_value = mock_client_instance

    # Force an exception every time it tries to query
    mock_client_instance.query_load.side_effect = Exception("API Timeout")

    fetch_entsoe_data("2023-01-01", "2023-01-01")

    # try exactly 3 times (max_retries = 3) before giving up
    assert mock_client_instance.query_load.call_count == 3
    # sleep 2 times (after 1st and 2nd failure)
    assert mock_sleep.call_count == 2


@patch("ingestion.os.path.exists")
@patch("ingestion.zipfile.ZipFile")
@patch("ingestion.cdsapi.Client")
@patch("ingestion.os.remove")
@patch("ingestion.os.replace")
def test_fetch_copernicus_data_success(mock_replace, mock_remove, mock_cds_client, mock_zip, mock_exists):
    """Test successful fetch, ZIP extraction, and cleanup for Copernicus data"""
    # Ensure it passes the initial 'file exists' check
    mock_exists.return_value = False

    mock_client_instance = MagicMock()
    mock_cds_client.return_value = mock_client_instance

    # Setup mock for zipfile
    mock_zip_instance = MagicMock()
    mock_zip.return_value.__enter__.return_value = mock_zip_instance
    mock_zip_instance.namelist.return_value = ["dummy_weather.csv"]

    fetch_copernicus_data("2023-01-01", "2023-01-31")

    # Verify API download was triggered
    mock_client_instance.retrieve.assert_called_once()
    mock_client_instance.retrieve().download.assert_called_once()

    # Verify extraction, replacement, and zip deletion
    mock_zip_instance.extractall.assert_called_once()
    mock_replace.assert_called_once()


@patch("gdrive_sync.upload_file_to_drive")
@patch("gdrive_sync.os.listdir")
@patch("gdrive_sync.os.path.exists")
def test_backup_project_data(mock_exists, mock_listdir, mock_upload, mock_env_vars):
    """Test the GDrive backup logic correctly loops over directories and uploads files"""
    mock_exists.return_value = True

    # Simulate raw directories containing CSV files
    mock_listdir.side_effect = [
        ["energy_test.csv"],  # Yielded for /raw/energy
        ["weather_test.csv"],  # Yielded for /raw/weather
    ]

    with patch("gdrive_sync.authenticate_gdrive", return_value=MagicMock()):
        backup_project_data()

    # Verify upload was called twice (once for each file)
    assert mock_upload.call_count == 2


# ==========================================
# Additional Coverage Tests
# ==========================================


@patch("ingestion.os.path.exists")
def test_fetch_entsoe_skips_if_exists(mock_exists):
    """Test ENTSO-E skips if file already exists"""
    mock_exists.return_value = True
    with patch("ingestion.EntsoePandasClient") as mock_client:
        fetch_entsoe_data("2023-01-01", "2023-01-01")
        mock_client.assert_not_called()


@patch("ingestion.os.getenv", return_value=None)
@patch("ingestion.os.path.exists", return_value=False)
def test_fetch_entsoe_no_api_key(mock_exists, mock_getenv):
    """Test ENTSO-E aborts if API key is missing"""
    with patch("ingestion.EntsoePandasClient") as mock_client:
        fetch_entsoe_data("2023-01-01", "2023-01-01")
        mock_client.assert_not_called()


@patch("ingestion.os.path.exists")
def test_fetch_copernicus_skips_if_exists(mock_exists):
    """Test Copernicus skips if file already exists"""
    mock_exists.return_value = True
    with patch("ingestion.cdsapi.Client") as mock_client:
        fetch_copernicus_data("2023-01-01", "2023-01-01")
        mock_client.assert_not_called()


@patch("ingestion.time.sleep", return_value=None)
@patch("ingestion.os.path.exists", return_value=False)
@patch("ingestion.cdsapi.Client")
def test_fetch_copernicus_bad_zip_file(mock_cds_client, mock_exists, mock_sleep):
    """Test Copernicus API quotas/messages handling as BadZipFile"""
    mock_client_instance = MagicMock()
    mock_cds_client.return_value = mock_client_instance

    with patch("ingestion.zipfile.ZipFile") as mock_zip:
        mock_zip.side_effect = zipfile.BadZipFile("Not a zip")
        with patch("builtins.open", mock_open(read_data="API Error Details")):
            fetch_copernicus_data("2023-01-01", "2023-01-01")
        # Should retry 3 times
        assert mock_zip.call_count == 3
        assert mock_sleep.call_count == 2


def test_backup_project_data_missing_ids(monkeypatch):
    """Test GDrive backup aborts if folder IDs are missing"""
    monkeypatch.delenv("WEATHER_DRIVE_FOLDER_ID", raising=False)
    monkeypatch.delenv("ENERGY_DRIVE_FOLDER_ID", raising=False)
    with patch("gdrive_sync.authenticate_gdrive"):
        with pytest.raises(ValueError, match="Missing Drive Folder IDs!"):
            backup_project_data()


def test_upload_file_to_drive_duplicate():
    """Test upload skipped when file already exists on GDrive"""
    mock_service = MagicMock()
    mock_service.files().list().execute.return_value = {"files": [{"id": "123"}]}
    upload_file_to_drive(mock_service, "dummy/test.csv", "folder_id")
    mock_service.files().create.assert_not_called()


def test_fetch_entsoe_invalid_dates():
    """Test that passing an end_date before a start_date raises an error"""
    with pytest.raises(ValueError, match="start_date cannot be strictly after end_date"):
        fetch_entsoe_data("2023-12-31", "2023-01-01")


def test_fetch_copernicus_invalid_dates():
    """Test that passing an end_date before a start_date raises an error"""
    with pytest.raises(ValueError, match="start_date cannot be strictly after end_date"):
        fetch_copernicus_data("2023-12-31", "2023-01-01")
