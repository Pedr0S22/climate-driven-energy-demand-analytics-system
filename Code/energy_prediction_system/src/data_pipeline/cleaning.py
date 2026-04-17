import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Modular Data Cleaning Pipeline for Energy and Weather data.

    Refactored for high performance using vectorized Pandas operations where possible,
    and targeted loops for mathematical correctness on missing value imputation.
    Follows UC2 requirements and supports Real-Time data processing.
    """

    def __init__(self):
        # Physical limits for data validation (UC2)
        # u10 and v10 are vector components and can be negative.
        self.physical_limits = {
            "t2m": (-40, 55),
            "skt": (-40, 55),
            "d2m": (-40, 55),
            "stl1": (-40, 65),
            "u10": (-69.4, 69.4),
            "v10": (-69.4, 69.4),
            "tp": (0, 55),
            "ssrd": (0, float("inf")),
        }
        self.iqr_only_vars = ["strd", "sp", "swvl1"]

    # =======================================
    # ENERGY PROCESSING
    # =======================================

    def fill_nan_energy(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        UC2 Imputation for Electricity Load:
        - Isolated (1 per hour): Linear interpolation.
        - Multiple (>1 per hour): Mean of the last 6 valid observations.
        """
        df = df.copy()
        df["Load_MW"] = pd.to_numeric(df["Load_MW"], errors="coerce")
        if df["Load_MW"].isna().sum() == 0:
            return df

        time_col = "datetime" if "datetime" in df.columns else "Unnamed: 0"
        df[time_col] = pd.to_datetime(df[time_col], utc=True)

        # Legacy Rule: First row NaN -> copy from next row
        if pd.isna(df.loc[0, "Load_MW"]) and len(df) > 1:
            if pd.notna(df.loc[1, "Load_MW"]):
                df.loc[0, "Load_MW"] = df.loc[1, "Load_MW"]

        # Identify isolated vs multiple NaNs in 1-hour window
        nan_counts = df["Load_MW"].isna().groupby(df[time_col].dt.floor("h")).transform("sum")

        # Pre-calculate candidate values
        interp = df["Load_MW"].interpolate(method="linear")

        # Mean of exactly the LAST 6 valid observations (UC2 Multiple rule)
        valid_only = df["Load_MW"].dropna()
        rolling_mean_6 = valid_only.rolling(window=6, min_periods=1).mean()
        rolling_mean_6 = rolling_mean_6.reindex(df.index, method="ffill")

        mask_isolated = (df["Load_MW"].isna()) & (nan_counts == 1)
        mask_multiple = (df["Load_MW"].isna()) & (nan_counts > 1)

        df.loc[mask_isolated, "Load_MW"] = interp[mask_isolated]
        df.loc[mask_multiple, "Load_MW"] = rolling_mean_6[mask_multiple]

        # Final fallback for start of dataset
        df["Load_MW"] = df["Load_MW"].ffill().bfill()
        return df

    def aggregate_hourly_energy(self, df: pd.DataFrame) -> pd.DataFrame:
        """UC2: Aggregate 15-min to 1-hour using MAX for load."""
        time_col = "datetime" if "datetime" in df.columns else "Unnamed: 0"
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        df["hour"] = df[time_col].dt.floor("h")
        df_hourly = df.groupby("hour")["Load_MW"].max().reset_index()
        df_hourly = df_hourly.rename(columns={"hour": time_col})
        return df_hourly

    def clean_energy_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main entry point for energy cleaning."""
        time_col = "Unnamed: 0" if "Unnamed: 0" in df.columns else "datetime"
        df = df.copy()
        # UC2: Timestamp Rounding
        df[time_col] = pd.to_datetime(df[time_col], utc=True).dt.round("15min")
        return self._align_15min_energy(df)

    def _align_15min_energy(self, df: pd.DataFrame) -> pd.DataFrame:
        """UC2: Time Alignment & Missing Rows insertion."""
        time_col = "Unnamed: 0" if "Unnamed: 0" in df.columns else "datetime"
        df = df.set_index(time_col).sort_index()
        df = df[~df.index.duplicated(keep="first")]

        # Continuous 15-min interval index
        new_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq="15min", name=time_col)
        df_aligned = df.reindex(new_index).reset_index()

        df_imputed = self.fill_nan_energy(df_aligned)
        return self.aggregate_hourly_energy(df_imputed)

    # =======================================
    # WEATHER PROCESSING
    # =======================================

    def clean_weather_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Modular weather cleaning for a single file/dataset."""
        df = df.copy()
        df = self.convert_era5_units(df)
        time_col = "valid_time" if "valid_time" in df.columns else "datetime"
        df[time_col] = pd.to_datetime(df[time_col], utc=True).dt.round("15min")

        df_aligned = self._align_weather_time(df)
        df_imputed = self._impute_missing_weather(df_aligned)
        df_no_outliers = self.treat_weather_outliers(df_imputed)
        return self.aggregate_hourly_weather(df_no_outliers)

    def convert_era5_units(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for var in ["skt", "t2m", "d2m", "stl1"]:
            if var in df.columns:
                df[var] = df[var] - 273.15
        for var in ["ssrd", "strd"]:
            if var in df.columns:
                df[var] = df[var] / 900
        if "sp" in df.columns:
            df["sp"] = df["sp"] / 100
        if "tp" in df.columns:
            df["tp"] = df["tp"] * 1000
        return df

    def _align_weather_time(self, df: pd.DataFrame) -> pd.DataFrame:
        time_col = "valid_time" if "valid_time" in df.columns else "datetime"
        df = df.set_index(time_col).sort_index()
        df = df[~df.index.duplicated(keep="first")]
        new_index = pd.date_range(start=df.index.min(), end=df.index.max(), freq="15min", name=time_col)
        return df.reindex(new_index).reset_index()

    def _impute_missing_weather(self, df: pd.DataFrame) -> pd.DataFrame:
        time_col = "valid_time" if "valid_time" in df.columns else "datetime"
        ignore = [time_col, "latitude", "longitude"]
        vars_to_impute = [c for c in df.columns if c not in ignore]

        df = df.copy().set_index(time_col)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)

        for var in vars_to_impute:
            df[var] = self._impute_var(df, var)
        return df.reset_index()

    def _impute_var(self, df: pd.DataFrame, var: str) -> pd.Series:
        """UC2 Imputation rules for weather."""
        series = df[var]
        mask_nan = series.isna()
        if not mask_nan.any():
            return series

        nan_counts = mask_nan.groupby(series.index.floor("1h")).transform("sum")
        mask_isolated = mask_nan & (nan_counts == 1)
        mask_multiple = mask_nan & (nan_counts > 1)

        result = series.copy()

        # Case 1: Isolated -> Linear Interpolation
        if mask_isolated.any():
            interp = series.interpolate(method="linear", limit_direction="both")
            result.loc[mask_isolated] = interp.loc[mask_isolated]

        # Case 2: Multiple -> Rule-based windows
        if mask_multiple.any():
            if var in ["t2m", "skt", "stl1", "d2m", "strd"]:
                custom = self._media_custom(series, 4, 2)
            elif var in ["u10", "v10"]:
                custom = self._media_custom(series, 3, 0)
            elif var == "ssrd":
                custom = self._solar_impute(series)
            elif var == "tp":
                custom = self._precip_impute(series)
            elif var == "sp":
                custom = self._media_custom(series, 4, 0)
            elif var == "swvl1":
                custom = self._media_custom(series, 6, 0)
            else:
                custom = series.interpolate(method="linear", limit_direction="both")

            result.loc[mask_multiple] = custom.loc[mask_multiple]

        return result.ffill().bfill()

    def _media_custom(self, series: pd.Series, n_prev: int, n_next: int) -> pd.Series:
        """Matches legacy media_custom: index-window based mean."""
        s = series.copy()
        res = s.copy()
        nan_indices = s.index[s.isna()]
        if len(nan_indices) == 0:
            return s

        # Convert to row-index for slicing parity
        s_values = s.values
        idx_map = {val: i for i, val in enumerate(s.index)}

        for dt in nan_indices:
            i = idx_map[dt]
            start = max(0, i - n_prev)
            end = min(len(s), i + n_next + 1)
            window = s_values[start:end]
            valid_window = window[~pd.isna(window)]
            if len(valid_window) > 0:
                res.loc[dt] = np.mean(valid_window)
        return res

    def _solar_impute(self, series: pd.Series) -> pd.Series:
        """Solar Radiation logic: Night=0, else custom(4,2)."""
        hour = series.index.hour
        is_night = (hour >= 22) | (hour <= 4)
        custom = self._media_custom(series, 4, 2)
        result = series.copy()
        result.loc[is_night & series.isna()] = 0.0
        result.loc[~is_night & series.isna()] = custom
        return result

    def _precip_impute(self, series: pd.Series) -> pd.Series:
        """Precipitation logic: Surround zero check."""
        s = series.astype(float)
        # Surround zeros check
        zeros = (s.shift(1) == 0) & (s.shift(-1) == 0)
        custom = self._media_custom(s, 3, 0)
        result = s.copy()
        result.loc[zeros & s.isna()] = 0.0
        result.loc[~zeros & s.isna()] = custom
        return result

    def treat_weather_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """IQR and Physical Limits outlier treatment."""
        time_col = "valid_time" if "valid_time" in df.columns else "datetime"
        ignore = [time_col, "latitude", "longitude"]
        vars_to_check = [c for c in df.columns if c not in ignore]

        df = df.copy().set_index(time_col)
        for var in vars_to_check:
            q1, q3 = df[var].quantile(0.25), df[var].quantile(0.75)
            iqr = q3 - q1
            low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            candidatos = (df[var] < low) | (df[var] > high)

            if var in self.physical_limits:
                l_min, l_max = self.physical_limits[var]
                reais = candidatos & ((df[var] < l_min) | (df[var] > l_max))
                if reais.any():
                    df.loc[reais, var] = np.nan
                    if var in ["t2m", "skt", "d2m", "stl1", "u10", "v10"]:
                        df[var] = self._media_custom(df[var], 4, 2)
                    elif var in ["ssrd", "tp"]:
                        df[var] = self._media_nearest(df[var], 2)
            elif var in self.iqr_only_vars:
                if candidatos.any():
                    df.loc[candidatos, var] = np.nan
                    if var == "strd":
                        df[var] = self._media_nearest(df[var], 2)
                    elif var == "sp":
                        df[var] = self._media_custom(df[var], 4, 2)
                    elif var == "swvl1":
                        df[var] = self._media_custom(df[var], 6, 0)
        return df.reset_index()

    def _media_nearest(self, series: pd.Series, n: int) -> pd.Series:
        """Mean of n closest valid observations."""
        s = series.copy()
        valid = s.dropna()
        if valid.empty:
            return s
        res = s.copy()
        nan_indices = s.index[s.isna()]
        for idx in nan_indices:
            diff_sec = pd.Series(np.abs((valid.index - idx).total_seconds()), index=valid.index)
            closest_indices = diff_sec.nsmallest(n).index
            res.loc[idx] = valid.loc[closest_indices].mean()
        return res

    def aggregate_hourly_weather(self, df: pd.DataFrame) -> pd.DataFrame:
        """UC2: Aggregate 15-min to 1-hour using MEAN for weather."""
        time_col = "valid_time" if "valid_time" in df.columns else "datetime"
        df = df.copy()
        df["hour_group"] = df[time_col].dt.floor("h")
        cols_agg = [c for c in df.columns if c not in [time_col, "latitude", "longitude", "hour_group"]]
        df_hourly = df.groupby("hour_group")[cols_agg].mean().reset_index()
        df_hourly = df_hourly.rename(columns={"hour_group": time_col})
        return df_hourly

    def create_daily_aggregation(self, df_hourly: pd.DataFrame) -> pd.DataFrame:
        """Derives daily dataset: Sum for load, Mean for climate."""
        df = df_hourly.copy()
        df["date"] = df["datetime"].dt.date
        agg_rules = {col: "mean" for col in df.columns if col not in ["datetime", "date", "Load_MW"]}
        agg_rules["Load_MW"] = "sum"
        df_daily = df.groupby("date").agg(agg_rules).reset_index()
        df_daily = df_daily.rename(columns={"date": "datetime", "Load_MW": "Load_MWh"})
        df_daily["datetime"] = pd.to_datetime(df_daily["datetime"], utc=True)
        return df_daily


