import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import iqr
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.preprocessing import StandardScaler

# =======================================
# CONFIGURATION AND CONSTANTS
# =======================================

# Plausible physical limits for domain validation (in Celsius)
PHYSICAL_LIMITS = {
    "t2m": (-50.0, 60.0),  # -50°C to 60°C
    "skt": (-50.0, 70.0),  # -50°C to 70°C
    "Load_MW": (0, 1000000),  # Positive load
}

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_data(file_path: Path) -> pd.DataFrame:
    """
    Loads synchronized data from the specified CSV file.

    Args:
        file_path (Path): Path to the synchronized CSV file.

    Returns:
        pd.DataFrame: Loaded and sorted DataFrame.
    """
    logger.info(f"Loading data from: {file_path}")
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Missing data at {file_path}")

    df = pd.read_csv(file_path)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        df = df.sort_values("datetime").reset_index(drop=True)
    return df


def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts temporal features such as hour, day of week, and seasonal indicators.

    Args:
        df (pd.DataFrame): Input DataFrame with a 'datetime' column.

    Returns:
        pd.DataFrame: DataFrame with added temporal features.
    """
    logger.info("Extracting temporal features...")
    df = df.copy()

    if "datetime" not in df.columns:
        logger.warning("Datetime column missing. Skipping temporal feature extraction.")
        return df

    # Hour of the day (0-23)
    df["hour"] = df["datetime"].dt.hour

    # Day of the week (0-6, where 0 is Monday)
    df["day_of_week"] = df["datetime"].dt.dayofweek

    # Month (1-12)
    df["month"] = df["datetime"].dt.month

    # Seasonal indicators
    # 1: Winter (Dec, Jan, Feb)
    # 2: Spring (Mar, Abr, Mai)
    # 3: Summer (Jun, Jul, Ago)
    # 4: Autumn (Set, Out, Nov)
    def get_season(month):
        if month in [12, 1, 2]:
            return 1
        elif month in [3, 4, 5]:
            return 2
        elif month in [6, 7, 8]:
            return 3
        else:
            return 4

    df["season"] = df["month"].apply(get_season)

    return df


def calculate_crossing_rate(series, reference="mean"):
    """
    Calculates the crossing rate (Zero Crossing or Mean Crossing).

    Args:
        series (pd.Series): Input numeric series.
        reference (str): 'zero' for Zero Crossing Rate, 'mean' for Mean Crossing Rate.

    Returns:
        float: Calculated crossing rate.
    """
    if len(series) <= 1:
        return 0

    if reference == "mean":
        ref_val = series.mean()
    else:
        ref_val = 0

    shifted_series = series - ref_val
    # Count sign changes
    crossings = ((shifted_series.shift(1) * shifted_series) < 0).sum()
    return crossings / (len(series) - 1)


def extract_rolling_features(df: pd.DataFrame, climate_cols: list, window_size: int = 24) -> pd.DataFrame:
    """
    Extracts rolling window features for climate variables.
    Optimized for performance:
    - Basic stats for all columns (vectorized).
    - Advanced stats for key columns only.
    - Extremely expensive stats (IQR, ZCR, MCR) for t2m only.

    Args:
        df (pd.DataFrame): Input DataFrame.
        climate_cols (list): List of columns to apply rolling features.
        window_size (int): Size of the rolling window.

    Returns:
        pd.DataFrame: DataFrame with added rolling features.
    """
    logger.info(f"Extracting rolling features (window={window_size})...")
    df = df.copy()

    # Key variables for more intensive analysis
    key_vars = ["t2m", "skt", "ssrd", "tp"]

    for col in climate_cols:
        if col not in df.columns:
            continue

        rolling = df[col].rolling(window=window_size)

        # 1. Basic Statistics (All columns - fast/vectorized)
        df[f"{col}_rolling_mean"] = rolling.mean()
        df[f"{col}_rolling_std"] = rolling.std()

        # 2. Advanced Statistics (Key columns only - slightly slower)
        if col in key_vars:
            df[f"{col}_rolling_median"] = rolling.median()
            df[f"{col}_rolling_var"] = rolling.var()

            # Root Mean Square (RMS) - Vectorized
            df[f"{col}_rolling_rms"] = np.sqrt((df[col] ** 2).rolling(window=window_size).mean())

            # Average Derivatives - Vectorized
            df[f"{col}_rolling_deriv"] = df[col].diff().abs().rolling(window=window_size).mean()

            # Shape features: Skewness and Kurtosis - Optimized Pandas
            df[f"{col}_rolling_skew"] = rolling.skew()
            df[f"{col}_rolling_kurt"] = rolling.kurt()

        # 3. Expensive Statistics (Primary column only - slow/apply)
        if col == "t2m":
            # Spread features: Interquartile Range (IQR)
            df[f"{col}_rolling_iqr"] = rolling.apply(lambda x: iqr(x) if len(x) > 1 else 0, raw=True)

            # Temporal features: Crossing Rates
            df[f"{col}_rolling_zcr"] = rolling.apply(
                lambda x: calculate_crossing_rate(pd.Series(x), reference="zero"), raw=False
            )
            df[f"{col}_rolling_mcr"] = rolling.apply(
                lambda x: calculate_crossing_rate(pd.Series(x), reference="mean"), raw=False
            )

    # Pairwise Correlation (only between t2m and skt)
    if "t2m" in df.columns and "skt" in df.columns:
        df["t2m_skt_corr"] = df["t2m"].rolling(window=window_size).corr(df["skt"])

    return df


def extract_lagged_features(df: pd.DataFrame, target_col: str = "Load_MW") -> pd.DataFrame:
    """
    Extracts lagged features for the target variable (L1, L24, L168).

    Args:
        df (pd.DataFrame): Input DataFrame.
        target_col (str): Name of the target variable column.

    Returns:
        pd.DataFrame: DataFrame with added lagged features.
    """
    logger.info("Extracting lagged features...")
    df = df.copy()

    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' missing. Skipping lagged features.")
        return df

    # L1 Load: Electrical load one hour ago
    df["L1_Load"] = df[target_col].shift(1)

    # L24 Load: Load one day ago (24 hours)
    df["L24_Load"] = df[target_col].shift(24)

    # L168 Load: Load one week ago (168 hours)
    df["L168_Load"] = df[target_col].shift(168)

    return df


def extract_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derives advanced features such as temperature anomalies, HDD/CDD, and heatwave flags.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with added derived features.
    """
    logger.info("Extracting derived features...")
    df = df.copy()

    if "t2m" in df.columns:
        # Temperature anomalies (deviation from monthly mean)
        if "month" in df.columns:
            df["temp_monthly_mean"] = df.groupby("month")["t2m"].transform("mean")
            df["temp_anomaly"] = df["t2m"] - df["temp_monthly_mean"]
            df = df.drop(columns=["temp_monthly_mean"])

        # Climatic Indicators: Heating Degree Days (HDD) and Cooling Degree Days (CDD)
        # Base temperature: 18°C = 291.15 K
        T_base = 291.15
        df["HDD"] = df["t2m"].apply(lambda x: max(0, T_base - x))
        df["CDD"] = df["t2m"].apply(lambda x: max(0, x - T_base))

        # Heatwave / Coldwave Flags (persistent extremes for 72 hours)
        # Defined here as the top 10% and bottom 10% of overall temperature
        q_high = df["t2m"].quantile(0.9)
        q_low = df["t2m"].quantile(0.1)

        df["is_extreme_heat"] = (df["t2m"] > q_high).astype(int)
        df["is_extreme_cold"] = (df["t2m"] < q_low).astype(int)

        # Rolling min over 72h window ensures persistence
        df["heatwave_flag"] = df["is_extreme_heat"].rolling(window=72).min().fillna(0)
        df["coldwave_flag"] = df["is_extreme_cold"].rolling(window=72).min().fillna(0)

        # Remove auxiliary columns
        df = df.drop(columns=["is_extreme_heat", "is_extreme_cold"])

    return df


