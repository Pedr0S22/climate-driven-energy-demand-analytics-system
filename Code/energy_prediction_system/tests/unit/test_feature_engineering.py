import joblib
import numpy as np
import pandas as pd
import pytest
from data_pipeline.feature_engineering import FeatureEngineer

# =======================================
# MOCK DATA GENERATOR
# =======================================


def create_mock_df(n_rows=200):
    """
    Creates a mock dataframe with datetime, Load_MW and climate variables.

    Args:
        n_rows (int): Number of rows to generate.

    Returns:
        pd.DataFrame: A mock dataset for testing.
    """
    dt_rng = pd.date_range("2023-01-01", periods=n_rows, freq="h", tz="UTC")
    data = {
        "datetime": dt_rng,
        "Load_MW": np.random.uniform(20000, 40000, n_rows),
        "t2m": np.random.uniform(0, 35, n_rows),
        "skt": np.random.uniform(0, 40, n_rows),
        "ssrd": np.random.uniform(0, 1000, n_rows),
        "tp": np.random.uniform(0, 10, n_rows),
        "d2m": np.random.uniform(-5, 20, n_rows),
        "stl1": np.random.uniform(5, 25, n_rows),
        "strd": np.random.uniform(200, 500, n_rows),
        "sp": np.random.uniform(950, 1050, n_rows),
        "u10": np.random.uniform(-5, 5, n_rows),
        "v10": np.random.uniform(-5, 5, n_rows),
        "swvl1": np.random.uniform(0.1, 0.4, n_rows),
    }
    return pd.DataFrame(data)


# =======================================
# UNIT TESTS
# =======================================


