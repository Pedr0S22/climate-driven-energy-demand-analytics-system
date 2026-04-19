"""
Integration Tests with focused coverage on modeling.py and full end-to-end pipeline validation.
"""

import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from data_pipeline.cleaning import cleaning
from data_pipeline.feature_engineering import FeatureEngineer
from data_pipeline.modeling import (
    DatabaseManager,
    ModelManager,
    PipelineOrchestrator,
)

# Silenciar os logs para os testes não encherem o ecrã
logging.getLogger("data_pipeline.modeling").setLevel(logging.CRITICAL)


class TestModelingFullCoverage:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.temp_dir = tmp_path
        self.models_dir = self.temp_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # DADOS SINTÉTICOS: 3 anos e 2 meses de dados diários.
        # Isto garante dados suficientes para passar na matemática rigorosa
        # de splits temporais (que exige gap de 1 ano + 1 ano de teste).
        dates = pd.date_range(start="2020-01-01", end="2023-03-01", freq="D")

        self.df = pd.DataFrame(
            {
                "datetime": dates,
                "Load_MW": np.random.normal(2000, 100, size=len(dates)),  # Para hourly
                "Load_MWh": np.random.normal(48000, 2000, size=len(dates)),  # Para daily
                "temperatura": np.random.normal(15, 5, size=len(dates)),
            }
        )

    @patch("data_pipeline.modeling.psycopg2.connect")
    @patch("data_pipeline.modeling.joblib.dump")
    @patch("data_pipeline.modeling.optuna.create_study")
    @patch("data_pipeline.modeling.ModelManager.load_all_datasets")
    def test_run_orchestrator_pipeline_full_coverage(self, mock_load, mock_create_study, mock_dump, mock_db_connect):
        """
        Executa a mega pipeline real (Orchestrator)!
        Cobre os loops Hourly e Daily, as 3 estratégias e a inserção na BD.
        """
        # 1. OPTUNA RÁPIDO: Enganamos o Optuna para não demorar horas
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 2, "max_depth": 2}
        mock_create_study.return_value = mock_study

        # 2. DATASETS FALSOS: Retornamos os 3 datasets com ruído para evitar avisos estatísticos
        df_full = self.df.copy()
        df_selected = self.df.copy()
        df_selected["Load_MW"] += np.random.normal(0, 1, size=len(df_selected))
        df_pca = self.df.copy()
        df_pca["Load_MW"] -= np.random.normal(0, 1, size=len(df_pca))

        mock_load.return_value = {"full": df_full, "selected": df_selected, "pca": df_pca}

        # 3. MOCK BASE DE DADOS: Finge que ligou ao PostgreSQL sem falhar
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # 4. EXECUTA O CÓDIGO REAL DA PIPELINE
        db_config = {"dbname": "test", "user": "test"}  # Passamos config para forçar a entrada no bloco da BD
        orchestrator = PipelineOrchestrator(db_config=db_config)

        # Injetamos o diretório temporário para não sujar o PC local
        orchestrator.models_dir = self.models_dir

        try:
            # Esta linha executa mais de 80% do ficheiro modeling.py num só golpe!
            orchestrator.run()
            sucesso = True
        except Exception as e:
            print(f"A pipeline quebrou: {e}")
            sucesso = False

        assert sucesso, "O PipelineOrchestrator falhou ao processar os dados!"
        assert mock_dump.called, "Os modelos não foram guardados no disco!"
        assert mock_cursor.execute.called, "A pipeline não tentou gravar na Base de Dados!"

    # =========================================================================
    # Testes Auxiliares (Tapar os "buracos" dos Edge Cases / Erros)
    # =========================================================================

    def test_get_next_version_file_reading(self):
        """Cobre a leitura de versões antigas de modelos no disco."""
        manager = ModelManager()
        manager.models_dir = self.models_dir
        (self.models_dir / "LR_v1.joblib").touch()
        (self.models_dir / "LR_v3.joblib").touch()

        version = manager._get_next_version("LR")
        assert version == 4

    @patch("data_pipeline.modeling.Path.exists")
    @patch("data_pipeline.modeling.pd.read_csv")
    def test_load_all_datasets_disk_reading(self, mock_read, mock_exists):
        """Cobre o carregamento do disco quando os ficheiros existem."""
        manager = ModelManager()
        mock_exists.return_value = True
        mock_read.return_value = pd.DataFrame({"datetime": ["2020-01-01"], "val": [1]})

        ds = manager.load_all_datasets()
        assert "full" in ds

    @patch("data_pipeline.modeling.optuna.create_study")
    def test_train_flexible_edge_cases(self, mock_create_study):
        """Cobre a estratégia 'nested' e o fallback de dados insuficientes."""
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 2, "max_depth": 2}
        mock_create_study.return_value = mock_study

        manager = ModelManager()

        # 1. Testar modo Nested explícito
        model_nested = manager.train_flexible(
            self.df[["datetime", "temperatura"]], self.df["Load_MW"], strategy="nested"
        )
        assert model_nested is not None

        # 2. Testar modo Expanding com poucos dados (aciona o fallback do split 80/20)
        small_df = self.df.iloc[:50].copy()  # Apenas 50 dias, insuficiente para gap de 2 anos
        model_small = manager.train_flexible(
            small_df[["datetime", "temperatura"]], small_df["Load_MW"], strategy="expanding"
        )
        assert model_small is not None

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_database_manager_exception(self, mock_connect):
        """Cobre o except bloco se a Base de Dados estiver desligada."""
        manager = DatabaseManager({"dbname": "test"})
        # Força o PostgreSQL a atirar um erro
        mock_connect.side_effect = Exception("Docker is down!")

        # Se a pipeline quebrar aqui, o teste falha (o objetivo é que o except apanhe o erro silenciosamente)
        try:
            manager.save_model_metrics(
                model_type="RF",
                model_pred_type="hourly",  # <-- O parâmetro novo!
                file_path="path/model.joblib",
                rmse=1.0,
                mae=1.0,
                r2=1.0,
            )
            passed = True
        except Exception:
            passed = False

        assert passed, "Uma falha na base de dados parou a execução da pipeline!"


