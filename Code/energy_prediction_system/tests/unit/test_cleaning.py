from cleaning import (
    ajust15_energy,
    fill_nan_energy,
    aggregate_hour,
    g15_energy,
    time_alignment_energy,
    g115g1,
    g15min,
    ajust15,
    missingValuesFind,
    temp_termicRad_imputation,
    wind_imputation,
    solar_imputation,
    precip_imputation,
    pressure_imputation,
    soil_imputation,
    media_custom,
    outliers_treatment,
    media_nearest,
    hourly_aggregation,
    convert_era5_units)
import pytest
import pandas as pd
import numpy as np

# =======================================
# DADOS ENERGY
# =======================================


def test_fill_nan_energy_1h_input():
    times = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 11:00"],
        utc=True,
    )
    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [100.0, 110.0],
        }
    )

    df_filled = fill_nan_energy(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_filled["Load_MW"])
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_15min_no_missing():
    times = pd.to_datetime(
        [
            "2023-01-01 10:00",
            "2023-01-01 10:15",
            "2023-01-01 10:30",
            "2023-01-01 10:45",
        ],
        utc=True,
    )
    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [100.0, 101.0, 102.0, 103.0],
        }
    )

    df_filled = fill_nan_energy(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_filled["Load_MW"])
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_15min_one_nan_uses_interpolation():
    times = pd.to_datetime(
        [
            "2023-01-01 10:00",
            "2023-01-01 10:15",
            "2023-01-01 10:30",
            "2023-01-01 10:45",
        ],
        utc=True,
    )
    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [100.0, 105.0, None, 110.0],
        }
    )

    df_filled = fill_nan_energy(df.copy())
    val = df_filled.loc[df_filled["Unnamed: 0"] == times[2], "Load_MW"].iloc[0]
    assert pd.notna(val)
    assert 105.0 <= val <= 110.0
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_15min_multiple_nans_uses_mean_last6():
    times = pd.to_datetime(
        [
            "2023-08-01 09:00",
            "2023-08-01 09:15",
            "2023-08-01 09:30",
            "2023-08-01 09:45",  # 09h
            "2023-08-01 10:00",
            "2023-08-01 10:15",
            "2023-08-01 10:30",
            "2023-08-01 10:45",  # 10h
            "2023-08-01 11:00",
            "2023-08-01 11:15",
            "2023-08-01 11:30",
            "2023-08-01 11:45",  # 11h — 2 NaN
        ],
        utc=True,
    )

    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [
                80.0,
                85.0,
                90.0,
                95.0,
                100.0,
                105.0,
                110.0,
                115.0,
                None,
                None,
                125.0,
                130.0,
            ],
        }
    )

    df_filled = fill_nan_energy(df.copy())

    # para 11:00 e 11:15, usa média das últimas 6 VÁLIDAS antes (9:00–10:45)
    expected_mean = (90 + 95 + 100 + 105 + 110 + 115) / 6
    expected_mean_2 = (expected_mean + 125) / 2

    # Ajusta para 6 últimos válidos antes de 11h
    valid_before = (
        df_filled.loc[df_filled["Unnamed: 0"] <
                      times[8], "Load_MW"].dropna().tail(6)
    )
    expected_mean = valid_before.mean()

    assert pytest.approx(df_filled["Load_MW"].iloc[8]) == expected_mean
    assert pytest.approx(df_filled["Load_MW"].iloc[9]) == expected_mean_2
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_1h_plus_15min_no_missing():
    times_1h = pd.to_datetime(
        ["2022-01-01 00:00", "2022-01-01 01:00"],
        utc=True,
    )
    times_15 = pd.to_datetime(
        [
            "2022-01-01 02:00",
            "2022-01-01 02:15",
            "2022-01-01 02:30",
            "2022-01-01 02:45",
        ],
        utc=True,
    )
    times = pd.concat(
        [
            pd.Series(times_1h),
            pd.Series(times_15),
        ]
    ).reset_index(drop=True)

    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [100.0, 105.0, 110.0, 115.0, 120.0, 125.0],
        }
    )

    df_filled = fill_nan_energy(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_filled["Load_MW"])
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_1h_plus_15min_one_nan_uses_interpolation():
    times_1h = pd.to_datetime(
        ["2022-01-01 00:00", "2022-01-01 01:00"],
        utc=True,
    )
    times_15 = pd.to_datetime(
        [
            "2022-01-01 02:00",
            "2022-01-01 02:15",
            "2022-01-01 02:30",
            "2022-01-01 02:45",
        ],
        utc=True,
    )
    times = pd.concat(
        [
            pd.Series(times_1h),
            pd.Series(times_15),
        ]
    ).reset_index(drop=True)

    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [100.0, 105.0, 110.0, None, 120.0, 125.0],
        }
    )

    df_filled = fill_nan_energy(df.copy())
    val = df_filled.loc[df_filled["Unnamed: 0"] == times[3], "Load_MW"].iloc[0]
    assert pd.notna(val)
    assert 110.0 <= val <= 120.0
    assert df_filled["Load_MW"].isna().sum() == 0


