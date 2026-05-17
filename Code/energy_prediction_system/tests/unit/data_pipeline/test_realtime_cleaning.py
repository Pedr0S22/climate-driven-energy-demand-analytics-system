import pandas as pd
import pytest

from src.data_pipeline.cleaning import DataCleaner


@pytest.fixture
def cleaner():
    return DataCleaner()


def test_convert_era5_units_skips_open_meteo(cleaner):
    """Verify that conversion is skipped for Open-Meteo data (has wind_speed_10m)."""
    # Open-Meteo style data (already in Celsius/hPa/mm)
    data = {"t2m": [15.0], "sp": [1013.0], "tp": [0.1], "wind_speed_10m": [2.0], "wind_direction_10m": [180]}
    df = pd.DataFrame(data)

    df_clean = cleaner.convert_era5_units(df)

    # Values should remain unchanged
    assert df_clean.loc[0, "t2m"] == 15.0
    assert df_clean.loc[0, "sp"] == 1013.0
    assert df_clean.loc[0, "tp"] == 0.1


def test_convert_era5_units_converts_era5(cleaner):
    """Verify that conversion is performed for ERA5 data (standard variables)."""
    # ERA5 style data (Kelvin/Pa/m)
    data = {
        "t2m": [288.15],  # 15 Celsius
        "sp": [101300.0],  # 1013 hPa
        "tp": [0.0001],  # 0.1 mm
    }
    df = pd.DataFrame(data)

    df_clean = cleaner.convert_era5_units(df)

    # Values should be converted
    assert pytest.approx(df_clean.loc[0, "t2m"]) == 15.0
    assert pytest.approx(df_clean.loc[0, "sp"]) == 1013.0
    assert pytest.approx(df_clean.loc[0, "tp"]) == 0.1


def test_clean_weather_dataframe_wind_components(cleaner):
    """Verify Open-Meteo wind speed/direction are converted to u10/v10."""
    data = {
        "datetime": ["2026-05-13T00:00"],
        "wind_speed_10m": [10.0],
        "wind_direction_10m": [90],  # From East
    }
    df = pd.DataFrame(data)

    df_clean = cleaner.clean_weather_dataframe(df)

    # 90 degrees (East): u = -10 * sin(90) = -10, v = -10 * cos(90) = 0
    assert "u10" in df_clean.columns
    assert "v10" in df_clean.columns
    assert pytest.approx(df_clean.loc[0, "u10"]) == -10.0
    assert pytest.approx(df_clean.loc[0, "v10"]) == 0.0


def test_timestamp_alignment(cleaner):
    """Ensure mismatched data is discarded and only synchronized entries are kept."""
    # This is better tested in the 'cleaning' function which joins energy and weather,
    # but we can test the internal _align_weather_time too.
    data = {"datetime": ["2026-05-13T00:00", "2026-05-13T00:15", "2026-05-13T00:45"], "t2m": [15.0, 15.1, 15.3]}
    df = pd.DataFrame(data)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)

    df_aligned = cleaner._align_weather_time(df)

    # Should have 4 rows (00:00, 00:15, 00:30, 00:45)
    assert len(df_aligned) == 4
    # 00:30 should be NaN before imputation
    assert pd.isna(df_aligned.loc[2, "t2m"])