# =========================================================================
# NOVOS TESTES: End-to-End Full Pipeline (Ingestion -> Cleaning -> FE -> Modeling)
# =========================================================================


def setup_synthetic_raw_data(raw_energy_dir, raw_weather_dir, freq="h"):
    """Gera ficheiros CSV sintéticos mínimos para o pipeline processar."""
    # Precisamos de dados suficientes para os splits (3 anos min)
    periods = 100 if freq == "h" else 50
    dates = pd.date_range("2023-01-01", periods=periods, freq=freq, tz="UTC")

    # Energy: O cleaner sempre espera "Load_MW" inicialmente
    df_e = pd.DataFrame({"Unnamed: 0": dates, "Load_MW": np.random.uniform(20000, 30000, len(dates))})
    df_e.to_csv(raw_energy_dir / "energy_raw.csv", index=False)

    # Weather
    weather_cols = [
        "valid_time",
        "latitude",
        "longitude",
        "t2m",
        "u10",
        "v10",
        "ssrd",
        "tp",
        "d2m",
        "skt",
        "strd",
        "sp",
        "stl1",
        "swvl1",
    ]
    df_w = pd.DataFrame({col: np.random.rand(len(dates)) for col in weather_cols})
    df_w["valid_time"] = dates
    df_w["latitude"] = 40.4
    df_w["longitude"] = -3.7
    for col in ["t2m", "d2m", "skt", "stl1"]:
        df_w[col] = df_w[col] * 20 + 273.15

    df_w.to_csv(raw_weather_dir / "weather_raw.csv", index=False)