def test_fill_nan_energy_1h_plus_15min_multiple_nans_uses_mean_last6():
    times_1h = pd.to_datetime(
        ["2022-01-01 00:00", "2022-01-01 01:00"],
        utc=True,
    )
    times_15 = pd.to_datetime(
        [
            "2022-01-01 02:00",
            "2022-01-01 02:15",
            "2022-01-01 02:30",
            "2022-01-01 02:45",  # 02h
            "2022-01-01 03:00",
            "2022-01-01 03:15",
            "2022-01-01 03:30",
            "2022-01-01 03:45",  # 03h — 2 NaN
            "2022-01-01 04:00",
            "2022-01-01 04:15",
        ],
        utc=True,
    )

    times = pd.concat(
        [
            pd.Series(times_1h),
            pd.Series(times_15),
        ]
    ).reset_index(drop=True)

    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [
                100.0,
                105.0,  # 1h
                110.0,
                115.0,
                120.0,
                125.0,  # 02h
                130.0,
                135.0,
                None,
                None,  # 03h — 2 NaN
                140.0,
                135.0,
            ],
        }
    )

    df_filled = fill_nan_energy(df.copy())
    expected_mean_1 = (110 + 115 + 120 + 125 + 130 + 135) / 6  # 122.5
    expected_mean_2 = (expected_mean_1 + 140) / 2

    assert pytest.approx(df_filled["Load_MW"].iloc[8]) == expected_mean_1
    assert pytest.approx(df_filled["Load_MW"].iloc[9]) == expected_mean_2
    assert df_filled["Load_MW"].isna().sum() == 0


def test_ajust15_energy_rounds_aggregates_correct():
    times = pd.to_datetime(
        ["2023-01-01 14:10", "2023-01-01 14:12", "2023-01-01 14:32"], utc=True
    )
    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [100.0, 105.0, 110.0]})

    df_adj = ajust15_energy(df.copy())

    # Espera 1 linha (após aggregate da hora 14h)
    assert len(df_adj) == 1
    assert df_adj["Unnamed: 0"].iloc[0].floor("h") == pd.to_datetime(
        "2023-01-01 14:00", utc=True
    )
    assert df_adj["Load_MW"].iloc[0] == 110.0  # Máximo da hora


def test_g15_energy_missing_15min_filled_and_aggregated():
    times = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 10:15", "2023-01-01 10:45"],
        utc=True,
    )
    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [100.0, 105.0, 110.0]})

    df_proc = g15_energy(df.copy())

    assert len(df_proc) == 1
    assert df_proc["Unnamed: 0"].iloc[0] == pd.to_datetime(
        "2023-01-01 10:00", utc=True)
    assert df_proc["Load_MW"].iloc[0] == 110.0  # Máximo da hora 10h
    assert df_proc["Load_MW"].isna().sum() == 0


def test_time_alignment_energy_1h_returns_input():
    times = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 11:00"],
        utc=True,
    )
    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [100.0, 110.0]})
    df_aligned = time_alignment_energy(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_aligned["Load_MW"])


def test_time_alignment_energy_15min_calls_g15_energy():
    times = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 10:15", "2023-01-01 10:30"],
        utc=True,
    )
    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [100.0, 105.0, 110.0]})
    df_aligned = time_alignment_energy(df.copy())
    # g15_energy já faz 15→1h via aggregate_hour
    assert len(df_aligned) == 1
    assert df_aligned["Load_MW"].iloc[0] == 110.0


