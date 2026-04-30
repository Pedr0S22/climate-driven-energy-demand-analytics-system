import logging
import os
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
    "Load_MWh": (0, 24000000),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Modular Feature Engineering Pipeline for Energy Demand Analytics.
    Supports both Hourly and Daily data frequencies.

    Decisions & Rationale:
    1. Threshold (0.6): Chosen to be conservative. In climate data, variables are often
       highly collinear (e.g., skin vs air temp). 0.6 ensures we only keep distinct signals.
    2. Dynamic Frequency: Adjusts lags and rolling windows based on 'hourly' or 'daily' grain.
    3. Modularity: The class saves its state (fitted scalers/PCA) to allow the
       Live Data Scheduler to transform real-time data using the exact same parameters.
    """

    def __init__(self, threshold=0.6, models_dir=None, frequency="hourly"):
        self.threshold = threshold
        self.models_dir = Path(models_dir) if models_dir else None
        self.frequency = frequency.lower()
        self.scaler = StandardScaler()
        self.pca = None
        self.selected_features = None
        self.pca_features = None
        # Datetime is metadata; these are its categorical decompositions
        self.categorical_cols = ["hour", "day_of_week", "month", "season", "year"]
        if self.frequency == "daily":
            self.categorical_cols.remove("hour")
            self.target_col = "Load_MWh"
        else:
            self.target_col = "Load_MW"

    def extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Decomposes datetime into periodic components.
        """
        logger.info(f"Extracting temporal features ({self.frequency})...")
        df = df.copy()
        if "datetime" in df.columns:
            dt = pd.to_datetime(df["datetime"], utc=True)
            if self.frequency == "hourly":
                df["hour"] = dt.dt.hour
            df["day_of_week"] = dt.dt.dayofweek
            df["month"] = dt.dt.month
            df["year"] = dt.dt.year
            # (Month % 12 // 3) + 1 maps Dec-Feb to 1, Mar-May to 2, etc.
            df["season"] = df["month"].apply(lambda m: (m % 12 // 3) + 1)
        return df

    def extract_rolling_features(self, df: pd.DataFrame, climate_cols: list) -> pd.DataFrame:
        """
        Captures short-term climate inertia using rolling windows.

        Windows:
        - Hourly: 24h window (1 full cycle).
        - Daily: 7-day and 30-day windows (weekly and monthly cycles).
        """
        logger.info(f"Extracting rolling features for frequency: {self.frequency}...")
        df = df.copy()
        key_vars = ["t2m", "skt", "ssrd", "tp"]

        # Define windows based on frequency
        windows = [24] if self.frequency == "hourly" else [7, 30]

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")
            for col in climate_cols:
                if col not in df.columns:
                    continue

                for win in windows:
                    suffix = f"_rolling_{win}"
                    rolling = df[col].rolling(window=win)
                    df[f"{col}{suffix}_mean"] = rolling.mean()
                    df[f"{col}{suffix}_std"] = rolling.std()

                    # Key variables get deeper physics-based stats
                    if col in key_vars:
                        df[f"{col}{suffix}_median"] = rolling.median()
                        df[f"{col}{suffix}_var"] = rolling.var()
                        df[f"{col}{suffix}_rms"] = np.sqrt((df[col] ** 2).rolling(window=win).mean())
                        df[f"{col}{suffix}_deriv"] = df[col].diff().abs().rolling(window=win).mean()
                        df[f"{col}{suffix}_skew"] = rolling.skew()
                        df[f"{col}{suffix}_kurt"] = rolling.kurt()

                    if col == "t2m":
                        df[f"{col}{suffix}_iqr"] = rolling.apply(lambda x: iqr(x) if len(x) > 1 else 0, raw=True)
        return df

    def extract_lagged_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Captures auto-regressive demand behavior.

        Lags:
        - Hourly: L1 (momentum), L24 (yesterday), L168 (last week).
        - Daily: L1 (yesterday), L7 (last week), L28 (4 weeks ago).
        """
        logger.info(f"Extracting lagged features for frequency: {self.frequency}...")
        df = df.copy()
        if self.target_col in df.columns:
            if self.frequency == "hourly":
                lags = {"L1": 1, "L24": 24, "L168": 168}
            else:
                lags = {"L1": 1, "L7": 7, "L28": 28}

            for name, shift_val in lags.items():
                df[f"{name}_Load"] = df[self.target_col].shift(shift_val)
        return df

    def extract_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Physics-derived climate indicators.
        """
        logger.info(f"Extracting derived features (HDD/CDD) for {self.frequency}...")
        df = df.copy()
        if "t2m" in df.columns:
            t_base = 18.0  # Celsius
            df["HDD"] = df["t2m"].apply(lambda x: max(0, t_base - x))
            df["CDD"] = df["t2m"].apply(lambda x: max(0, x - t_base))

            if "month" in df.columns:
                df["temp_anomaly"] = df["t2m"] - df.groupby("month")["t2m"].transform("mean")

            # Persistent Extremes logic
            # Hourly: 72 hours. Daily: 3 days.
            persist_win = 72 if self.frequency == "hourly" else 3

            q_high, q_low = df["t2m"].quantile(0.9), df["t2m"].quantile(0.1)
            df["is_extreme_heat"] = (df["t2m"] > q_high).astype(int)
            df["is_extreme_cold"] = (df["t2m"] < q_low).astype(int)

            df["heatwave_flag"] = df["is_extreme_heat"].rolling(window=persist_win).min().fillna(0)
            df["coldwave_flag"] = df["is_extreme_cold"].rolling(window=persist_win).min().fillna(0)

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

        if y.nunique() < 2:
            return 0

        baseline = y.value_counts(normalize=True).max()
        try:
            model = LogisticRegression(solver="lbfgs", max_iter=200)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning)
                # Use cv=2 for very small datasets (common in new daily slices)
                cv_val = min(3, y.value_counts().min())
                if cv_val < 2:
                    return 0
                scores = cross_val_score(model, X, y, cv=cv_val)
            acc = scores.mean()
            strength = (acc - baseline) / (1 - baseline + 1e-6)
            return max(0, strength)
        except Exception:
            return 0

    def fit_selection(self, df: pd.DataFrame):
        logger.info(f"Fitting redundancy filter (Threshold: {self.threshold})...")
        cols = [c for c in df.columns if c not in ["datetime", self.target_col]]
        target = df[self.target_col].fillna(0)

        relevance = {}
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
        logger.info("Detecting PCA elbow...")
        X_scaled = self.scaler.fit_transform(X.fillna(0))
        full_pca = PCA().fit(X_scaled)
        evr = full_pca.explained_variance_ratio_

        n = len(evr)
        if n < 2:
            self.pca = PCA(n_components=n)
            self.pca.fit(X_scaled)
            return

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

    def save(self, suffix=""):
        if self.models_dir:
            self.models_dir.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.scaler, self.models_dir / f"scaler_{self.frequency}{suffix}.joblib")
            joblib.dump(self.pca, self.models_dir / f"pca_{self.frequency}{suffix}.joblib")
            joblib.dump(self.selected_features, self.models_dir / f"selected_features_{self.frequency}{suffix}.joblib")
            joblib.dump(self.pca_features, self.models_dir / f"pca_features_{self.frequency}{suffix}.joblib")
            logger.info(f"Transformers persisted to {self.models_dir} with suffix {self.frequency}")

    def load(self, suffix=""):
        """Loads fitted transformers and feature lists for real-time inference."""
        if self.models_dir:
            self.scaler = joblib.load(self.models_dir / f"scaler_{self.frequency}{suffix}.joblib")
            self.pca = joblib.load(self.models_dir / f"pca_{self.frequency}{suffix}.joblib")
            self.selected_features = joblib.load(self.models_dir / f"selected_features_{self.frequency}{suffix}.joblib")
            self.pca_features = joblib.load(self.models_dir / f"pca_features_{self.frequency}{suffix}.joblib")
            logger.info(f"Transformers loaded from {self.models_dir} for frequency {self.frequency}")

    def run_pipeline(self, df: pd.DataFrame, fit=True):
        df = self.extract_temporal_features(df)
        climate_vars = ["skt", "t2m", "d2m", "stl1", "ssrd", "strd", "sp", "u10", "v10", "swvl1", "tp"]
        df = self.extract_rolling_features(df, climate_cols=climate_vars)
        df = self.extract_lagged_features(df)
        df = self.extract_derived_features(df)

        df = df.ffill().bfill()

        if fit:
            self.fit_selection(df)

        features_full = df.copy()
        # All columns except metadata are the "full feature set" for PCA
        if self.pca_features is None:
            self.pca_features = [c for c in df.columns if c not in ["datetime", self.target_col]]

        meta_cols = ["datetime", self.target_col] if "datetime" in df.columns else []
        features_selected = df[meta_cols + self.selected_features].copy()

        if fit:
            self.fit_pca(df[self.pca_features])

        X_pca = self.pca.transform(self.scaler.transform(df[self.pca_features].fillna(0)))
        pca_df = pd.DataFrame(X_pca, columns=[f"PCA_{i}" for i in range(X_pca.shape[1])])
        base_cols = [c for c in ["datetime", self.target_col] if c in df.columns]
        features_pca = pd.concat([df[base_cols].reset_index(drop=True), pca_df], axis=1)

        return {"full": features_full.fillna(0), "selected": features_selected.fillna(0), "pca": features_pca.fillna(0)}