@patch("data_pipeline.modeling.psycopg2.connect")
@patch("data_pipeline.modeling.optuna.create_study")
@patch("data_pipeline.modeling.joblib.dump")
@patch("data_pipeline.modeling.ModelManager.generate_splits")
@patch("data_pipeline.modeling.StatisticalEvaluator.select_best_dataset")
@patch("data_pipeline.modeling.StatisticalEvaluator.select_best_strategy")
def test_full_pipeline_hourly_integration(mock_strat, mock_ds, mock_splits, mock_dump, mock_optuna, mock_db, tmp_path):
    """Testa o pipeline completo de ponta a ponta (Hourly)."""
    # Setup Dirs
    raw_energy = tmp_path / "raw" / "energy"
    raw_weather = tmp_path / "raw" / "weather"
    processed = tmp_path / "processed"
    models = tmp_path / "models"
    for d in [raw_energy, raw_weather, processed, models]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. MOCK INGESTION: Drop synthetic files
    setup_synthetic_raw_data(raw_energy, raw_weather, freq="h")

    # 2. CLEANING
    df_hourly, _ = cleaning(energy_dir=raw_energy, weather_dir=raw_weather, train_data=True, output_dir=processed)
    assert not df_hourly.empty

    # 3. FEATURE ENGINEERING
    fe = FeatureEngineer(threshold=0.6, models_dir=models, frequency="hourly")
    fe.run_pipeline(df_hourly, fit=True)
    fe.save()

    # 4. MODELING (Orchestrator)
    mock_study = MagicMock()
    mock_study.best_params = {"n_estimators": 1, "max_depth": 1}
    mock_optuna.return_value = mock_study

    # Mock splits to return 1 fold for speed
    mock_splits.return_value = [(np.arange(0, 40), np.arange(40, 50))]
    mock_ds.return_value = ("full", {"rmse": 10.0, "r2": 0.9, "mae": 5.0})
    mock_strat.return_value = "fixed_rolling"

    orchestrator = PipelineOrchestrator(db_config=None)
    orchestrator.models_dir = models

    with patch("data_pipeline.modeling.ModelManager.load_all_datasets", autospec=True) as mock_load:
        dummy_ds = {"full": df_hourly.copy(), "pca": df_hourly.copy(), "selected": df_hourly.copy()}
        # Only return data for hourly
        mock_load.side_effect = lambda self_manager: dummy_ds if self_manager.frequency == "hourly" else {}
        orchestrator.run()

    assert mock_dump.called


@patch("data_pipeline.modeling.psycopg2.connect")
@patch("data_pipeline.modeling.optuna.create_study")
@patch("data_pipeline.modeling.joblib.dump")
@patch("data_pipeline.modeling.ModelManager.generate_splits")
@patch("data_pipeline.modeling.StatisticalEvaluator.select_best_dataset")
@patch("data_pipeline.modeling.StatisticalEvaluator.select_best_strategy")
def test_full_pipeline_daily_integration(mock_strat, mock_ds, mock_splits, mock_dump, mock_optuna, mock_db, tmp_path):
    """Testa o pipeline completo de ponta a ponta (Daily)."""
    # Setup Dirs
    raw_energy = tmp_path / "raw" / "energy"
    raw_weather = tmp_path / "raw" / "weather"
    processed = tmp_path / "processed"
    models = tmp_path / "models"
    for d in [raw_energy, raw_weather, processed, models]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. MOCK INGESTION: Drop synthetic files
    setup_synthetic_raw_data(raw_energy, raw_weather, freq="D")

    # 2. CLEANING
    _, df_daily = cleaning(energy_dir=raw_energy, weather_dir=raw_weather, train_data=True, output_dir=processed)
    assert not df_daily.empty

    # 3. FEATURE ENGINEERING
    fe = FeatureEngineer(threshold=0.6, models_dir=models, frequency="daily")
    fe.run_pipeline(df_daily, fit=True)
    fe.save()

    # 4. MODELING (Orchestrator)
    mock_study = MagicMock()
    mock_study.best_params = {"n_estimators": 1, "max_depth": 1}
    mock_optuna.return_value = mock_study

    mock_splits.return_value = [(np.arange(0, 40), np.arange(40, 50))]
    mock_ds.return_value = ("full", {"rmse": 10.0, "r2": 0.9, "mae": 5.0})
    mock_strat.return_value = "fixed_rolling"

    orchestrator = PipelineOrchestrator(db_config=None)
    orchestrator.models_dir = models

    with patch("data_pipeline.modeling.ModelManager.load_all_datasets", autospec=True) as mock_load:
        dummy_ds = {"full": df_daily.copy(), "pca": df_daily.copy(), "selected": df_daily.copy()}
        # Only return data for daily
        mock_load.side_effect = lambda self_manager: dummy_ds if self_manager.frequency == "daily" else {}
        orchestrator.run()

    assert mock_dump.called