def test_aggregate_hour_15min_to_1h():
    times = pd.to_datetime(
        [
            "2023-01-01 10:00",
            "2023-01-01 10:15",
            "2023-01-01 10:30",
            "2023-01-01 10:45",
        ],
        utc=True,
    )
    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [
                      100.0, 105.0, 110.0, 108.0]})
    df_agg = aggregate_hour(df.copy())
    assert len(df_agg) == 1
    assert df_agg["Load_MW"].iloc[0] == 110.0


def test_aggregate_hour_1h_input_unchanged():
    times = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 11:00"],
        utc=True,
    )
    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [100.0, 110.0]})
    df_agg = aggregate_hour(df.copy())
    pd.testing.assert_series_equal(df["Load_MW"], df_agg["Load_MW"])


def test_g115g1_1h_plus_15min_processed():
    times_1h = pd.to_datetime(
        ["2022-01-01 00:00", "2022-01-01 01:00"],
        utc=True,
    )
    times_15 = pd.to_datetime(
        [
            "2022-01-01 02:00",
            "2022-01-01 02:15",
            "2022-01-01 02:30",
            "2022-01-01 02:45",
        ],
        utc=True,
    )
    times = pd.concat(
        [
            pd.Series(times_1h),
            pd.Series(times_15),
        ]
    ).reset_index(drop=True)

    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [
        100.0, 105.0, 110.0, 115.0, 120.0, 125.0]})

    df_proc = g115g1(df.copy())
    assert "idx_15_start" in df_proc.attrs

    df_agg = aggregate_hour(df_proc.copy())
    # 00:00, 01:00, 02:00
    assert len(df_agg) == 3

    expected_times = pd.to_datetime(
        ["2022-01-01 00:00", "2022-01-01 01:00", "2022-01-01 02:00"], utc=True
    )
    expected_series = pd.Series(expected_times, name="Unnamed: 0")

    pd.testing.assert_series_equal(
        df_agg["Unnamed: 0"].dt.floor("h").reset_index(drop=True),
        expected_series.reset_index(drop=True),
        check_names=False,  # OU usar esta opção para ignorar nomes
    )


# =======================================
# DADOS WEATHER
# =======================================
def test_g15min_no_gaps_returns_same_df():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=4,
        freq="15min",
        tz="UTC")
    df = pd.DataFrame(
        {
            "valid_time": times,
            "t2m": [10, 11, 12, 13],
            "latitude": [40.0] * 4,
            "longitude": [-8.0] * 4,
        }
    )
    df_filled = g15min(df)
    pd.testing.assert_frame_equal(df, df_filled, check_dtype=False)


def test_g15min_fills_one_missing_interval_and_imputes():
    times = pd.to_datetime(["2023-01-01 10:00", "2023-01-01 10:30"], utc=True)
    df = pd.DataFrame(
        {
            "valid_time": times,
            "t2m": [10, 12],
            "latitude": [40.0, 40.0],
            "longitude": [-8.0, -8.0],
        }
    )

    df_filled = g15min(df)
    expected_times = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 10:15", "2023-01-01 10:30"], utc=True
    )

    assert len(df_filled) == 3
    assert list(df_filled["valid_time"]) == list(expected_times)
    assert not pd.isna(df_filled["t2m"].iloc[1])


def test_g15min_multiple_missing_intervals():
    times = pd.to_datetime(["2023-01-01 10:00", "2023-01-01 10:45"], utc=True)
    df = pd.DataFrame({"valid_time": times, "t2m": [10, 13]})
    df_filled = g15min(df)
    expected_times = pd.date_range(
        "2023-01-01 10:00", "2023-01-01 10:45", freq="15min", tz="UTC"
    )
    assert len(df_filled) == 4
    assert list(df_filled["valid_time"]) == list(expected_times)


# ------


def test_ajust15_rounds_to_15min():
    times = pd.to_datetime(["2023-01-01 10:07", "2023-01-01 10:23"], utc=True)
    df = pd.DataFrame({"valid_time": times, "t2m": [10, 11]})
    df_adjusted = ajust15(df)
    # Verifica arredondamento correto
    assert df_adjusted["valid_time"].iloc[0].minute in [0, 15, 30, 45]
    assert df_adjusted["valid_time"].iloc[1].minute in [0, 15, 30, 45]