class TestFeatureEngineer:
    """Unit tests for the FeatureEngineer class."""

    @pytest.fixture
    def fe(self, tmp_path):
        """Fixture to initialize FeatureEngineer with a temporary model directory."""
        return FeatureEngineer(threshold=0.6, models_dir=tmp_path)

    def test_extract_temporal_features(self, fe):
        """
        Input: DataFrame with 'datetime' column.
        Output: DataFrame with hour, day_of_week, month, year, season columns.
        Logic: Verifies decomposition of UTC datetime into cyclical/periodic components.
        """
        df = create_mock_df(10)
        df_out = fe.extract_temporal_features(df)

        expected_cols = ["hour", "day_of_week", "month", "year", "season"]
        for col in expected_cols:
            assert col in df_out.columns

        # Verify season mapping (Jan=1, Apr=2, Jul=3, Oct=4)
        assert df_out.loc[0, "season"] == 1  # Jan
        assert df_out.loc[0, "year"] == 2023

    @pytest.mark.parametrize("window", [12, 24])
    def test_extract_rolling_features(self, fe, window):
        """
        Input: DataFrame with climate columns and a window size.
        Output: DataFrame with rolling mean, std, rms, etc.
        Logic: Verifies that rolling statistics are computed and columns are named correctly.
        """
        df = create_mock_df(50)
        climate_cols = ["t2m", "ssrd"]
        df_out = fe.extract_rolling_features(df, climate_cols, window_size=window)

        assert "t2m_rolling_mean" in df_out.columns
        assert "t2m_rolling_rms" in df_out.columns
        assert "t2m_rolling_iqr" in df_out.columns
        assert len(df_out) == 50

        # First window-1 rows should have NaNs (before imputation in pipeline)
        assert df_out["t2m_rolling_mean"].iloc[0 : window - 1].isna().all()

    def test_extract_lagged_features(self, fe):
        """
        Input: DataFrame with 'Load_MW'.
        Output: DataFrame with L1, L24, L168 lags.
        Logic: Verifies auto-regressive feature creation.
        """
        df = create_mock_df(200)
        df_out = fe.extract_lagged_features(df)

        assert "L1_Load" in df_out.columns
        assert "L24_Load" in df_out.columns
        assert "L168_Load" in df_out.columns

        # Verify L1 shift
        assert df_out["L1_Load"].iloc[1] == df["Load_MW"].iloc[0]

    def test_extract_derived_features(self, fe):
        """
        Input: DataFrame with 't2m' and 'month'.
        Output: DataFrame with HDD, CDD, temp_anomaly, and wave flags.
        Logic: Verifies physics-based demand indicators.
        """
        df = create_mock_df(100)
        df = fe.extract_temporal_features(df)
        df_out = fe.extract_derived_features(df)

        assert "HDD" in df_out.columns
        assert "CDD" in df_out.columns
        assert "temp_anomaly" in df_out.columns
        assert "heatwave_flag" in df_out.columns

        # HDD check (Base 18): if t2m=10, HDD=8, CDD=0
        df_test = pd.DataFrame({"t2m": [10.0, 25.0], "month": [1, 7]})
        df_test_out = fe.extract_derived_features(df_test)
        assert df_test_out.loc[0, "HDD"] == 8.0
        assert df_test_out.loc[0, "CDD"] == 0.0
        assert df_test_out.loc[1, "HDD"] == 0.0
        assert df_test_out.loc[1, "CDD"] == 7.0

    def test_fit_selection_collinearity(self, fe):
        """
        Input: DataFrame with highly correlated features.
        Output: selected_features list with one of the redundant features removed.
        Logic: Verifies the 0.6 Spearman threshold filter.
        """
        df = create_mock_df(100)
        # Create perfect collinearity
        df["t2m_copy"] = df["t2m"] * 1.05
        df["hour"] = np.random.randint(0, 24, 100)
        df["day_of_week"] = np.random.randint(0, 7, 100)
        df["month"] = np.random.randint(1, 13, 100)
        df["year"] = 2023
        df["season"] = 1

        fe.fit_selection(df)

        assert "t2m" in fe.selected_features or "t2m_copy" in fe.selected_features
        # They shouldn't both be there if threshold is 0.6 and correlation is ~1.0
        assert not ("t2m" in fe.selected_features and "t2m_copy" in fe.selected_features)

    def test_fit_pca_elbow(self, fe):
        """
        Input: High-dimensional feature matrix.
        Output: Fitted PCA object with reduced components.
        Logic: Verifies Knee Point detection logic.
        """
        n_rows, n_cols = 100, 20
        data = np.random.randn(n_rows, n_cols)
        # Inject some structure so PCA can find an elbow
        data[:, :5] = data[:, :5] * 10
        df = pd.DataFrame(data, columns=[f"feat_{i}" for i in range(n_cols)])

        fe.fit_pca(df)
        assert fe.pca is not None
        assert fe.pca.n_components_ < n_cols
        assert fe.pca.n_components_ > 0

    def test_run_pipeline_shapes(self, fe):
        """
        Input: Full raw dataset.
        Output: Dictionary with 'full', 'selected', and 'pca' datasets.
        Logic: Verifies row count consistency and gap filling.
        """
        n_rows = 200
        df = create_mock_df(n_rows)

        results = fe.run_pipeline(df, fit=True)

        for name in ["full", "selected", "pca"]:
            assert len(results[name]) == n_rows
            assert not results[name].isna().any().any()  # Should be filled by ffill/bfill

    def test_save_and_load(self, fe, tmp_path):
        """
        Input: Fitted FeatureEngineer state.
        Output: Persisted joblib files.
        Logic: Verifies modularity for real-time reuse.
        """
        df = create_mock_df(100)
        fe.run_pipeline(df, fit=True)
        fe.save()

        assert (tmp_path / "scaler.joblib").exists()
        assert (tmp_path / "pca.joblib").exists()
        assert (tmp_path / "selected_features.joblib").exists()

        # Load check
        scaler = joblib.load(tmp_path / "scaler.joblib")
        assert scaler.mean_.shape[0] == len(fe.selected_features)

    # =======================================
    # EDGE CASES
    # =======================================

    def test_edge_small_dataset(self, fe):
        """
        Edge Case: Dataset smaller than the largest lag (168h).
        Expected: Pipeline runs without error, bfill handles everything.
        """
        df = create_mock_df(10)  # < 168
        results = fe.run_pipeline(df, fit=True)
        assert len(results["full"]) == 10
        assert not results["full"]["L168_Load"].isna().any()

    def test_edge_constant_values(self, fe):
        """
        Edge Case: Climate variables are constant (zero variance).
        Expected: PCA and association metrics handle it without division by zero.
        """
        df = create_mock_df(50)
        df["t2m"] = 25.0  # Constant
        results = fe.run_pipeline(df, fit=True)
        assert "t2m" in results["full"].columns

    def test_edge_all_nan_column(self, fe):
        """
        Edge Case: A column is entirely NaN.
        Expected: Pipeline doesn't crash, ffill/bfill might leave it NaN if all are NaN,
        but verify stability.
        """
        df = create_mock_df(50)
        df["tp"] = np.nan
        # run_pipeline uses ffill().bfill(), if all are NaN, it stays NaN.
        # fit_pca and fit_selection fillna(0).
        results = fe.run_pipeline(df, fit=True)
        assert len(results["full"]) == 50

    def test_edge_extreme_values(self, fe):
        """
        Edge Case: Values far outside physical limits.
        Expected: Pipeline processes them (since FE doesn't clip, Cleaning does).
        """
        df = create_mock_df(50)
        df.loc[0, "t2m"] = 500.0  # Physical limit is 60
        results = fe.run_pipeline(df, fit=True)
        assert results["full"].loc[0, "t2m"] == 500.0
