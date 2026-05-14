import numpy as np
import pandas as pd
import pytest
from data_pipeline.feature_engineering import FeatureEngineer

# =======================================
# MOCK DATA GENERATOR
# =======================================


def create_mock_df(n_rows=200, freq="h"):
    """
    Creates a mock dataframe with datetime, Load and climate variables.
    """
    dt_rng = pd.date_range("2023-01-01", periods=n_rows, freq=freq, tz="UTC")
    target_col = "Load_MW" if freq == "h" else "Load_MWh"
    data = {
        "datetime": dt_rng,
        target_col: np.random.uniform(20000, 40000, n_rows),
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
    """Unit tests for the FeatureEngineer class supporting both frequencies."""

    @pytest.fixture
    def fe_hourly(self, tmp_path):
        return FeatureEngineer(threshold=0.6, models_dir=tmp_path, frequency="hourly")

    @pytest.fixture
    def fe_daily(self, tmp_path):
        return FeatureEngineer(threshold=0.6, models_dir=tmp_path, frequency="daily")

    def test_extract_temporal_features_hourly(self, fe_hourly):
        df = create_mock_df(10, freq="h")
        df_out = fe_hourly.extract_temporal_features(df)
        assert "hour" in df_out.columns
        assert "day_of_week" in df_out.columns

    def test_extract_temporal_features_daily(self, fe_daily):
        df = create_mock_df(10, freq="D")
        df_out = fe_daily.extract_temporal_features(df)
        assert "hour" not in df_out.columns
        assert "day_of_week" in df_out.columns

    def test_extract_lagged_features_hourly(self, fe_hourly):
        df = create_mock_df(200, freq="h")
        df_out = fe_hourly.extract_lagged_features(df)
        assert "L1_Load" in df_out.columns
        assert "L24_Load" in df_out.columns
        assert "L168_Load" in df_out.columns
        assert "L7_Load" not in df_out.columns

    def test_extract_lagged_features_daily(self, fe_daily):
        df = create_mock_df(50, freq="D")
        df_out = fe_daily.extract_lagged_features(df)
        assert "L1_Load" in df_out.columns
        assert "L7_Load" in df_out.columns
        assert "L28_Load" in df_out.columns
        assert "L24_Load" not in df_out.columns

    def test_extract_rolling_features_daily(self, fe_daily):
        df = create_mock_df(100, freq="D")
        climate_cols = ["t2m"]
        df_out = fe_daily.extract_rolling_features(df, climate_cols)
        # Should have 7-day and 30-day rolling windows
        assert "t2m_rolling_7_mean" in df_out.columns
        assert "t2m_rolling_30_mean" in df_out.columns
        assert "t2m_rolling_24_mean" not in df_out.columns

    def test_extract_derived_features_daily(self, fe_daily):
        df = create_mock_df(50, freq="D")
        df = fe_daily.extract_temporal_features(df)
        df_out = fe_daily.extract_derived_features(df)
        assert "heatwave_flag" in df_out.columns
        # Heatwave flag on daily data uses window of 3
        # First 2 rows should be NaN before ffill/bfill
        # raw_hw = df_out["heatwave_flag"].iloc[:2]
        # In run_pipeline it is filled, but extract_derived_features alone might have NaNs
        # (Actually rolling(3).min() has 2 NaNs)

    def test_save_and_load_with_frequency(self, fe_hourly, tmp_path):
        df = create_mock_df(100, freq="h")
        fe_hourly.run_pipeline(df, fit=True)
        fe_hourly.save()
        assert (tmp_path / "scaler_hourly.joblib").exists()
        assert (tmp_path / "pca_hourly.joblib").exists()
        assert (tmp_path / "selected_features_hourly.joblib").exists()

    def test_run_pipeline_daily_integration(self, fe_daily):
        df = create_mock_df(100, freq="D")
        results = fe_daily.run_pipeline(df, fit=True)
        assert "Load_MWh" in results["full"].columns
        assert len(results["full"]) == 100
        # Check if some daily-specific column exists
        assert "L7_Load" in results["full"].columns

    def test_edge_daily_small_dataset(self, fe_daily):
        """Edge Case: Daily dataset smaller than L28."""
        df = create_mock_df(10, freq="D")
        results = fe_daily.run_pipeline(df, fit=True)
        assert len(results["full"]) == 10
        assert not results["full"]["L28_Load"].isna().any()