# TESTES missingValuesFind
def test_missingValuesFind_single_nan_imputes():
    """Testa imputação simples"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=4,
        freq="15min",
        tz="UTC")
    df = pd.DataFrame(
        {
            "valid_time": times,
            "t2m": [10, None, 12, 13],
            "latitude": [40.0] * 4,
            "longitude": [-8.0] * 4,
        }
    )
    df_imputed = missingValuesFind(df)
    assert not df_imputed["t2m"].isna().any()


# TESTES FUNÇÕES ESPECÍFICAS


def test_temp_termicRad_imputation_media_4prev_2next():
    """t2m: média 4 anteriores + 2 seguintes"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=7,
        freq="15min",
        tz="UTC")
    series = pd.Series([10, 11, 12, 13, np.nan, 15, 16], index=times)
    result = temp_termicRad_imputation(series)
    expected = (10 + 11 + 12 + 13 + 15 + 16) / 6  # 12.833
    assert pytest.approx(result.iloc[4], rel=1e-6) == expected


def test_wind_imputation_media_last3():
    """u10/v10: média últimas 3"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=5,
        freq="15min",
        tz="UTC")
    series = pd.Series([2, 2.5, 3, np.nan, 4], index=times)
    result = wind_imputation(series)
    expected = (2 + 2.5 + 3) / 3  # 2.5
    assert pytest.approx(result.iloc[3], rel=1e-6) == expected


def test_solar_imputation_night_zero():
    """ssrd: noite (00-04h) = 0"""
    times = pd.date_range("2023-01-01 00:00", periods=3, freq="h", tz="UTC")
    series = pd.Series([np.nan, 0, np.nan], index=times)
    result = solar_imputation(series)
    pd.testing.assert_series_equal(
        result.fillna(0), pd.Series([0.0, 0.0, 0.0], index=times, dtype=float)
    )


def test_precip_imputation_surrounded_by_zeros():
    """tp: rodeado de 0s → 0"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=5,
        freq="15min",
        tz="UTC")
    series = pd.Series([0, 0, np.nan, 0, 0], index=times)
    result = precip_imputation(series)
    assert pytest.approx(result.iloc[2], rel=1e-6) == 0


def test_pressure_imputation_media_last4():
    """sp: média das últimas 4 observações válidas anteriores"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=6,
        freq="15min",
        tz="UTC")
    series = pd.Series([1012.8, 1013.0, 1013.2, 1013.5,
                       np.nan, 1014.0], index=times)
    result = pressure_imputation(series)

    expected = (1012.8 + 1013.0 + 1013.2 + 1013.5) / 4
    assert pytest.approx(result.iloc[4], rel=1e-6) == expected


def test_soil_imputation_media_last6():
    """swvl1: média últimas 6"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=7,
        freq="15min",
        tz="UTC")
    series = pd.Series(
        [0.3, 0.31, 0.32, 0.33, 0.34, 0.35, np.nan], index=times)
    result = soil_imputation(series)
    expected = (0.3 + 0.31 + 0.32 + 0.33 + 0.34 + 0.35) / 6  # 0.325
    assert pytest.approx(result.iloc[6], rel=1e-6) == expected


def test_media_custom_correct_window():
    """Testa media_custom"""
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=7,
        freq="15min",
        tz="UTC")
    series = pd.Series([1, 2, 3, 4, np.nan, 6, 7], index=times)
    result = media_custom(series, n_prev=2, n_next=2)
    # Verifica que preencheu NaN
    assert pd.notna(result.iloc[4])


# OUTLIERS
def test_outliers_treatment_t2m_physical_outlier_uses_media_custom():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=10,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 10,
            "longitude": [-8.0] * 10,
            "t2m": [8.0, 9.0, 10.0, 11.0, -45.0, 12.0, 13.0, 14.0, 15.0, 16.0],
        }
    )

    df_result = outliers_treatment(df.copy())
    assert pytest.approx(
        df_result.loc[4, "t2m"], rel=1e-6) == 10.5  # ✓ CORRETO
    assert df_result.loc[4, "t2m"] >= -40


def test_outliers_treatment_stl1_iqr_but_physical_ok_not_treated():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=9,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 9,
            "longitude": [-8.0] * 9,
            # ← 50 é outlier IQR mas OK físico
            "stl1": [20, 21, 22, 23, 50.0, 24, 25, 26, 27],
        }
    )

    df_result = outliers_treatment(df.copy())

    # NÃO deve ser alterado (só trata se VIOLAR limite físico)
    assert df_result.loc[4, "stl1"] == 50.0


