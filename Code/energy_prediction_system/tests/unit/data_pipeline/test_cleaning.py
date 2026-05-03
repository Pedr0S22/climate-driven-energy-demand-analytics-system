import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from data_pipeline.cleaning import DataCleaner, cleaning

# =======================================
# FIXTURES
# =======================================


@pytest.fixture
def cleaner():
    return DataCleaner()


# =======================================
# DADOS ENERGY TESTS (Adapted from Legacy)
# =======================================


def test_fill_nan_energy_1h_input(cleaner):
    times = pd.to_datetime(["2023-01-01 10:00", "2023-01-01 11:00"], utc=True)
    df = pd.DataFrame({"datetime": times, "Load_MW": [100.0, 110.0]})
    df_filled = cleaner.fill_nan_energy(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_filled["Load_MW"])
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_15min_no_missing(cleaner):
    times = pd.to_datetime(["2023-01-01 10:00", "2023-01-01 10:15", "2023-01-01 10:30", "2023-01-01 10:45"], utc=True)
    df = pd.DataFrame({"datetime": times, "Load_MW": [100.0, 101.0, 102.0, 103.0]})
    df_filled = cleaner.fill_nan_energy(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_filled["Load_MW"])
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_15min_one_nan_uses_interpolation(cleaner):
    times = pd.to_datetime(["2023-01-01 10:00", "2023-01-01 10:15", "2023-01-01 10:30", "2023-01-01 10:45"], utc=True)
    df = pd.DataFrame({"datetime": times, "Load_MW": [100.0, 105.0, None, 110.0]})
    df_filled = cleaner.fill_nan_energy(df.copy())
    val = df_filled.loc[df_filled["datetime"] == times[2], "Load_MW"].iloc[0]
    assert pd.notna(val)
    assert 105.0 <= val <= 110.0
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_15min_multiple_nans_uses_mean_last6(cleaner):
    times = pd.to_datetime(
        [
            "2023-08-01 09:00",
            "2023-08-01 09:15",
            "2023-08-01 09:30",
            "2023-08-01 09:45",
            "2023-08-01 10:00",
            "2023-08-01 10:15",
            "2023-08-01 10:30",
            "2023-08-01 10:45",
            "2023-08-01 11:00",
            "2023-08-01 11:15",
            "2023-08-01 11:30",
            "2023-08-01 11:45",
        ],
        utc=True,
    )
    df = pd.DataFrame(
        {"datetime": times, "Load_MW": [80.0, 85.0, 90.0, 95.0, 100.0, 105.0, 110.0, 115.0, None, None, 125.0, 130.0]}
    )
    df_filled = cleaner.fill_nan_energy(df.copy())
    valid_before = df.loc[df["datetime"] < times[8], "Load_MW"].dropna().tail(6)
    expected_mean = valid_before.mean()
    assert pytest.approx(df_filled["Load_MW"].iloc[8]) == expected_mean
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_primeira_linha_nan(cleaner):
    times = pd.to_datetime(["2023-01-01 10:00", "2023-01-01 10:15", "2023-01-01 10:30"], utc=True)
    df = pd.DataFrame({"datetime": times, "Load_MW": [None, 105.0, 110.0]})
    df_filled = cleaner.fill_nan_energy(df.copy())
    assert df_filled.loc[0, "Load_MW"] == 105.0
    assert not df_filled["Load_MW"].isna().any()


# =======================================
# WEATHER PROCESSING TESTS (Adapted from Legacy)
# =======================================


def test_convert_era5_units_all_conversions(cleaner):
    times = pd.date_range("2023-01-01 10:00", periods=2, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "valid_time": times,
            "skt": [273.15, 286.15],
            "t2m": [273.15, 286.15],
            "d2m": [273.15, 286.15],
            "stl1": [273.15, 286.15],
            "ssrd": [900, 1800],
            "strd": [900, 1800],
            "sp": [101325, 102000],
            "tp": [0.001, 0.005],
        }
    )
    result = cleaner.convert_era5_units(df.copy())
    assert pytest.approx(result["t2m"].iloc[0]) == 0.0
    assert pytest.approx(result["ssrd"].iloc[0]) == 1.0
    assert pytest.approx(result["sp"].iloc[0]) == 1013.25
    assert pytest.approx(result["tp"].iloc[0]) == 1.0


def test_temp_termicRad_imputation_media_4prev_2next(cleaner):
    times = pd.date_range("2023-01-01 10:00", periods=7, freq="15min", tz="UTC")
    series = pd.Series([10, 11, 12, 13, np.nan, 15, 16], index=times)
    # trigger multiple NaN logic by having at least 2 NaNs in one hour
    series.iloc[5] = np.nan
    result = cleaner._media_custom(series, n_prev=4, n_next=2)
    expected = (10 + 11 + 12 + 13 + 16) / 5
    assert pytest.approx(result.iloc[4], rel=1e-6) == expected


def test_solar_imputation_night_zero(cleaner):
    times = pd.date_range("2023-01-01 00:00", periods=3, freq="h", tz="UTC")
    series = pd.Series([np.nan, 0, np.nan], index=times)
    result = cleaner._solar_impute(series)
    assert (result == 0.0).all()


def test_precip_imputation_surrounded_by_zeros(cleaner):
    times = pd.date_range("2023-01-01 10:00", periods=5, freq="15min", tz="UTC")
    series = pd.Series([0, 0, np.nan, 0, 0], index=times)
    result = cleaner._precip_impute(series)
    assert pytest.approx(result.iloc[2], rel=1e-6) == 0


# =======================================
# OUTLIERS & AGGREGATION
# =======================================


