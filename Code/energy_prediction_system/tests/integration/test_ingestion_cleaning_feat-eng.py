from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from data_pipeline.cleaning import cleaning, energy, weather
from data_pipeline.feature_engineering import FeatureEngineer

# Import modules to test

# =======================================
# INTEGRATION TESTS
# =======================================


class TestPipelineIntegration:
    """Integration tests for the Ingestion -> Cleaning -> Feature Engineering pipeline."""

    @pytest.fixture
    def pipeline_dirs(self, tmp_path):
        """Creates temporary directory structure for the pipeline."""
        base = tmp_path / "project"
        raw_energy = base / "data" / "raw" / "energy"
        raw_weather = base / "data" / "raw" / "weather"
        corrigido_energy = base / "data" / "raw" / "energy_corrigido"
        corrigido_weather = base / "data" / "raw" / "weather_corrigido"
        processed = base / "data" / "processed"
        models = base / "models" / "feat-engineering"

        for d in [raw_energy, raw_weather, corrigido_energy, corrigido_weather, processed, models]:
            d.mkdir(parents=True, exist_ok=True)

        return {
            "root": base,
            "raw_energy": raw_energy,
            "raw_weather": raw_weather,
            "corrigido_energy": corrigido_energy,
            "corrigido_weather": corrigido_weather,
            "processed": processed,
            "models": models,
        }

    @patch("data_pipeline.ingestion.EntsoePandasClient")
    @patch("data_pipeline.ingestion.cdsapi.Client")
    def test_full_pipeline_flow(self, mock_cds, mock_entsoe, pipeline_dirs):
        """
        Input: Mocked API responses.
        Output: Final feature-engineered datasets.
        Logic: Verifies the end-to-end data flow and integrity.
        """
        start_date, end_date = "2020-01-01", "2025-12-31"

        # 1. Mock ENTSO-E
        mock_client_entsoe = MagicMock()
        mock_load = pd.Series(
            np.random.uniform(20000, 30000, 100),
            index=pd.date_range("2020-01-01", periods=100, freq="h", tz="Europe/Madrid"),
            name="Load_MW",
        )
        mock_client_entsoe.query_load.return_value = mock_load
        mock_entsoe.return_value = mock_client_entsoe

        # 2. Mock Copernicus
        mock_client_cds = MagicMock()
        mock_cds.return_value = mock_client_cds

        # Create all 7 files expected by cleaning.weather
        weather_data = {
            "valid_time": pd.date_range("2020-01-01", periods=100, freq="h", tz="UTC"),
            "t2m": np.random.uniform(273, 300, 100),
            "skt": np.random.uniform(273, 300, 100),
            "d2m": np.random.uniform(270, 290, 100),
            "stl1": np.random.uniform(270, 290, 100),
            "ssrd": np.random.uniform(0, 1000000, 100),
            "strd": np.random.uniform(200000, 500000, 100),
            "sp": np.random.uniform(90000, 110000, 100),
            "tp": np.random.uniform(0, 0.01, 100),
            "u10": np.random.uniform(-5, 5, 100),
            "v10": np.random.uniform(-5, 5, 100),
            "swvl1": np.random.uniform(0.1, 0.4, 100),
            "latitude": [40.4] * 100,
            "longitude": [-3.7] * 100,
        }

        filenames = [
            f"era5_timeseries_{start_date}_to_{end_date}.csv",
            "reanalysis-era5-land-timeseries-sfc-2m-temperatureauafbxo0.csv",
            "reanalysis-era5-land-timeseries-sfc-pressure-precipitationtwpvvkbd.csv",
            "reanalysis-era5-land-timeseries-sfc-radiation-heathoyt7mym.csv",
            "reanalysis-era5-land-timeseries-sfc-skin-temperaturercarv5g8.csv",
            "reanalysis-era5-land-timeseries-sfc-soil-temperatureokgb55eq.csv",
            "reanalysis-era5-land-timeseries-sfc-soil-waterp9pn16zx.csv",
        ]
        for fname in filenames:
            pd.DataFrame(weather_data).to_csv(pipeline_dirs["raw_weather"] / fname, index=False)

        # Mock energy file
        entsoe_path = pipeline_dirs["raw_energy"] / f"entsoe_ES_load_{start_date}_to_{end_date}.csv"
        # Entsoe data in CSV usually has 'Unnamed: 0' as index when read back
        df_load_csv = mock_load.to_frame()
        df_load_csv.index.name = "Unnamed: 0"
        df_load_csv.to_csv(entsoe_path)

        # B. Cleaning
        # Mocking complex alignment/treatment to focus on integration flow
        with patch("data_pipeline.cleaning.outliers_treatment", side_effect=lambda x: x):
            with patch("data_pipeline.cleaning.hourly_aggregation", side_effect=lambda x: x):
                energy(pipeline_dirs["raw_energy"], pasta_saida=pipeline_dirs["corrigido_energy"])
                weather(pasta_entrada=pipeline_dirs["raw_weather"], pasta_saida=pipeline_dirs["corrigido_weather"])

                df_clean = cleaning(
                    pasta_energy_corrigido=pipeline_dirs["corrigido_energy"],
                    pasta_weather_corrigido=pipeline_dirs["corrigido_weather"],
                    train_data=True,
                    pasta_saida=pipeline_dirs["processed"],
                )

        assert not df_clean.empty
        assert "Load_MW" in df_clean.columns

        # C. Feature Engineering
        fe = FeatureEngineer(threshold=0.6, models_dir=pipeline_dirs["models"])
        results = fe.run_pipeline(df_clean, fit=True)
        fe.save()

        assert "full" in results
        assert len(results["full"]) == len(df_clean)
        assert (pipeline_dirs["models"] / "pca.joblib").exists()

    def test_integration_edge_missing_files(self, pipeline_dirs):
        """
        Edge Case: Cleaning is called but energy folder is empty.
        Expected: Raises FileNotFoundError.
        """
        with pytest.raises(FileNotFoundError):
            cleaning(
                pasta_energy_corrigido=pipeline_dirs["corrigido_energy"],
                pasta_weather_corrigido=pipeline_dirs["corrigido_weather"],
                train_data=True,
                pasta_saida=pipeline_dirs["processed"],
            )
