import os
import shutil
import tempfile
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from cleaning import (
    energy,
    weather,
    cleaning,
)

from ingestion import fetch_entsoe_data, fetch_copernicus_data


def setup_fake_weather_files(fake_path):
    os.makedirs(fake_path, exist_ok=True)

    # cria um CSV falso com datas 2020–2025, só para o teste
    index = pd.date_range("2024-01-01", "2024-01-02", freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "valid_time": index,
            "t2m": 273.15 + 15 + np.random.randn(len(index)),
            "d2m": 273.15 + 12 + np.random.randn(len(index)),
            "ssrd": 200 + 100 * np.random.randn(len(index)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index)),
        }
    )

    # ficheiro fake
    ERA5_CSV = os.path.join(
        fake_path,
        "era5_timeseries_2020-01-01_to_2025-12-31.csv")
    df.to_csv(ERA5_CSV, index=False)

    # restantes
    other_files = [
        "reanalysis-era5-land-timeseries-sfc-2m-temperatureauafbxo0.csv",
        "reanalysis-era5-land-timeseries-sfc-pressure-precipitationtwpvvkbd.csv",
        "reanalysis-era5-land-timeseries-sfc-radiation-heathoyt7mym.csv",
        "reanalysis-era5-land-timeseries-sfc-skin-temperaturercarv5g8.csv",
        "reanalysis-era5-land-timeseries-sfc-soil-temperatureokgb55eq.csv",
        "reanalysis-era5-land-timeseries-sfc-soil-waterp9pn16zx.csv",
    ]
    for fname in other_files:
        df.head(0).to_csv(os.path.join(fake_path, fname), index=False)

    return df

# 1


def setup_dirs():
    base_dir = tempfile.mkdtemp(prefix="piacd_test_")

    raw_energy = os.path.join(base_dir, "data", "raw", "energy")
    raw_weather = os.path.join(base_dir, "data", "raw", "weather")
    energy_clean = os.path.join(base_dir, "data", "raw", "energy_corrigido")
    weather_clean = os.path.join(base_dir, "data", "raw", "weather_corrigido")

    os.makedirs(raw_energy, exist_ok=True)
    os.makedirs(raw_weather, exist_ok=True)
    os.makedirs(energy_clean, exist_ok=True)
    os.makedirs(weather_clean, exist_ok=True)

    start_date = "2024-01-01"
    end_date = "2024-01-03"

    return (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    )

# 2