def validate_and_handle_errors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates data integrity, handles minor inconsistencies, and raises critical errors.

    Args:
        df (pd.DataFrame): Input DataFrame with extracted features.

    Returns:
        pd.DataFrame: Validated and cleaned DataFrame.
    """
    logger.info("Validating feature integrity...")
    df = df.copy()

    # 1. Domain Validation: Check physical limits
    for col, (min_val, max_val) in PHYSICAL_LIMITS.items():
        if col in df.columns:
            outliers = (df[col] < min_val) | (df[col] > max_val)
            num_outliers = outliers.sum()

            if num_outliers > 0:
                perc_outliers = num_outliers / len(df)
                if perc_outliers > 0.05:
                    logger.error(
                        f"Critical Error: {num_outliers} domain inconsistencies in {col} ({perc_outliers:.2%})"
                    )
                    raise ValueError(f"Domain consistency error: too many outliers in {col}")
                else:
                    logger.warning(f"Minor inconsistency: {num_outliers} values in {col} outside limits. Imputing...")
                    df.loc[outliers, col] = np.nan
                    df[col] = df[col].ffill().bfill()

    # 2. Check for unexpected NaNs in generated features (post-initialization period)
    # We expect some NaNs in the first 168 rows due to lags and rolling windows
    check_df = df.iloc[168:]
    if check_df.isna().any().any():
        nan_cols = check_df.columns[check_df.isna().any()].tolist()
        logger.warning(f"Unexpected NaN values detected in columns: {nan_cols}")
        # Final imputation to ensure downstream compatibility
        df = df.ffill().bfill()

    return df


def handle_high_dimensionality(df: pd.DataFrame, target_col: str = "Load_MW") -> dict:
    """
    Handles high dimensionality using feature selection (Fisher Score proxy) and PCA.

    Args:
        df (pd.DataFrame): Full feature DataFrame.
        target_col (str): Target variable name.

    Returns:
        dict: Dictionary containing 'full', 'selected', and 'pca' versions of the dataset.
    """
    logger.info("Handling high dimensionality...")

    # Prepare feature matrix X and target y
    exclude_cols = ["datetime", target_col]
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    # Use zero-fill for selection/reduction to avoid errors
    X_raw = df[feature_cols].fillna(0)
    y = df[target_col].fillna(0) if target_col in df.columns else np.zeros(len(df))

    # 1. Feature Selection (Fisher Score proxy using f_regression)
    # Applied if dimensionality is high (e.g., > 50 features)
    num_features = len(feature_cols)
    df_selected = df.copy()
    if num_features > 50 and target_col in df.columns:
        k = min(50, num_features)
        selector = SelectKBest(score_func=f_regression, k=k)
        selector.fit(X_raw, y)

        selected_features = [feature_cols[i] for i in selector.get_support(indices=True)]
        logger.info(f"Top {k} features selected via Fisher Score proxy.")

        base_cols = [c for c in ["datetime", target_col] if c in df.columns]
        df_selected = df[base_cols + selected_features].copy()

    # 2. Dimensionality Reduction (PCA)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    pca = PCA(n_components=0.95)  # Retain 95% of variance
    X_pca = pca.fit_transform(X_scaled)

    logger.info(f"PCA reduced dimensions from {num_features} to {X_pca.shape[1]} components.")

    pca_cols = [f"PCA_{i}" for i in range(X_pca.shape[1])]
    base_cols = [c for c in ["datetime", target_col] if c in df.columns]

    df_pca = pd.concat([df[base_cols].reset_index(drop=True), pd.DataFrame(X_pca, columns=pca_cols)], axis=1)

    return {"full": df, "selected": df_selected, "pca": df_pca}


def save_datasets(datasets: dict, output_dir: Path):
    """
    Saves various versions of the engineered datasets.

    Args:
        datasets (dict): Dictionary of DataFrames.
        output_dir (Path): Target directory.
    """
    logger.info(f"Saving datasets to: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    for version, df in datasets.items():
        file_path = output_dir / f"features_{version}.csv"
        df.to_csv(file_path, index=False)
        logger.info(f"Saved '{version}' dataset: {len(df.columns)} features.")


def main():
    """
    Main execution pipeline for feature engineering.
    """
    start_time = time.time()
    logger.info("Starting Feature Engineering module execution...")

    try:
        # Resolve paths relative to this script
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        DATA_PROCESSED = BASE_DIR / "data" / "processed"
        INPUT_FILE = DATA_PROCESSED / "dados_treino_completos.csv"
        OUTPUT_DIR = DATA_PROCESSED / "feat-engineering"

        # 1. Load Data
        df = load_data(INPUT_FILE)

        # 2. Extract Features
        df = extract_temporal_features(df)

        climate_vars = ["skt", "t2m", "d2m", "stl1", "ssrd", "strd", "sp", "u10", "v10", "swvl1", "tp"]
        df = extract_rolling_features(df, climate_cols=climate_vars, window_size=24)
        df = extract_lagged_features(df, target_col="Load_MW")
        df = extract_derived_features(df)

        # 3. Validation & Error Handling
        df = validate_and_handle_errors(df)

        # 4. Dimensionality Handling & PCA
        datasets = handle_high_dimensionality(df, target_col="Load_MW")

        # 5. Versioning & Saving
        save_datasets(datasets, OUTPUT_DIR)

        duration = time.time() - start_time
        logger.info(f"Feature engineering completed in {duration:.2f} seconds.")
        logger.info(f"Total features in full dataset: {len(df.columns)}")

    except Exception as e:
        logger.error(f"Critical failure in feature engineering pipeline: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