def test_outliers_treatment_ssrd_physical_and_iqr_outlier_uses_media_nearest():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=7,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 7,
            "longitude": [-8.0] * 7,
            "ssrd": [100, 110, -10.0, 120, 130, 140, 150],  # ← NEGATIVO
        }
    )

    df_result = outliers_treatment(df.copy())
    assert pytest.approx(
        df_result.loc[2, "ssrd"], rel=1e-6) == 105.0  # ✓ CORRETO
    assert df_result.loc[2, "ssrd"] >= 0


def test_outliers_treatment_tp_iqr_but_physical_ok_not_treated():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=9,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 9,
            "longitude": [-8.0] * 9,
            # ← 20 é IQR mas OK físico
            "tp": [1.0, 1.2, 1.5, 1.8, 20.0, 2.0, 2.2, 2.5, 3.0],
        }
    )

    df_result = outliers_treatment(df.copy())

    # NÃO tratado (só trata se >55)
    assert df_result.loc[4, "tp"] == 20.0


def test_outliers_treatment_swvl1_iqr_only_uses_media_custom_6_0():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=10,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame({"valid_time": times,
                       "latitude": [40.0] * 10,
                       "longitude": [-8.0] * 10,
                       "swvl1": [0.20,
                                 0.21,
                                 0.22,
                                 0.23,
                                 0.24,
                                 0.25,
                                 0.90,
                                 0.26,
                                 0.27,
                                 0.28],
                       })

    df_result = outliers_treatment(df.copy())
    assert pytest.approx(df_result.loc[6, "swvl1"], rel=1e-6) == 0.225


def test_outliers_treatment_no_outliers_returns_same():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=4,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 4,
            "longitude": [-8.0] * 4,
            "t2m": [10.0, 11.0, 12.0, 13.0],
        }
    )

    df_result = outliers_treatment(df.copy())
    pd.testing.assert_series_equal(df["t2m"], df_result["t2m"])


# agregação hora em hora
def test_hourly_aggregation_already_hourly_returns_same():
    times = pd.date_range("2023-01-01 10:00", periods=2, freq="1h", tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 2,
            "longitude": [-8.0] * 2,
            "t2m": [10.0, 12.0],
        }
    )

    df_result = hourly_aggregation(df.copy())

    # Deve manter EXATAMENTE igual
    pd.testing.assert_frame_equal(df, df_result)


def test_hourly_aggregation_15min_to_hourly_single_column_mean():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=8,
        freq="15min",
        tz="UTC")

    df = pd.DataFrame(
        {
            "valid_time": times,
            "latitude": [40.0] * 8,
            "longitude": [-8.0] * 8,
            # 10h=11.5, 11h=24.25
            "t2m": [10.0, 11.0, 12.0, 13.0, 15.0, 30.0, 25.0, 27.0],
        }
    )

    df_result = hourly_aggregation(df.copy())

    # Deve ter 2 linhas (10:00 e 11:00)
    assert len(df_result) == 2
    assert df_result.loc[0, "valid_time"].hour == 10  # 10:00
    assert df_result.loc[1, "valid_time"].hour == 11  # 11:00

    # Médias corretas
    # (10+11+12+13)/4
    assert pytest.approx(df_result.loc[0, "t2m"], rel=1e-6) == 11.5
    assert pytest.approx(
        df_result.loc[1, "t2m"], rel=1e-6) == 24.25  # (15+30+25+27)/4

    # lat/lon inalterados
    assert df_result["latitude"].iloc[0] == 40.0
    assert df_result["longitude"].iloc[0] == -8.0


