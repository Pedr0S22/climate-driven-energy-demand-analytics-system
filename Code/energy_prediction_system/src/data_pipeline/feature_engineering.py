import logging
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import iqr, spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler

# =======================================
# CONFIGURATION AND CONSTANTS
# =======================================

# Physical limits for data validation during engineering
# t2m and skt are in Celsius (converted from Kelvin in the cleaning module)
PHYSICAL_LIMITS = {
    "t2m": (-50.0, 60.0),
    "skt": (-50.0, 70.0),
    "Load_MW": (0, 1000000),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Modular Feature Engineering Pipeline for Energy Demand Analytics.

    Decisions & Rationale:
    1. Threshold (0.6): Chosen to be conservative. In climate data, variables are often
       highly collinear (e.g., skin vs air temp). 0.6 ensures we only keep distinct signals.
    2. Spearman Correlation: Used for continuous variables as it captures non-linear
       monotonic relationships and is less sensitive to non-normal distributions.
    3. Modularity: The class saves its state (fitted scalers/PCA) to allow the
       Live Data Scheduler to transform real-time data using the exact same parameters.
    """

    def __init__(self, threshold=0.6, models_dir=None):
        self.threshold = threshold
        self.models_dir = Path(models_dir) if models_dir else None
        self.scaler = StandardScaler()
        self.pca = None
        self.selected_features = None
        # Datetime is metadata; these are its categorical decompositions
        self.categorical_cols = ["hour", "day_of_week", "month", "season", "year"]
        self.target_col = "Load_MW"

    def extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Decomposes datetime into periodic components.

        Extraction Logic:
        - Hour/Day/Month: Capture daily, weekly, and annual seasonality.
        - Year: Captures long-term demand growth/trends.
        - Season: Categorical grouping (1:Winter, 2:Spring, 3:Summer, 4:Autumn).
        - Decision: 'datetime' is excluded from feature sets as it is a non-stationary metadata key.
        """
        logger.info("Extracting temporal features...")
        df = df.copy()
        if "datetime" in df.columns:
            dt = pd.to_datetime(df["datetime"], utc=True)
            df["hour"] = dt.dt.hour
            df["day_of_week"] = dt.dt.dayofweek
            df["month"] = dt.dt.month
            df["year"] = dt.dt.year
            # (Month % 12 // 3) + 1 maps Dec-Feb to 1, Mar-May to 2, etc.
            df["season"] = df["month"].apply(lambda m: (m % 12 // 3) + 1)
        return df

    def extract_rolling_features(self, df: pd.DataFrame, climate_cols: list, window_size: int = 24) -> pd.DataFrame:
        """
        Captures short-term climate inertia using rolling windows.

        Extraction Logic:
        - Mean/Std: Basic central tendency and volatility.
        - RMS/Deriv: Captures the 'energy' of the signal and rate of change (e.g., rapid cooling).
        - IQR: Robust measure of spread, specifically for t2m to detect thermal instability.
        - Window (24h): Chosen to represent the full daily cycle.
        """
        logger.info(f"Extracting rolling features (window={window_size})...")
        df = df.copy()
        key_vars = ["t2m", "skt", "ssrd", "tp"]

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")
            for col in climate_cols:
                if col not in df.columns:
                    continue

                rolling = df[col].rolling(window=window_size)
                df[f"{col}_rolling_mean"] = rolling.mean()
                df[f"{col}_rolling_std"] = rolling.std()

                # Key variables get deeper physics-based stats
                if col in key_vars:
                    df[f"{col}_rolling_median"] = rolling.median()
                    df[f"{col}_rolling_var"] = rolling.var()
                    df[f"{col}_rolling_rms"] = np.sqrt((df[col] ** 2).rolling(window=window_size).mean())
                    df[f"{col}_rolling_deriv"] = df[col].diff().abs().rolling(window=window_size).mean()
                    df[f"{col}_rolling_skew"] = rolling.skew()
                    df[f"{col}_rolling_kurt"] = rolling.kurt()

                if col == "t2m":
                    df[f"{col}_rolling_iqr"] = rolling.apply(lambda x: iqr(x) if len(x) > 1 else 0, raw=True)
        return df

    def extract_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Captures auto-regressive demand behavior.

        Lags:
        - L1: Immediate momentum (last hour).
        - L24: Daily seasonality (same hour yesterday).
        - L168: Weekly seasonality (same hour last week).
        """
        logger.info("Extracting lagged features (L1, L24, L168)...")
        df = df.copy()
        if self.target_col in df.columns:
            df["L1_Load"] = df[self.target_col].shift(1)
            df["L24_Load"] = df[self.target_col].shift(24)
            df["L168_Load"] = df[self.target_col].shift(168)
        return df

    def extract_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Physics-derived climate indicators.

        Decisions:
        - HDD/CDD Base (18°C): Standard threshold for when heating/cooling is triggered.
        - Units: Standardized to Celsius to match the cleaning module output.
        - Anomalies: Captures deviation from the 'normal' month, highlighting extreme days.
        - Heatwave (72h): Captures persistence of extreme heat, which has cumulative effects on demand.
        """
        logger.info("Extracting derived features (HDD/CDD in Celsius)...")
        df = df.copy()
        if "t2m" in df.columns:
            t_base = 18.0  # Celsius
            df["HDD"] = df["t2m"].apply(lambda x: max(0, t_base - x))
            df["CDD"] = df["t2m"].apply(lambda x: max(0, x - t_base))

            if "month" in df.columns:
                # Grouped by month to capture relative thermal stress
                df["temp_anomaly"] = df["t2m"] - df.groupby("month")["t2m"].transform("mean")

            # Persistent Extremes logic
            q_high, q_low = df["t2m"].quantile(0.9), df["t2m"].quantile(0.1)
            df["is_extreme_heat"] = (df["t2m"] > q_high).astype(int)
            df["is_extreme_cold"] = (df["t2m"] < q_low).astype(int)

            # Flag is 1 only if extremum persists for 72 consecutive hours
            df["heatwave_flag"] = df["is_extreme_heat"].rolling(window=72).min().fillna(0)
            df["coldwave_flag"] = df["is_extreme_cold"].rolling(window=72).min().fillna(0)

            df = df.drop(columns=["is_extreme_heat", "is_extreme_cold"])
        return df

    def _calculate_lambda(self, x, y):
        """Goodman and Kruskal's lambda for categorical association."""
        confusion_matrix = pd.crosstab(x, y)
        sum_max_row = confusion_matrix.max(axis=1).sum()
        max_sum_row = confusion_matrix.sum(axis=1).max()
        n = confusion_matrix.sum().sum()
        if n == max_sum_row:
            return 0
        return (sum_max_row - max_sum_row) / (n - max_sum_row)

    def _cat_cont_association(self, cat_ser, cont_ser):
        """Association strength using LogReg accuracy (Cat from Cont)."""
        df_tmp = pd.DataFrame({"cat": cat_ser, "cont": cont_ser}).dropna()
        if len(df_tmp) < 10:
            return 0
        X = df_tmp[["cont"]]
        y = df_tmp["cat"]

        # If only one category exists, association is zero
        if y.nunique() < 2:
            return 0

        baseline = y.value_counts(normalize=True).max()
        try:
            # Increase iterations to solve ConvergenceWarning
            model = LogisticRegression(solver="lbfgs", max_iter=200)
            # Suppress surgical warnings during CV on small groups
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                scores = cross_val_score(model, X, y, cv=3)
            acc = scores.mean()
            strength = (acc - baseline) / (1 - baseline + 1e-6)
            return max(0, strength)
        except Exception:
            return 0

    def fit_selection(self, df: pd.DataFrame):
        """
        Fits selection logic using a 0.6 threshold.

        Decision Rule: If two features are correlated > 0.6, drop the one
        with lower Spearman correlation to the target (Load_MW).
        """
        logger.info(f"Fitting redundancy filter (Threshold: {self.threshold})...")
        cols = [c for c in df.columns if c not in ["datetime", self.target_col]]
        target = df[self.target_col].fillna(0)

        # Calculate 'Relevance' to target as the tie-breaker
        relevance = {}
        # Ignore constant array warnings during statistical scan
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="An input array is constant")
            for col in cols:
                if col in self.categorical_cols:
                    relevance[col] = df.groupby(col)[self.target_col].mean().std()
                else:
                    relevance[col] = abs(spearmanr(df[col].fillna(0), target)[0])

        to_drop = set()
        sorted_cols = sorted(cols, key=lambda x: relevance.get(x, 0), reverse=True)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="An input array is constant")
            for i, col_a in enumerate(sorted_cols):
                if col_a in to_drop:
                    continue
                for col_b in sorted_cols[i + 1 :]:
                    if col_b in to_drop:
                        continue

                    if col_a in self.categorical_cols and col_b in self.categorical_cols:
                        score = self._calculate_lambda(df[col_a], df[col_b])
                        metric = "Lambda"
                    elif col_a not in self.categorical_cols and col_b not in self.categorical_cols:
                        score = abs(spearmanr(df[col_a].fillna(0), df[col_b].fillna(0))[0])
                        metric = "Spearman"
                    else:
                        cat = col_a if col_a in self.categorical_cols else col_b
                        cont = col_b if col_a in self.categorical_cols else col_a
                        score = self._cat_cont_association(df[cat], df[cont])
                        metric = "LogReg/Assoc"

                    if score > self.threshold:
                        logger.info(f"Dropped '{col_b}' (score={score:.2f} {metric} with '{col_a}')")
                        to_drop.add(col_b)

        self.selected_features = [c for c in cols if c not in to_drop]
        logger.info(f"Final Selection: {len(self.selected_features)} relevant features.")

    def fit_pca(self, X):
        """Automated PCA elbow detection using the Knee Point method."""
        logger.info("Detecting PCA elbow...")
        X_scaled = self.scaler.fit_transform(X.fillna(0))
        full_pca = PCA().fit(X_scaled)
        evr = full_pca.explained_variance_ratio_

        # Calculate Knee: Point of maximum distance to the line between start and end
        n = len(evr)
        coords = np.vstack((np.arange(n), evr)).T
        line_vec = coords[-1] - coords[0]
        line_vec_norm = line_vec / np.sqrt(np.sum(line_vec**2))
        vec_from_start = coords - coords[0]
        scalar_prod = np.sum(vec_from_start * line_vec_norm, axis=1)
        vec_to_line = vec_from_start - np.outer(scalar_prod, line_vec_norm)
        elbow_idx = np.argmax(np.sqrt(np.sum(vec_to_line**2, axis=1)))

        n_comp = elbow_idx + 1
        logger.info(f"Elbow rule selected {n_comp} components.")
        self.pca = PCA(n_components=n_comp)
        self.pca.fit(X_scaled)

    def save(self):
        """Saves state for real-time reuse by Live Data Scheduler."""
        if self.models_dir:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.scaler, self.models_dir / "scaler.joblib")
            joblib.dump(self.pca, self.models_dir / "pca.joblib")
            joblib.dump(self.selected_features, self.models_dir / "selected_features.joblib")
            logger.info(f"Transformers persisted to {self.models_dir}")

    def run_pipeline(self, df: pd.DataFrame, fit=True):
        """Runs the extraction and transformation sequence."""
        df = self.extract_temporal_features(df)
        climate_vars = ["skt", "t2m", "d2m", "stl1", "ssrd", "strd", "sp", "u10", "v10", "swvl1", "tp"]
        df = self.extract_rolling_features(df, climate_cols=climate_vars)
        df = self.extract_lagged_features(df)
        df = self.extract_derived_features(df)

        # Imputation to ensure downstream stability
        df = df.ffill().bfill()

        if fit:
            self.fit_selection(df)

        features_full = df.copy()

        # 'Selected' dataset reconstruction
        meta_cols = ["datetime", self.target_col] if "datetime" in df.columns else []
        features_selected = df[meta_cols + self.selected_features].copy()

        if fit:
            self.fit_pca(df[self.selected_features])

        # 'PCA' dataset reconstruction
        X_pca = self.pca.transform(self.scaler.transform(df[self.selected_features].fillna(0)))
        pca_df = pd.DataFrame(X_pca, columns=[f"PCA_{i}" for i in range(X_pca.shape[1])])
        base_cols = [c for c in ["datetime", self.target_col] if c in df.columns]
        features_pca = pd.concat([df[base_cols].reset_index(drop=True), pca_df], axis=1)

        # Final safety fill to catch columns that were entirely NaN
        features_full = features_full.fillna(0)
        features_selected = features_selected.fillna(0)
        features_pca = features_pca.fillna(0)

        return {"full": features_full, "selected": features_selected, "pca": features_pca}


def main():
    start_time = time.time()
    APP_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_PROCESSED = APP_ROOT / "data" / "processed"
    MODELS_FEAT = APP_ROOT / "models" / "feat-engineering"
    INPUT_FILE = DATA_PROCESSED / "dados_treino_completos.csv"
    OUTPUT_DIR = DATA_PROCESSED / "feat-engineering"

    logger.info("Initializing Feature Engineering Pipeline...")
    df = pd.read_csv(INPUT_FILE)

    fe = FeatureEngineer(threshold=0.6, models_dir=MODELS_FEAT)
    datasets = fe.run_pipeline(df, fit=True)
    fe.save()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, df_set in datasets.items():
        df_set.to_csv(OUTPUT_DIR / f"features_{name}.csv", index=False)
        logger.info(f"Exported '{name}' dataset: {len(df_set.columns)} columns.")

    duration = time.time() - start_time
    logger.info(f"Feature Engineering Pipeline execution finished in {duration:.2f} seconds.")


if __name__ == "__main__":
    main()