def run_realtime_engineering(freq: str):
    """
    Entry point for real-time feature engineering.
    Uses pre-fitted models to transform incoming live data context.
    """
    APP_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_PROCESSED = APP_ROOT / "data" / "processed"
    MODELS_FEAT = APP_ROOT / "models" / "feat-engineering"
    OUTPUT_DIR = DATA_PROCESSED / "feat-engineering"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_path = DATA_PROCESSED / f"realtime_{freq}.csv"
    if not input_path.exists():
        logger.error(f"Real-time input file {input_path} not found.")
        return

    df = pd.read_csv(input_path)
    fe = FeatureEngineer(models_dir=MODELS_FEAT, frequency=freq)
    fe.load()

    datasets = fe.run_pipeline(df, fit=False)

    # Persistence: Store the engineered PCA set for inference
    out_name = f"realtime_{freq}_engineered.csv"
    output_file = OUTPUT_DIR / out_name

    # Robust Save: Save to .tmp and rename only on success
    tmp_path = f"{output_file}.tmp"
    datasets["pca"].to_csv(tmp_path, index=False)
    os.replace(tmp_path, output_file)

    logger.info(f"Successfully persisted real-time engineered {freq} data to {output_file}")


def main():
    start_time = time.time()
    APP_ROOT = Path(__file__).resolve().parent.parent.parent
    DATA_PROCESSED = APP_ROOT / "data" / "processed"
    MODELS_FEAT = APP_ROOT / "models" / "feat-engineering"
    OUTPUT_DIR = DATA_PROCESSED / "feat-engineering"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process both frequencies
    for freq in ["hourly", "daily"]:
        filename = f"complete_train_data_{freq}.csv"
        input_path = DATA_PROCESSED / filename
        if not input_path.exists():
            logger.warning(f"Input file {input_path} not found. Skipping {freq} pipeline.")
            continue

        logger.info(f"Starting {freq} Feature Engineering Pipeline...")
        df = pd.read_csv(input_path)

        fe = FeatureEngineer(threshold=0.6, models_dir=MODELS_FEAT, frequency=freq)
        datasets = fe.run_pipeline(df, fit=True)
        fe.save()

        for name, df_set in datasets.items():
            out_name = f"features_{freq}_{name}.csv"
            output_file = OUTPUT_DIR / out_name

            # Robust Save: Save to .tmp and rename only on success
            tmp_path = f"{output_file}.tmp"
            df_set.to_csv(tmp_path, index=False)
            os.replace(tmp_path, output_file)

            logger.info(f"Exported '{freq}/{name}' dataset.")

    duration = time.time() - start_time
    logger.info(f"Feature Engineering Pipeline execution finished in {duration:.2f} seconds.")


if __name__ == "__main__":
    main()