def test_weather_pipeline_completo():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=8,
        freq="15min",
        tz="UTC")
    df = pd.DataFrame(
        {
            "valid_time": times,
            "t2m": [10, 11, np.nan, 13, -50, 15, np.nan, 17],
            "u10": [2, np.nan, 3, 4, 5, 6, np.nan, 8],
            "v10": [1, 2, np.nan, 4, 5, 6, 7, 8],
            "ssrd": [-10, 100, 200, np.nan, 300, 400, 500, 600],
            "tp": [0, 0, 60, 0, 0, 0, 0, 0],
            "sp": [1013, np.nan, np.nan, 1015, 1016, 1017, 1018, 1019],
            "swvl1": [0.2, 0.3, 0.9, 0.25, 0.26, 0.27, 0.28, 0.29],
            "latitude": [40.0] * 8,
            "longitude": [-8.0] * 8,
        }
    )

    df1 = g15min(df.copy())
    df2 = ajust15(df1)
    df3 = missingValuesFind(df2)
    df4 = outliers_treatment(df3)
    df_final = hourly_aggregation(df4)

    assert len(df_final) >= 2
    assert df_final["t2m"].isna().sum() == 0
    assert df_final["ssrd"].min() >= 0


def test_coverage_final_push():
    # Energy simples
    times_e = pd.to_datetime(
        ["2023-01-01 10:00", "2023-01-01 11:00"], utc=True)
    df_energy = pd.DataFrame({"Unnamed: 0": times_e, "Load_MW": [100, 110]})
    result_energy = fill_nan_energy(df_energy.copy())

    times_w = pd.date_range(
        "2023-01-01 10:00",
        periods=4,
        freq="15min",
        tz="UTC")
    df_weather = pd.DataFrame(
        {
            "valid_time": times_w,
            "t2m": [10, np.nan, 12, 13],
            "latitude": [40.0] * 4,
            "longitude": [-8.0] * 4,
        }
    )

    result_weather1 = missingValuesFind(df_weather.copy())
    result_weather2 = outliers_treatment(result_weather1)
    result_weather3 = hourly_aggregation(result_weather2)

    assert len(result_energy) == 2
    assert not result_weather3["t2m"].isna().any()
    assert len(result_weather3) == 1


def test_media_nearest_basic():
    times = pd.date_range(
        "2023-01-01 10:00",
        periods=5,
        freq="15min",
        tz="UTC")
    series = pd.Series([10, 11, np.nan, 13, 14], index=times)
    result = media_nearest(series)
    assert pytest.approx(result.iloc[2], rel=1e-6) == 10.5


def test_fill_nan_energy_primeira_linha_nan():
    times = pd.to_datetime(
        [
            "2023-01-01 10:00",
            "2023-01-01 10:15",
            "2023-01-01 10:30",
            "2023-01-01 10:45",
        ],
        utc=True,
    )

    df = pd.DataFrame(
        {
            "Unnamed: 0": times,
            "Load_MW": [None, 105.0, 110.0, 115.0],  # Primeira linha NaN
        }
    )

    df_filled = fill_nan_energy(df.copy())

    assert df_filled.loc[0, "Load_MW"] == 105.0
    assert not df_filled["Load_MW"].isna().any()
    assert len(df_filled) == 4


def test_time_alignment_energy_mixed_intervals_g115g1():
    times = pd.to_datetime(
        [
            "2023-01-01 10:00",
            "2023-01-01 11:00",
            "2023-01-01 12:00",
            "2023-01-01 12:15",
            "2023-01-01 12:30",
        ],
        utc=True,
    )

    df = pd.DataFrame(
        {"Unnamed: 0": times, "Load_MW": [100, 110, 120, 125, 130]})

    result = time_alignment_energy(df.copy())
    assert "idx_15_start" in result.attrs


def test_g115g1_no_transition_returns_original():
    times = pd.to_datetime(
        [
            "2023-01-01 10:00",
            "2023-01-01 11:00",  # Sempre 1h
            "2023-01-01 12:00",
            "2023-01-01 13:00",
        ],
        utc=True,
    )

    df = pd.DataFrame({"Unnamed: 0": times, "Load_MW": [100, 110, 120, 130]})

    result = g115g1(df.copy())
    assert "idx_15_start" not in result.attrs
    pd.testing.assert_frame_equal(df, result, check_dtype=False)


def test_convert_era5_units_all_conversions():
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
            # Pa → hPa
            "sp": [101325, 102000],
            # m → mm
            "tp": [0.001, 0.005],
        }
    )

    result = convert_era5_units(df.copy())
    assert pytest.approx(result["t2m"].iloc[0]) == 0.0
    assert pytest.approx(result["ssrd"].iloc[0]) == 1.0
    assert pytest.approx(result["sp"].iloc[0]) == 1013.25
    assert pytest.approx(result["tp"].iloc[0]) == 1.0
