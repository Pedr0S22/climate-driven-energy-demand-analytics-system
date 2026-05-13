from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

# Ensure it's imported exactly as pytest sees it
from src.data_pipeline.real_time_pipeline import run_pipeline


class TestRealtimePipelineIntegration:
    """Integration tests for the real-time data pipeline."""

    @pytest.fixture
    def mock_dirs(self, tmp_path):
        """Setup temporary directory structure for simulation."""
        base = tmp_path / "app"
        raw_energy = base / "data" / "raw" / "energy"
        raw_weather = base / "data" / "raw" / "weather"
        processed = base / "data" / "processed"
        feat_eng_realtime = processed / "feat-engineering" / "real-time"

        for d in [raw_energy, raw_weather, processed, feat_eng_realtime]:
            d.mkdir(parents=True, exist_ok=True)

        return {
            "root": base,
            "raw_energy": raw_energy,
            "raw_weather": raw_weather,
            "processed": processed,
            "feat_eng_realtime": feat_eng_realtime,
        }

    def test_full_realtime_cycle(self, mock_dirs, monkeypatch):
        """Run a full real-time cycle bypassing hardcoded path calculations."""

        # 1. Setup Mock Files
        # Using 'h' instead of 'H' to fix the pandas deprecation warning
        now = pd.Timestamp.now(tz="UTC").floor("h")
        times = pd.date_range(end=now, periods=48, freq="h", tz="UTC")

        energy_df = pd.DataFrame({"datetime": times, "Load_MW": np.random.uniform(20000, 30000, 48)})
        energy_df.to_csv(mock_dirs["raw_energy"] / "realtime_energy.csv", index=False)

        weather_df = pd.DataFrame(
            {
                "datetime": times,
                "temperature_2m": np.random.uniform(10, 30, 48),
                "dew_point_2m": 10.0,
                "surface_pressure": 1013.0,
                "precipitation": 0.0,
                "shortwave_radiation": 100.0,
                "terrestrial_radiation": 300.0,
                "skin_temperature": 15.0,
                "soil_temperature_0_to_7cm": 14.0,
                "soil_moisture_0_to_7cm": 0.2,
                "wind_speed_10m": 2.0,
                "wind_direction_10m": 180,
            }
        )
        weather_df.to_csv(mock_dirs["raw_weather"] / "realtime_weather.csv", index=False)

        # 2. THE TRICK: Spoof __file__ with the CORRECT 'src.' namespace
        fake_file_path = str(mock_dirs["root"] / "fake_dir_1" / "fake_dir_2" / "fake_pipeline.py")

        monkeypatch.setattr("src.data_pipeline.real_time_pipeline.__file__", fake_file_path)

        try:
            monkeypatch.setattr("src.data_pipeline.feature_engineering.__file__", fake_file_path)
            monkeypatch.setattr("src.data_pipeline.cleaning.__file__", fake_file_path)
        except AttributeError:
            pass

        # 3. Mute APIs and Models using the correct 'src.' namespace
        # We mock realtime_data_retrieval directly since that's what run_pipeline calls
        monkeypatch.setattr("src.data_pipeline.real_time_pipeline.realtime_data_retrieval", lambda **kwargs: None)

        # Optional: mute load_dotenv so it doesn't complain about missing env files in the mock dir
        monkeypatch.setattr("src.data_pipeline.real_time_pipeline.load_dotenv", lambda *args, **kwargs: None)

        def mock_fe_load(self_instance, *args, **kwargs):
            # 1. Tell the pipeline to keep the generated "L1_Load" feature
            # so it doesn't get filtered out before saving the CSV.
            self_instance.selected_features = ["L1_Load"]
            self_instance.pca_features = ["temperature_2m"]

            # 2. Mock the Scaler
            self_instance.scaler = MagicMock()
            self_instance.scaler.transform.side_effect = lambda x: x.values

            # 3. Mock the PCA model
            self_instance.pca = MagicMock()
            self_instance.pca.transform.side_effect = lambda x: np.zeros((x.shape[0], 5))
            self_instance.pca.n_components_ = 5

            # 4. Mock KMeans clusterer
            self_instance.kmeans = MagicMock()
            self_instance.kmeans.predict.side_effect = lambda x: np.zeros(x.shape[0])

        monkeypatch.setattr("src.data_pipeline.feature_engineering.FeatureEngineer.load", mock_fe_load)
        monkeypatch.setattr("src.data_pipeline.feature_engineering.FeatureEngineer.save", lambda *args: None)

        # 4. Execute Pipeline
        run_pipeline()

        # 5. Verify Persistence
        hourly_full = mock_dirs["feat_eng_realtime"] / "realtime_hourly_full.csv"
        daily_full = mock_dirs["feat_eng_realtime"] / "realtime_daily_full.csv"

        assert hourly_full.exists(), f"Hourly file not found at {hourly_full}"
        assert daily_full.exists(), f"Daily file not found at {daily_full}"

        df_hourly = pd.read_csv(hourly_full)
        assert "Load_MW" in df_hourly.columns
        assert not df_hourly.empty
