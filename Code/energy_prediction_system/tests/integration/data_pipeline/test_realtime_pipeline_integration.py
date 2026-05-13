from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from data_pipeline.real_time_pipeline import run_pipeline


class TestRealtimePipelineIntegration:
    """Integration tests for the real-time data pipeline."""

    @pytest.fixture
    def mock_dirs(self, tmp_path):
        """Setup temporary directory structure for simulation."""
        base = tmp_path / "app"
        raw_energy = base / "data" / "raw" / "energy"
        raw_weather = base / "data" / "raw" / "weather"
        processed = base / "data" / "processed"
        # The code creates OUTPUT_DIR = DATA_PROCESSED / "feat-engineering" / "real-time"
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

    @patch("data_pipeline.ingestion.fetch_realtime_energy_load")
    @patch("data_pipeline.ingestion.fetch_realtime_weather")
    @patch("data_pipeline.real_time_pipeline.load_dotenv")
    # We mock load/save to avoid needing actual model files on disk
    @patch("data_pipeline.feature_engineering.FeatureEngineer.load", return_value=None)
    @patch("data_pipeline.feature_engineering.FeatureEngineer.save", return_value=None)
    def test_full_realtime_cycle(
        self, mock_fe_save, mock_fe_load, mock_load_dotenv, mock_fetch_weather, mock_fetch_energy, mock_dirs
    ):
        """Run a full real-time cycle (Mock Ingestion -> Cleaning -> Engineering)."""

        # 1. Setup Mock Files
        times = pd.date_range("2026-05-13", periods=48, freq="h", tz="UTC")
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

        # Patching only the ROOT variables, avoiding global Path patch
        with (
            patch("data_pipeline.real_time_pipeline.Path") as mock_path_rt,
            patch("data_pipeline.cleaning.ROOT", mock_dirs["root"]),
            patch("data_pipeline.feature_engineering.Path") as mock_path_fe,
        ):
            # RT Pipeline mock for project_root calculation
            rt_inst = MagicMock()
            rt_inst.parent.parent.parent = mock_dirs["root"]
            rt_inst.parent.__truediv__.return_value = mock_dirs["root"] / ".env"
            # We must make sure RT pipeline uses the real Path for energy_dir/weather_dir
            # but mock_path_rt.return_value is used for Path(__file__)
            mock_path_rt.return_value = rt_inst
            # Fallback to real Path for other calls
            mock_path_rt.side_effect = lambda *args: Path(*args)

            # FE mock for APP_ROOT calculation
            fe_inst = MagicMock()
            fe_inst.resolve.return_value.parent.parent.parent = mock_dirs["root"]
            mock_path_fe.return_value = fe_inst
            mock_path_fe.side_effect = lambda *args: Path(*args)

            run_pipeline()

        # 2. Verify Persistence
        hourly_full = mock_dirs["feat_eng_realtime"] / "realtime_hourly_full.csv"
        daily_full = mock_dirs["feat_eng_realtime"] / "realtime_daily_full.csv"

        assert hourly_full.exists(), f"Hourly file not found at {hourly_full}"
        assert daily_full.exists(), f"Daily file not found at {daily_full}"

        df_hourly = pd.read_csv(hourly_full)
        assert "L1_Load" in df_hourly.columns
        assert len(df_hourly) > 0