def test_outliers_treatment_t2m_physical_outlier(cleaner):
    times = pd.date_range("2023-01-01 10:00", periods=10, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {
            "datetime": times,
            "latitude": [40.0] * 10,
            "longitude": [-8.0] * 10,
            "t2m": [8.0, 9.0, 10.0, 11.0, -45.0, 12.0, 13.0, 14.0, 15.0, 16.0],
        }
    )
    df_result = cleaner.treat_weather_outliers(df.copy())
    assert df_result.loc[4, "t2m"] >= -40
    assert pd.notna(df_result.loc[4, "t2m"])


def test_hourly_aggregation_15min_to_hourly_mean(cleaner):
    times = pd.date_range("2023-01-01 10:00", periods=4, freq="15min", tz="UTC")
    df = pd.DataFrame(
        {"valid_time": times, "latitude": [40.0] * 4, "longitude": [-8.0] * 4, "t2m": [10.0, 11.0, 12.0, 13.0]}
    )
    df_result = cleaner.aggregate_hourly_weather(df.copy())
    assert len(df_result) == 1
    assert pytest.approx(df_result.loc[0, "t2m"], rel=1e-6) == 11.5


# =======================================
# NEW: DAILY AGGREGATION TESTS
# =======================================


def test_create_daily_aggregation(cleaner):
    times = pd.date_range("2023-01-01 00:00", periods=48, freq="h", tz="UTC")
    df_hourly = pd.DataFrame({"datetime": times, "Load_MW": [100.0] * 48, "t2m": [10.0] * 48})
    df_daily = cleaner.create_daily_aggregation(df_hourly)
    assert len(df_daily) == 2
    # Sum: 24 * 100 = 2400
    assert df_daily.loc[0, "Load_MWh"] == 2400.0
    # Mean: 10.0
    assert df_daily.loc[0, "t2m"] == 10.0


# =======================================
# INTEGRATION TESTS (Adapted from Legacy)
# =======================================


def setup_fake_weather_files(fake_path, df_copernicus):
    fake_path = Path(fake_path)
    fake_path.mkdir(parents=True, exist_ok=True)
    file_map = {
        "era5_timeseries_2020-01-01_to_2025-12-31.csv": ["valid_time", "u10", "v10", "latitude", "longitude"],
        "reanalysis-era5-land-timeseries-sfc-2m-temperatureauafbxo0.csv": [
            "valid_time",
            "d2m",
            "t2m",
            "latitude",
            "longitude",
        ],
        "reanalysis-era5-land-timeseries-sfc-skin-temperaturercarv5g8.csv": [
            "valid_time",
            "skt",
            "latitude",
            "longitude",
        ],
        "reanalysis-era5-land-timeseries-sfc-radiation-heathoyt7mym.csv": [
            "valid_time",
            "ssrd",
            "strd",
            "latitude",
            "longitude",
        ],
        "reanalysis-era5-land-timeseries-sfc-pressure-precipitationtwpvvkbd.csv": [
            "valid_time",
            "sp",
            "tp",
            "latitude",
            "longitude",
        ],
        "reanalysis-era5-land-timeseries-sfc-soil-temperatureokgb55eq.csv": [
            "valid_time",
            "stl1",
            "latitude",
            "longitude",
        ],
        "reanalysis-era5-land-timeseries-sfc-soil-waterp9pn16zx.csv": ["valid_time", "swvl1", "latitude", "longitude"],
    }
    for fname, cols in file_map.items():
        cols_existentes = [c for c in cols if c in df_copernicus.columns]
        df_copernicus[cols_existentes].to_csv(fake_path / fname, index=False)


@patch("data_pipeline.ingestion.cdsapi.Client")
@patch("data_pipeline.ingestion.EntsoePandasClient")
def test_full_pipeline_integration_mocked(mock_entsoe, mock_cds, cleaner):
    with tempfile.TemporaryDirectory() as base_dir:
        base_path = Path(base_dir)
        raw_energy = base_path / "energy"
        raw_weather = base_path / "weather"
        raw_energy.mkdir()
        raw_weather.mkdir()

        start_date = "2024-01-01"

        # Mock Energy
        times_e = pd.date_range(start=start_date, periods=4, freq="15min", tz="UTC")
        df_e = pd.DataFrame({"Unnamed: 0": times_e, "Load_MW": [100.0, 110.0, 120.0, 130.0]})
        df_e.to_csv(raw_energy / "entsoe_test.csv", index=False)

        # Mock Weather
        times_w = pd.date_range(start=start_date, periods=4, freq="15min", tz="UTC")
        df_w = pd.DataFrame(
            {
                "valid_time": times_w,
                "latitude": [40.0] * 4,
                "longitude": [-3.0] * 4,
                "t2m": [283.15] * 4,
                "u10": [2.0] * 4,
                "tp": [0.0] * 4,
                "ssrd": [0.0] * 4,
                "d2m": [275.0] * 4,
                "skt": [283.0] * 4,
                "strd": [1000.0] * 4,
                "sp": [101325.0] * 4,
                "stl1": [280.0] * 4,
                "swvl1": [0.3] * 4,
            }
        )
        setup_fake_weather_files(raw_weather, df_w)

        # Run cleaning
        df_hourly, df_daily = cleaning(
            energy_dir=raw_energy, weather_dir=raw_weather, train_data=True, output_dir=base_path
        )

        assert len(df_hourly) == 1
        assert "Load_MW" in df_hourly.columns
        assert "t2m" in df_hourly.columns
        assert df_hourly.loc[0, "t2m"] == 10.0
        assert df_hourly.loc[0, "Load_MW"] == 130.0