def cleaning(energy_dir, weather_dir, train_data, output_dir=None):
    """
    Unified cleaning entry point.
    Processes weather files individually to match legacy behavior and ensure correctness.
    Supports real-time predictions by consolidating data into separate folders.
    """
    root = Path(__file__).parent.parent.parent

    # Path logic for Real-Time vs Batch
    if train_data:
        default_folder = root / "data" / "processed"
        prefix = "complete_train_data"
    else:
        # Real-time/Prediction specific folder
        default_folder = root / "data" / "processed" / "real-time"
        prefix = "prediction_data"

    output_path = Path(output_dir or default_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    cleaner = DataCleaner()

    # 1. Energy
    logger.info("Cleaning Energy data...")
    energy_files = sorted(Path(energy_dir).glob("*.csv"))
    if not energy_files:
        raise FileNotFoundError(f"No energy files in {energy_dir}")
    df_energy_raw = pd.concat([pd.read_csv(f) for f in energy_files], ignore_index=True)
    df_e = cleaner.clean_energy_dataframe(df_energy_raw)
    df_e = df_e.rename(columns={df_e.columns[0]: "datetime"})
    df_e = df_e[["datetime", "Load_MW"]].drop_duplicates("datetime")

    # 2. Weather (Individual file cleaning then join)
    logger.info("Cleaning Weather files individually...")
    weather_files = sorted(Path(weather_dir).glob("*.csv"))
    if not weather_files:
        raise FileNotFoundError(f"No weather files in {weather_dir}")

    weather_dfs_hourly = []
    for f in weather_files:
        df_w_raw = pd.read_csv(f)
        df_w_clean = cleaner.clean_weather_dataframe(df_w_raw)
        time_col = "datetime" if "datetime" in df_w_clean.columns else "valid_time"
        df_w_clean = df_w_clean.rename(columns={time_col: "datetime"})
        cols_to_keep = [c for c in df_w_clean.columns if c not in ["latitude", "longitude", "hour_group"]]
        weather_dfs_hourly.append(df_w_clean[cols_to_keep])

    # Outer join weather variables
    df_weather_combined = weather_dfs_hourly[0]
    for df in weather_dfs_hourly[1:]:
        df_weather_combined = pd.merge(df_weather_combined, df, on="datetime", how="outer")

    df_weather_final = df_weather_combined.groupby("datetime").mean(numeric_only=True).reset_index()

    # 3. Join
    df_hourly = pd.merge(df_weather_final, df_e, on="datetime", how="inner")
    df_hourly = df_hourly.sort_values("datetime").reset_index(drop=True)

    # 4. Daily
    df_daily = cleaner.create_daily_aggregation(df_hourly)

    # 5. Export
    hourly_file = output_path / f"{prefix}_hourly.csv"
    daily_file = output_path / f"{prefix}_daily.csv"

    # For real-time, we might want to append or overwrite.
    # Usually, we overwrite the consolidated prediction file with the full updated history.
    df_hourly.to_csv(hourly_file, index=False)
    df_daily.to_csv(daily_file, index=False)

    logger.info(f"Synchronized Dataset: {df_hourly.shape[0]} rows. Saved to {output_path}")
    return df_hourly, df_daily


if __name__ == "__main__":
    ROOT = Path(__file__).parent.parent.parent
    DATA_RAW = ROOT / "data" / "raw"
    start = time.time()
    cleaning(energy_dir=DATA_RAW / "energy", weather_dir=DATA_RAW / "weather", train_data=True)
    logger.info(f"Total processing time: {time.time() - start:.2f}s")
