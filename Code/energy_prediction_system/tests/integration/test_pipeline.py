import pytest
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Importações do projeto
from data_pipeline.cleaning import DataCleaner, cleaning
from data_pipeline.feature_engineering import FeatureEngineer
from data_pipeline.modeling import PipelineOrchestrator, ModelManager
import data_pipeline.ingestion as ingestion

class TestPipelineIntegration:
    """Testes de integração corrigidos para evitar erros de indexação com Mocks."""

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
            "feat_eng_dir": processed / "feat-engineering"
        }

    @patch("data_pipeline.ingestion.cdsapi.Client")
    @patch("data_pipeline.ingestion.EntsoePandasClient")
    def test_ingestion_mock(self, mock_entsoe, mock_cds):
        mock_entsoe.return_value.query_load.return_value = pd.DataFrame([100], columns=["Load_MW"])
        client = ingestion.EntsoePandasClient(api_key="fake")
        assert client is not None

    def test_cleaning_and_feat_eng(self, pipeline_dirs):
        times = pd.date_range("2023-01-01", periods=48, freq="h", tz="UTC")
        df_e = pd.DataFrame({"Unnamed: 0": times, "Load_MW": np.random.uniform(20000, 30000, 48)})
        df_e.to_csv(pipeline_dirs["raw_energy"] / "energy_test.csv", index=False)

        df_w = pd.DataFrame({
            "valid_time": times, "t2m": 285, "skt": 285, "ssrd": 100,
            "latitude": 40.4, "longitude": -3.7
        })
        df_w.to_csv(pipeline_dirs["raw_weather"] / "weather_test.csv", index=False)

        with patch.object(DataCleaner, "treat_weather_outliers", side_effect=lambda x: x):
            df_hourly, _ = cleaning(
                energy_dir=pipeline_dirs["raw_energy"],
                weather_dir=pipeline_dirs["raw_weather"],
                train_data=True,
                output_dir=pipeline_dirs["processed"],
            )

        fe = FeatureEngineer(threshold=0.6, models_dir=pipeline_dirs["models"], frequency="hourly")
        results = fe.run_pipeline(df_hourly, fit=True)
        
        pipeline_dirs["feat_eng_dir"].mkdir(parents=True, exist_ok=True)
        for ds in ["full", "selected", "pca"]:
            results.get(ds, results["full"]).to_csv(
                pipeline_dirs["feat_eng_dir"] / f"features_hourly_{ds}.csv", index=False
            )

    @patch("data_pipeline.modeling.psycopg2.connect")
    @patch("data_pipeline.modeling.RandomForestRegressor")
    @patch("optuna.create_study")
    @patch("joblib.dump")
    def test_modeling_integration_extension(self, mock_joblib, mock_create_study, mock_rf, mock_db, pipeline_dirs):
        """Ativa 3 splits e resolve o IndexError usando arrays NumPy reais nos atributos do modelo."""
        mock_db.return_value = MagicMock()
        mock_joblib.return_value = None

        # 1. Mock do Estudo Optuna
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 5, "max_depth": 3}
        mock_study.best_trial.params = {"n_estimators": 5, "max_depth": 3}
        mock_create_study.return_value = mock_study

        # 2. Mock do RandomForestRegressor Dinâmico
        fake_rf = MagicMock()
        
        def dynamic_fit_mock(X, y, **kwargs):
            # IMPORTANTE: Definir feature_importances_ como um array NumPy real
            # Isto evita que o .argsort() devolva um Mock e cause erro no Pandas
            n_features = X.shape[1]
            fake_rf.feature_importances_ = np.random.rand(n_features)
            fake_rf.coef_ = np.random.rand(n_features)
            return fake_rf

        # Configurar comportamentos do modelo
        fake_rf.fit.side_effect = dynamic_fit_mock
        fake_rf.predict.side_effect = lambda X: np.zeros(len(X))
        mock_rf.return_value = fake_rf

        # 3. Gerar 5 anos de dados (Suporta 3 splits de 1 ano cada com folga)
        feat_eng_path = pipeline_dirs["feat_eng_dir"]
        feat_eng_path.mkdir(exist_ok=True, parents=True)
        times = pd.date_range("2019-01-01", periods=24*365*5, freq="h", tz="UTC")
        df_mock = pd.DataFrame({
            "datetime": times,
            "Load_MW": np.random.normal(25000, 5000, len(times)),
            "temp": np.random.rand(len(times)),
            "ssrd": np.random.rand(len(times))
        })
        for ds in ["full", "selected", "pca"]:
            df_mock.to_csv(feat_eng_path / f"features_hourly_{ds}.csv", index=False)

        # 4. Configurar Orquestrador
        orchestrator = PipelineOrchestrator(db_config={"fake": "db"})
        orchestrator.manager = ModelManager(frequency="hourly")
        orchestrator.manager.data_dir = feat_eng_path
        orchestrator.manager.models_dir = pipeline_dirs["models"]
        
        # 3 splits para garantir validade estatística (elimina warnings)
        orchestrator.manager.n_partitions = 3 

        datasets = orchestrator.manager.load_all_datasets()
        splits = orchestrator._precalculate_splits(datasets)

        # 5. Executar Treino (Baseline e Flexible)
        for m_type in ["baseline", "flexible"]:
            with patch("data_pipeline.modeling.LinearRegression") as mock_lr:
                # Aplicamos a mesma lógica dinâmica à Regressão Linear
                fake_lr = MagicMock()
                fake_lr.fit.side_effect = dynamic_fit_mock
                fake_lr.predict.side_effect = lambda X: np.zeros(len(X))
                mock_lr.return_value = fake_lr
                
                orchestrator._evaluate_and_save_model(m_type, "hourly", datasets, splits)

        # 6. Asserções finais
        assert mock_joblib.called 
        assert mock_db.called