def mock_entsoe_data(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)

    index = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    index = index[:-1]

    df = pd.DataFrame(
        {
            "Load_MW": abs(
                5000
                + 1000 * np.cos(0.01 * index.astype(int) // 1e9)
                + 100 * np.random.randn(len(index))
            ).round(2),
        },
        index=index,
    )
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df

# 3


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

# 4. teste de integração


@patch("ingestion.cdsapi.Client")
@patch("ingestion.EntsoePandasClient")
def test_full_pipeline_integration(mock_entsoe, mock_cds):
    (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    ) = setup_dirs()

    fake_path = "/tmp/fake_weather_data"
    fake_df = setup_fake_weather_files(fake_path)

    try:
        # 1. ENTSO‑E
        df_entsoe = mock_entsoe_data_mixed_granularity_clean(
            start_date, end_date)
        entsoe_filename = f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        entsoe_path = os.path.join(raw_energy, entsoe_filename)
        df_entsoe.to_csv(entsoe_path, index=False)

        # 2. Copernicus
        df_copernicus = mock_copernicus_data_mixed_granularity_clean(
            start_date, end_date)
        # exact same name as fetch_copernicus_data
        copernicus_filename = f"era5_timeseries_{start_date}_to_{end_date}.csv"
        copernicus_path = os.path.join(raw_weather, copernicus_filename)
        df_copernicus.to_csv(copernicus_path, index=False)

        # 3. chama as funções como se fossem do pipeline
        fetch_entsoe_data(start_date, end_date)
        fetch_copernicus_data(start_date, end_date)

        # 4. energia
        energy(raw_energy, pasta_saida=energy_clean)

        # 5. clima
        with patch("pandas.read_csv", return_value=fake_df):
            weather(pasta_saida=weather_clean)

        # 6. limpeza e junção final
        df_final = cleaning(
            pasta_energy_corrigido=energy_clean,
            pasta_weather_corrigido=weather_clean,
        )

        # 7. CSV final
        REAL_PROCESSED = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
        final_csv = os.path.join(REAL_PROCESSED, "dados_finais_completos.csv")
        assert os.path.exists(final_csv), f"CSV final não existe: {final_csv}"
        assert os.path.getsize(final_csv) > 0

        # 8. verificações
        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in [
                   "t2m", "ssrd", "tp", "u10", "v10"])
        assert df_final["datetime"].min() < pd.Timestamp(
            end_date, tz="UTC") + pd.Timedelta(days=1)
        assert df_final["datetime"].max() > pd.Timestamp(
            start_date, tz="UTC") - pd.Timedelta(days=1)

        print(
            f"Pipeline completo com sucesso: {len(df_final)} registos no dataset final."
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

##########
#########

# 5. mock ENTSO‑E 15 min com outliers e NaN


def mock_entsoe_data_15min_with_nan_and_without_out(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    index = index[:-1]

    base = abs(5000 + 1000 * np.cos(0.01 * index.astype(int) // 1e9))
    noise = 100 * np.random.randn(len(index))
    load = np.array((base + noise).round(2))

    nan_every_hour = 4
    load[nan_every_hour::nan_every_hour] = np.nan

    df = pd.DataFrame({"Load_MW": load}, index=index)
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df

# 6. mock Copernicus 15 min com outliers e NaN


def mock_copernicus_data_15min_with_outliers_and_nan(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="15min", tz="UTC")
    index = index[:-1]

    df = pd.DataFrame(
        {
            "valid_time": index,
            "t2m": 273.15
            + 15
            + 10 * ((index.hour / 24) - 0.5)
            + np.random.randn(len(index)),
            "d2m": 273.15
            + 12
            + 8 * ((index.hour / 24) - 0.5)
            + np.random.randn(len(index)),
            "skt": 273.15
            + 20
            + 12 * ((index.hour / 24) - 0.5)
            + np.random.randn(len(index)),
            "stl1": 273.15
            + 18
            + 8 * ((index.hour / 24) - 0.5)
            + np.random.randn(len(index)),
            "u10": 5 + 10 * np.random.randn(len(index)),
            "v10": 3 + 8 * np.random.randn(len(index)),
            "ssrd": 200 + 100 * np.random.randn(len(index)),
            "strd": 300 + 200 * np.random.randn(len(index)),
            "sp": 101300 + 1000 * np.random.randn(len(index)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index)),
            "swvl1": 0.3 + 0.1 * np.random.randn(len(index)),
        }
    )

    # 1. outliers
    indices_t2m = df.index[::8]
    indices_ssrd = df.index[::16]

    df.loc[indices_t2m, "t2m"] *= 2
    df.loc[indices_ssrd, "ssrd"] *= 3

    # 2. NaN probabilísticos
    mask_t2m_nan = np.random.rand(len(df)) < 0.05
    mask_ssrd_nan = np.random.rand(len(df)) < 0.03
    df.loc[mask_t2m_nan, "t2m"] = np.nan
    df.loc[mask_ssrd_nan, "ssrd"] = np.nan

    return df

# 7. teste de integração com 15 min, outliers e NaN


@patch("ingestion.cdsapi.Client")
@patch("ingestion.EntsoePandasClient")
def test_full_pipeline_integration_15min_with_outliers_and_nan(
        mock_entsoe,
        mock_cds):
    (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    ) = setup_dirs()

    fake_path = "/tmp/fake_weather_data"
    fake_df = setup_fake_weather_files(fake_path)

    try:
        # 1. ENTSO‑E
        df_entsoe = mock_entsoe_data_mixed_granularity_clean(
            start_date, end_date)
        entsoe_filename = f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        entsoe_path = os.path.join(raw_energy, entsoe_filename)
        df_entsoe.to_csv(entsoe_path, index=False)

        # 2. Copernicus
        df_copernicus = mock_copernicus_data_mixed_granularity_clean(
            start_date, end_date)
        # exact same name as fetch_copernicus_data
        copernicus_filename = f"era5_timeseries_{start_date}_to_{end_date}.csv"
        copernicus_path = os.path.join(raw_weather, copernicus_filename)
        df_copernicus.to_csv(copernicus_path, index=False)

        # 3. ingestão
        fetch_entsoe_data(start_date, end_date)
        fetch_copernicus_data(start_date, end_date)

        # 4. energia
        energy(raw_energy, pasta_saida=energy_clean)

        # 5. clima
        with patch("pandas.read_csv", return_value=fake_df):
            weather(pasta_saida=weather_clean)

        # 6. limpeza e junção final
        df_final = cleaning(
            pasta_energy_corrigido=energy_clean,
            pasta_weather_corrigido=weather_clean,
        )

        # 7. CSV final
        REAL_PROCESSED = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
        final_csv = os.path.join(REAL_PROCESSED, "dados_finais_completos.csv")
        assert os.path.exists(final_csv), f"CSV final não existe: {final_csv}"
        assert os.path.getsize(final_csv) > 0

        # 8. verificações
        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in [
                   "t2m", "ssrd", "tp", "u10", "v10"])

        print(
            f"Pipeline 15min com outliers + NaN: {len(df_final)} registos no dataset final."
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


##########
#########

# 8. mock ENTSO‑E 1h sem outliers e NaN


def mock_entsoe_data_1h_clean(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="1h", tz="UTC")
    index = index[:-1]  # limpa o último, se quiseres

    base = abs(5000 + 1000 * np.cos(0.01 * index.astype(int) // 1e9))
    noise = 100 * np.random.randn(len(index))
    load = ((base + noise).round(2))

    df = pd.DataFrame({"Load_MW": load}, index=index)
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df


# 9. mock Copernicus 1h
def mock_copernicus_data_1h_clean(start_date, end_date):
    # 1h em vez de 15 min
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="1h", tz="UTC")
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

# 10. teste integraçao 1h limpo


@patch("ingestion.cdsapi.Client")
@patch("ingestion.EntsoePandasClient")
def test_full_pipeline_integration_1h_clean(mock_entsoe, mock_cds):
    (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    ) = setup_dirs()

    fake_path = "/tmp/fake_weather_data"
    fake_df = setup_fake_weather_files(fake_path)

    try:
        # 1. ENTSO‑E
        df_entsoe = mock_entsoe_data_mixed_granularity_clean(
            start_date, end_date)
        entsoe_filename = f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        entsoe_path = os.path.join(raw_energy, entsoe_filename)
        df_entsoe.to_csv(entsoe_path, index=False)

        # 2. Copernicus
        df_copernicus = mock_copernicus_data_mixed_granularity_clean(
            start_date, end_date)
        # exact same name as fetch_copernicus_data
        copernicus_filename = f"era5_timeseries_{start_date}_to_{end_date}.csv"
        copernicus_path = os.path.join(raw_weather, copernicus_filename)
        df_copernicus.to_csv(copernicus_path, index=False)

        # 3.  ingestão
        fetch_entsoe_data(start_date, end_date)
        fetch_copernicus_data(start_date, end_date)

        # 4. energia
        energy(raw_energy, pasta_saida=energy_clean)

        # 5. clima
        with patch("pandas.read_csv", return_value=fake_df):
            weather(pasta_saida=weather_clean)

        # 6. limpeza e junção final
        df_final = cleaning(
            pasta_energy_corrigido=energy_clean,
            pasta_weather_corrigido=weather_clean,
        )

        # 7. CSV final
        REAL_PROCESSED = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
        final_csv = os.path.join(REAL_PROCESSED, "dados_finais_completos.csv")
        assert os.path.exists(final_csv), f"CSV final não existe: {final_csv}"
        assert os.path.getsize(final_csv) > 0

        # 8. verificações
        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in [
                   "t2m", "ssrd", "tp", "u10", "v10"])
        assert df_final.isnull().sum().sum() == 0

        print(
            f"Pipeline 1h sem outliers/NaN: {len(df_final)} registos no dataset final."
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

##########
#########

# 11. mock ENTSO‑E 1h sem outliers


def mock_entsoe_data_1h_without_outliers(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="1h", tz="UTC")
    index = index[:-1]

    base = abs(5000 + 1000 * np.cos(0.01 * index.astype(int) // 1e9))
    noise = 100 * np.random.randn(len(index))
    load = (base + noise).round(2)

    df = pd.DataFrame({"Load_MW": load}, index=index)
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df

# 12. mock Copernicus 1h com outliers


def mock_copernicus_data_1h_with_outliers(start_date, end_date):
    start = pd.Timestamp(start_date, tz="UTC")
    end = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index = pd.date_range(start=start, end=end, freq="1h", tz="UTC")
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

    indices_t2m = df.index[::2]
    indices_ssrd = df.index[::4]

    df.loc[indices_t2m, "t2m"] *= 2
    df.loc[indices_ssrd, "ssrd"] *= 3

    return df

# 13. teste integraçao 1h com outliers


@patch("ingestion.cdsapi.Client")
@patch("ingestion.EntsoePandasClient")
def test_full_pipeline_integration_1h_with_outliers(mock_entsoe, mock_cds):
    (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    ) = setup_dirs()

    fake_path = "/tmp/fake_weather_data"
    fake_df = setup_fake_weather_files(fake_path)

    try:
        # 1. ENTSO‑E
        df_entsoe = mock_entsoe_data_mixed_granularity_clean(
            start_date, end_date)
        entsoe_filename = f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        entsoe_path = os.path.join(raw_energy, entsoe_filename)
        df_entsoe.to_csv(entsoe_path, index=False)

        # 2. Copernicus
        df_copernicus = mock_copernicus_data_mixed_granularity_clean(
            start_date, end_date)
        # exact same name as fetch_copernicus_data
        copernicus_filename = f"era5_timeseries_{start_date}_to_{end_date}.csv"
        copernicus_path = os.path.join(raw_weather, copernicus_filename)
        df_copernicus.to_csv(copernicus_path, index=False)

        # 3.  ingestão
        fetch_entsoe_data(start_date, end_date)
        fetch_copernicus_data(start_date, end_date)

        # 4. energia
        energy(raw_energy, pasta_saida=energy_clean)

        # 5. clima
        with patch("pandas.read_csv", return_value=fake_df):
            weather(pasta_saida=weather_clean)

        # 6. limpeza e junção final
        df_final = cleaning(
            pasta_energy_corrigido=energy_clean,
            pasta_weather_corrigido=weather_clean,
        )

        # 7. CSV final
        REAL_PROCESSED = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
        final_csv = os.path.join(REAL_PROCESSED, "dados_finais_completos.csv")
        assert os.path.exists(final_csv), f"CSV final não existe: {final_csv}"
        assert os.path.getsize(final_csv) > 0

        # 8. verificações
        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in [
                   "t2m", "ssrd", "tp", "u10", "v10"])
        assert df_final.isnull().sum().sum() == 0

        print(
            f"Pipeline 1h com outliers: {len(df_final)} registos no dataset final."
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


##########
#########

# 14.


def mock_entsoe_data_mixed_granularity_clean(start_date, end_date):
    start_15min = pd.Timestamp(start_date, tz="UTC")
    end_15min = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_15min = pd.date_range(
        start=start_15min,
        end=end_15min,
        freq="15min",
        tz="UTC")
    index_15min = index_15min[:-1]

    start_1h = pd.Timestamp(start_date, tz="UTC")
    end_1h = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_1h = pd.date_range(start=start_1h, end=end_1h, freq="1h", tz="UTC")
    index_1h = index_1h[:-1]

    # parte em 15 min
    base_15min = abs(
        5000 +
        1000 *
        np.cos(
            0.01 *
            index_15min.astype(int) //
            1e9))
    noise_15min = 100 * np.random.randn(len(index_15min))
    load_15min = (base_15min + noise_15min).round(2)

    df_15min = pd.DataFrame({"Load_MW": load_15min}, index=index_15min)

    # parte em 1 h
    base_1h = abs(5000 + 1000 * np.cos(0.01 * index_1h.astype(int) // 1e9))
    noise_1h = 100 * np.random.randn(len(index_1h))
    load_1h = (base_1h + noise_1h).round(2)

    df_1h = pd.DataFrame({"Load_MW": load_1h}, index=index_1h)

    # junta os dois
    df = pd.concat([df_15min, df_1h]).sort_index()

    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df

# 15.


def mock_copernicus_data_mixed_granularity_clean(start_date, end_date):
    start_15min = pd.Timestamp(start_date, tz="UTC")
    end_15min = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_15min = pd.date_range(
        start=start_15min,
        end=end_15min,
        freq="15min",
        tz="UTC")
    index_15min = index_15min[:-1]

    start_1h = pd.Timestamp(start_date, tz="UTC")
    end_1h = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_1h = pd.date_range(start=start_1h, end=end_1h, freq="1h", tz="UTC")
    index_1h = index_1h[:-1]

    df_15min = pd.DataFrame(
        {
            "valid_time": index_15min,
            "t2m": 273.15 + 15 + 10 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "d2m": 273.15 + 12 + 8 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "skt": 273.15 + 20 + 12 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "stl1": 273.15 + 18 + 8 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "u10": 5 + 10 * np.random.randn(len(index_15min)),
            "v10": 3 + 8 * np.random.randn(len(index_15min)),
            "ssrd": 200 + 100 * np.random.randn(len(index_15min)),
            "strd": 300 + 200 * np.random.randn(len(index_15min)),
            "sp": 101300 + 1000 * np.random.randn(len(index_15min)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index_15min)),
            "swvl1": 0.3 + 0.1 * np.random.randn(len(index_15min)),
        }
    )

    df_1h = pd.DataFrame(
        {
            "valid_time": index_1h,
            "t2m": 273.15 + 15 + 10 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "d2m": 273.15 + 12 + 8 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "skt": 273.15 + 20 + 12 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "stl1": 273.15 + 18 + 8 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "u10": 5 + 10 * np.random.randn(len(index_1h)),
            "v10": 3 + 8 * np.random.randn(len(index_1h)),
            "ssrd": 200 + 100 * np.random.randn(len(index_1h)),
            "strd": 300 + 200 * np.random.randn(len(index_1h)),
            "sp": 101300 + 1000 * np.random.randn(len(index_1h)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index_1h)),
            "swvl1": 0.3 + 0.1 * np.random.randn(len(index_1h)),
        }
    )

    df = pd.concat([df_15min, df_1h]).sort_values(
        "valid_time").reset_index(drop=True)
    return df

# 16.


@patch("ingestion.cdsapi.Client")
@patch("ingestion.EntsoePandasClient")
def test_full_pipeline_integration_mixed_granularity_datasets_clean(
        mock_entsoe,
        mock_cds):
    (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    ) = setup_dirs()

    fake_path = "/tmp/fake_weather_data"
    fake_df = setup_fake_weather_files(fake_path)

    try:
        # 1. ENTSO‑E
        df_entsoe = mock_entsoe_data_mixed_granularity_clean(
            start_date, end_date)
        entsoe_filename = f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        entsoe_path = os.path.join(raw_energy, entsoe_filename)
        df_entsoe.to_csv(entsoe_path, index=False)

        # 2. Copernicus
        df_copernicus = mock_copernicus_data_mixed_granularity_clean(
            start_date, end_date)
        # exact same name as fetch_copernicus_data
        copernicus_filename = f"era5_timeseries_{start_date}_to_{end_date}.csv"
        copernicus_path = os.path.join(raw_weather, copernicus_filename)
        df_copernicus.to_csv(copernicus_path, index=False)

        # 3.  ingestão
        fetch_entsoe_data(start_date, end_date)
        fetch_copernicus_data(start_date, end_date)

        # 4. energia
        energy(raw_energy, pasta_saida=energy_clean)

        # 5. clima
        with patch("pandas.read_csv", return_value=fake_df):
            weather(pasta_saida=weather_clean)

        # 6. limpeza e junção final
        df_final = cleaning(
            pasta_energy_corrigido=energy_clean,
            pasta_weather_corrigido=weather_clean,
        )

        # 7. CSV final
        REAL_PROCESSED = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
        final_csv = os.path.join(REAL_PROCESSED, "dados_finais_completos.csv")
        assert os.path.exists(final_csv), f"CSV final não existe: {final_csv}"
        assert os.path.getsize(final_csv) > 0

        # 8. verificações
        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in [
                   "t2m", "ssrd", "tp", "u10", "v10"])
        assert df_final.isnull().sum().sum() == 0

        print(
            f"Pipeline datasets mistos (15min/1h) limpos: {len(df_final)} registos no dataset final."
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


##########
#########

# 17. 1h+15min e com NaN


def mock_entsoe_data_mixed_granularity_15min_nan(start_date, end_date):
    start_15min = pd.Timestamp(start_date, tz="UTC")
    end_15min = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_15min = pd.date_range(
        start=start_15min,
        end=end_15min,
        freq="15min",
        tz="UTC")
    index_15min = index_15min[:-1]

    start_1h = pd.Timestamp(start_date, tz="UTC")
    end_1h = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_1h = pd.date_range(start=start_1h, end=end_1h, freq="1h", tz="UTC")
    index_1h = index_1h[:-1]

    # 1. 15 min
    base_15min = abs(
        5000 +
        1000 *
        np.cos(
            0.01 *
            index_15min.astype(int) //
            1e9))
    noise_15min = 100 * np.random.randn(len(index_15min))
    load_15min = np.array((base_15min + noise_15min).round(2))

    nan_every_hour = 4
    load_15min[nan_every_hour::nan_every_hour] = np.nan

    df_15min = pd.DataFrame({"Load_MW": load_15min}, index=index_15min)

    # 2. 1h
    base_1h = abs(5000 + 1000 * np.cos(0.01 * index_1h.astype(int) // 1e9))
    noise_1h = 100 * np.random.randn(len(index_1h))
    load_1h = np.array((base_1h + noise_1h).round(2))

    df_1h = pd.DataFrame({"Load_MW": load_1h}, index=index_1h)

    df = pd.concat([df_15min, df_1h]).sort_index()
    df = df.reset_index().rename(columns={"index": "Unnamed: 0"})
    return df

# 18. 1h+15min com outliers e NaN


def mock_copernicus_data_mixed_granularity_15min_outliers_nan(
        start_date,
        end_date):
    start_15min = pd.Timestamp(start_date, tz="UTC")
    end_15min = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_15min = pd.date_range(
        start=start_15min,
        end=end_15min,
        freq="15min",
        tz="UTC")
    index_15min = index_15min[:-1]

    start_1h = pd.Timestamp(start_date, tz="UTC")
    end_1h = pd.Timestamp(end_date, tz="UTC") + pd.Timedelta(days=1)
    index_1h = pd.date_range(start=start_1h, end=end_1h, freq="1h", tz="UTC")
    index_1h = index_1h[:-1]

    # 15 min → com outliers e NaN
    df_15min = pd.DataFrame(
        {
            "valid_time": index_15min,
            "t2m": 273.15 + 15 + 10 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "d2m": 273.15 + 12 + 8 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "skt": 273.15 + 20 + 12 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "stl1": 273.15 + 18 + 8 * ((index_15min.hour / 24) - 0.5) + np.random.randn(len(index_15min)),
            "u10": 5 + 10 * np.random.randn(len(index_15min)),
            "v10": 3 + 8 * np.random.randn(len(index_15min)),
            "ssrd": 200 + 100 * np.random.randn(len(index_15min)),
            "strd": 300 + 200 * np.random.randn(len(index_15min)),
            "sp": 101300 + 1000 * np.random.randn(len(index_15min)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index_15min)),
            "swvl1": 0.3 + 0.1 * np.random.randn(len(index_15min)),
        }
    )

    # outliers apenas na parte de 15 min
    indices_t2m_15min = df_15min.index[::8]
    indices_ssrd_15min = df_15min.index[::16]

    df_15min.loc[indices_t2m_15min, "t2m"] *= 2
    df_15min.loc[indices_ssrd_15min, "ssrd"] *= 3

    # NaN apenas na parte de 15 min
    mask_t2m_nan_15min = np.random.rand(len(df_15min)) < 0.05
    mask_ssrd_nan_15min = np.random.rand(len(df_15min)) < 0.03
    df_15min.loc[mask_t2m_nan_15min, "t2m"] = np.nan
    df_15min.loc[mask_ssrd_nan_15min, "ssrd"] = np.nan

    # 1h → sem outliers, sem NaN
    df_1h = pd.DataFrame(
        {
            "valid_time": index_1h,
            "t2m": 273.15 + 15 + 10 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "d2m": 273.15 + 12 + 8 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "skt": 273.15 + 20 + 12 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "stl1": 273.15 + 18 + 8 * ((index_1h.hour / 24) - 0.5) + np.random.randn(len(index_1h)),
            "u10": 5 + 10 * np.random.randn(len(index_1h)),
            "v10": 3 + 8 * np.random.randn(len(index_1h)),
            "ssrd": 200 + 100 * np.random.randn(len(index_1h)),
            "strd": 300 + 200 * np.random.randn(len(index_1h)),
            "sp": 101300 + 1000 * np.random.randn(len(index_1h)),
            "tp": 0.1 + 0.05 * np.random.randn(len(index_1h)),
            "swvl1": 0.3 + 0.1 * np.random.randn(len(index_1h)),
        }
    )

    # junta e ordena por valid_time
    df = pd.concat([df_15min, df_1h]).sort_values(
        "valid_time").reset_index(drop=True)
    return df

# 19.


@patch("ingestion.cdsapi.Client")
@patch("ingestion.EntsoePandasClient")
def test_full_pipeline_integration_mixed_granularity_datasets_with_outliers_nan(
        mock_entsoe,
        mock_cds):
    (
        base_dir,
        raw_energy,
        raw_weather,
        energy_clean,
        weather_clean,
        start_date,
        end_date,
    ) = setup_dirs()

    fake_path = "/tmp/fake_weather_data"
    fake_df = setup_fake_weather_files(fake_path)

    try:
        # 1. ENTSO‑E
        df_entsoe = mock_entsoe_data_mixed_granularity_clean(
            start_date, end_date)
        entsoe_filename = f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        entsoe_path = os.path.join(raw_energy, entsoe_filename)
        df_entsoe.to_csv(entsoe_path, index=False)

        # 2. Copernicus
        df_copernicus = mock_copernicus_data_mixed_granularity_clean(
            start_date, end_date)
        # exact same name as fetch_copernicus_data
        copernicus_filename = f"era5_timeseries_{start_date}_to_{end_date}.csv"
        copernicus_path = os.path.join(raw_weather, copernicus_filename)
        df_copernicus.to_csv(copernicus_path, index=False)

        # 3.  ingestão
        fetch_entsoe_data(start_date, end_date)
        fetch_copernicus_data(start_date, end_date)

        # 4. energia
        energy(raw_energy, pasta_saida=energy_clean)

        # 5. clima
        with patch("pandas.read_csv", return_value=fake_df):
            weather(pasta_saida=weather_clean)

        # 6. limpeza e junção final
        df_final = cleaning(
            pasta_energy_corrigido=energy_clean,
            pasta_weather_corrigido=weather_clean,
        )

        # 7. CSV final
        REAL_PROCESSED = "/Users/beatrizfernandes/Desktop/PIACD/projeto/pl1g1/Code/energy_prediction_system/data/processed"
        final_csv = os.path.join(REAL_PROCESSED, "dados_finais_completos.csv")
        assert os.path.exists(final_csv), f"CSV final não existe: {final_csv}"
        assert os.path.getsize(final_csv) > 0

        # 8. verificações básicas
        assert df_final is not None
        assert len(df_final) > 0
        assert "datetime" in df_final.columns
        assert "Load_MW" in df_final.columns
        assert any(var in df_final.columns for var in [
                   "t2m", "ssrd", "tp", "u10", "v10"])

        # 9. mostra NaN finais
        nulos = df_final.isnull().sum()
        print("\nValores em falta no dataset final:")
        print(nulos[nulos > 0])

        print(
            f"Pipeline datasets mistos com outliers/NaN: {len(df_final)} registos no dataset final."
        )
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
