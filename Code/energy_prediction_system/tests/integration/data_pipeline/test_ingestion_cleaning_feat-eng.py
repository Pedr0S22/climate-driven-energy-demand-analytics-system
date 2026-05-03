from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from data_pipeline.cleaning import DataCleaner, cleaning
from data_pipeline.feature_engineering import FeatureEngineer


class TestPipelineIntegration:
    """Integration tests for the modular Ingestion -> Cleaning -> Feature Engineering pipeline."""

    @pytest.fixture
    def pipeline_dirs(self, tmp_path):
        base = tmp_path / "project"
        raw_energy = base / "data" / "raw" / "energy"
        raw_weather = base / "data" / "raw" / "weather"
        processed = base / "data" / "processed"
        models = base / "models" / "feat-engineering"

        for d in [raw_energy, raw_weather, processed, models]:
            d.mkdir(parents=True, exist_ok=True)

        return {
            "raw_energy": raw_energy,
            "raw_weather": raw_weather,
            "processed": processed,
            "models": models,
        }

    def test_full_pipeline_modular_flow(self, pipeline_dirs):
        """
        Tests the end-to-end flow from raw CSVs to Hourly/Daily engineered features.
        """
        # 1. Create Mock Data
        times = pd.date_range("2023-01-01", periods=48, freq="h", tz="UTC")

        # Mock Energy
        df_e = pd.DataFrame({"Unnamed: 0": times, "Load_MW": np.random.uniform(20000, 30000, 48)})
        df_e.to_csv(pipeline_dirs["raw_energy"] / "energy_test.csv", index=False)

        # Mock Weather (Simplified for integration check)
        df_w = pd.DataFrame(
            {
                "valid_time": times,
                "t2m": np.random.uniform(280, 290, 48),
                "skt": np.random.uniform(280, 290, 48),
                "ssrd": [1000] * 48,
                "latitude": [40.4] * 48,
                "longitude": [-3.7] * 48,
            }
        )
        df_w.to_csv(pipeline_dirs["raw_weather"] / "weather_test.csv", index=False)

        # 2. Run Cleaning (Modular Batch)
        # We patch unit conversion to avoid kelvin->celsius shift if data is already near 280
        with patch.object(DataCleaner, "treat_weather_outliers", side_effect=lambda x: x):
            df_hourly, df_daily = cleaning(
                energy_dir=pipeline_dirs["raw_energy"],
                weather_dir=pipeline_dirs["raw_weather"],
                train_data=True,
                output_dir=pipeline_dirs["processed"],
            )

        assert (pipeline_dirs["processed"] / "complete_train_data_hourly.csv").exists()
        assert (pipeline_dirs["processed"] / "complete_train_data_daily.csv").exists()
        assert len(df_daily) == 2  # 48h -> 2 days

        # 3. Run Feature Engineering for both
        for freq in ["hourly", "daily"]:
            df_to_fe = df_hourly if freq == "hourly" else df_daily
            fe = FeatureEngineer(threshold=0.6, models_dir=pipeline_dirs["models"], frequency=freq)
            results = fe.run_pipeline(df_to_fe, fit=True)
            fe.save()

            assert "full" in results
            assert len(results["full"]) == len(df_to_fe)
            assert (pipeline_dirs["models"] / f"scaler_{freq}.joblib").exists()

    def test_integration_missing_energy_raises_error(self, pipeline_dirs):
        # Weather exists but energy doesn't
        df_w = pd.DataFrame({"valid_time": ["2023-01-01"], "t2m": [280]})
        df_w.to_csv(pipeline_dirs["raw_weather"] / "weather.csv", index=False)

        with pytest.raises(FileNotFoundError):
            cleaning(energy_dir=pipeline_dirs["raw_energy"], weather_dir=pipeline_dirs["raw_weather"], train_data=True)
