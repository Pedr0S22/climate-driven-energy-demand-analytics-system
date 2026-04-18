import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from data_pipeline.cleaning import (
    DataCleaner,
    cleaning,
)


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
        df_copernicus[cols_existentes].to_csv(os.path.join(fake_path, fname), index=False)


def clean_folder_energy(cleaner, input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(input_dir.glob("*.csv")):
        df = pd.read_csv(f)
        df_cleaned = cleaner.clean_energy_dataframe(df)
        df_cleaned.to_csv(output_dir / f.name, index=False)


def clean_folder_weather(cleaner, input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(input_dir.glob("*.csv")):
        df = pd.read_csv(f)
        df_cleaned = cleaner.clean_weather_dataframe(df)
        df_cleaned.to_csv(output_dir / f.name, index=False)


def setup_dirs():
    base_dir = tempfile.mkdtemp(prefix="piacd_test_")
    base_dir_path = Path(base_dir)

    raw_energy = base_dir_path / "energy"
    raw_weather = base_dir_path / "weather"
    energy_clean = base_dir_path / "energy_corrigido"
    weather_clean = base_dir_path / "weather_corrigido"

    raw_energy.mkdir(parents=True, exist_ok=True)
    raw_weather.mkdir(parents=True, exist_ok=True)
    energy_clean.mkdir(parents=True, exist_ok=True)
    weather_clean.mkdir(parents=True, exist_ok=True)

    start_date = "2024-01-01"
    end_date = "2024-01-03"

    return (
        base_dir_path,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    )


def mock_entsoe_data(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    index = index[:-1]
    df = pd.DataFrame(
        {
            "Load_MW": abs(
                5000 + 1000 * np.cos(0.01 * index.astype("int64") // 1e9) + 100 * np.random.randn(len(index))
            ).round(2),
        },
        index=index,
    )
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df


def mock_copernicus_data(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    index = index[:-1]
    df = pd.DataFrame(
        {
            "valid_time": index,
            "t2m": 273.15 + 15 + 10 * ((index.hour / 24) - 0.5) + np.random.randn(len(index)),
            "d2m": 273.15 + 12 + 8 * ((index.hour / 24) - 0.5) + np.random.randn(len(index)),
            "skt": 273.15 + 20 + 12 * ((index.hour / 24) - 0.5) + np.random.randn(len(index)),
            "stl1": 273.15 + 18 + 8 * ((index.hour / 24) - 0.5) + np.random.randn(len(index)),
            "u10": 5 + 10 * np.random.randn(len(index)),
            "v10": 3 + 8 * np.random.randn(len(index)),
            "ssrd": 200 + 100 * np.random.randn(len(index)),
            "strd": 300 + 200 * np.random.randn(len(index)),
            "sp": 101300 + 1000 * np.random.randn(len(index)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index)),
            "swvl1": 0.3 + 0.1 * np.random.randn(len(index)),
        }
    )
    return df


@patch("data_pipeline.ingestion.cdsapi.Client")
@patch("data_pipeline.ingestion.EntsoePandasClient")
def test_full_pipeline_integration(mock_entsoe, mock_cds):
    (base_dir_path, raw_energy, raw_weather, energy_clean, weather_clean, start_date, end_date) = setup_dirs()
    try:
        cleaner = DataCleaner()
        df_entsoe = mock_entsoe_data(start_date, end_date)
        df_entsoe.to_csv(raw_energy / "entsoe_ES.csv", index=False)
        df_copernicus = mock_copernicus_data(start_date, end_date)
        setup_fake_weather_files(raw_weather, df_copernicus)

        clean_folder_energy(cleaner, raw_energy, energy_clean)
        clean_folder_weather(cleaner, raw_weather, weather_clean)

        res = cleaning(energy_dir=energy_clean, weather_dir=weather_clean, train_data=True, output_dir=base_dir_path)
        df_final = res[0] if isinstance(res, tuple) else res

        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in ["t2m", "ssrd", "tp", "u10", "v10"])
    finally:
        shutil.rmtree(base_dir_path, ignore_errors=True)


def mock_entsoe_data_15min_with_nan_and_without_out(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    index = index[:-1]
    base = abs(5000 + 1000 * np.cos(0.01 * index.astype("int64") // 1e9))
    noise = 100 * np.random.randn(len(index))
    load = np.array((base + noise).round(2))
    load[4::4] = np.nan
    df = pd.DataFrame({"Load_MW": load}, index=index)
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df


def mock_copernicus_data_15min_with_outliers_and_nan(start_date, end_date):
    df = mock_copernicus_data(start_date, end_date)
    indices_t2m = df.index[::8]
    indices_ssrd = df.index[::16]
    df.loc[indices_t2m, "t2m"] *= 2
    df.loc[indices_ssrd, "ssrd"] *= 3
    mask_t2m_nan = np.random.rand(len(df)) < 0.05
    df.loc[mask_t2m_nan, "t2m"] = np.nan
    return df


@patch("data_pipeline.ingestion.cdsapi.Client")
@patch("data_pipeline.ingestion.EntsoePandasClient")
def test_full_pipeline_integration_15min_with_outliers_and_nan(mock_entsoe, mock_cds):
    (base_dir_path, raw_energy, raw_weather, energy_clean, weather_clean, start_date, end_date) = setup_dirs()
    try:
        cleaner = DataCleaner()
        df_entsoe = mock_entsoe_data_15min_with_nan_and_without_out(start_date, end_date)
        df_entsoe.to_csv(raw_energy / "entsoe_nan.csv", index=False)
        df_copernicus = mock_copernicus_data_15min_with_outliers_and_nan(start_date, end_date)
        setup_fake_weather_files(raw_weather, df_copernicus)

        clean_folder_energy(cleaner, raw_energy, energy_clean)
        clean_folder_weather(cleaner, raw_weather, weather_clean)

        res = cleaning(energy_dir=energy_clean, weather_dir=weather_clean, train_data=True, output_dir=base_dir_path)
        df_final = res[0] if isinstance(res, tuple) else res

        assert df_final is not None
        assert len(df_final) > 0
        assert any(var in df_final.columns for var in ["t2m", "ssrd", "tp", "u10", "v10"])
    finally:
        shutil.rmtree(base_dir_path, ignore_errors=True)


@patch("data_pipeline.ingestion.cdsapi.Client")
@patch("data_pipeline.ingestion.EntsoePandasClient")
def test_full_pipeline_integration_1h_clean(mock_entsoe, mock_cds):
    (base_dir_path, raw_energy, raw_weather, energy_clean, weather_clean, start_date, end_date) = setup_dirs()
    try:
        cleaner = DataCleaner()
        # Create 1h data
        times = pd.date_range(start_date, periods=48, freq="1h", tz="UTC")
        df_e = pd.DataFrame({"Unnamed: 0": times, "Load_MW": np.random.uniform(20000, 30000, 48)})
        df_e.to_csv(raw_energy / "energy_1h.csv", index=False)

        df_w = pd.DataFrame(
            {
                "valid_time": times,
                "latitude": [40.4] * 48,
                "longitude": [-3.7] * 48,
                "t2m": [283.15] * 48,
                "u10": [2.0] * 48,
                "tp": [0.0] * 48,
                "ssrd": [0.0] * 48,
                "d2m": [275.0] * 48,
                "skt": [283.0] * 48,
                "strd": [1000.0] * 48,
                "sp": [101325.0] * 48,
                "stl1": [280.0] * 48,
                "swvl1": [0.3] * 48,
            }
        )
        setup_fake_weather_files(raw_weather, df_w)

        clean_folder_energy(cleaner, raw_energy, energy_clean)
        clean_folder_weather(cleaner, raw_weather, weather_clean)

        res = cleaning(energy_dir=energy_clean, weather_dir=weather_clean, train_data=True, output_dir=base_dir_path)
        df_final = res[0] if isinstance(res, tuple) else res

        assert df_final is not None
        assert len(df_final) > 0
        assert df_final.isnull().sum().sum() == 0
    finally:
        shutil.rmtree(base_dir_path, ignore_errors=True)
