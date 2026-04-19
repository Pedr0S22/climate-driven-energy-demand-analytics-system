import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from data_pipeline.modeling import (
    DatabaseManager,
    ModelManager,
    PipelineOrchestrator,
    StatisticalEvaluator,
)

# Silenciar os logs durante os testes para não sujar a consola
logging.getLogger("data_pipeline.modeling").setLevel(logging.CRITICAL)


class TestStatisticalEvaluator:
    """Testes para a classe StatisticalEvaluator"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.evaluator = StatisticalEvaluator()

    def test_normality_with_normal_data(self):
        np.random.seed(42)
        normal_data = {
            "group1": np.random.normal(loc=100, scale=5, size=50),
            "group2": np.random.normal(loc=100, scale=5, size=50),
        }
        result = self.evaluator.test_normality(normal_data)
        assert result

    def test_normality_with_non_normal_data(self):
        np.random.seed(42)
        non_normal_data = {
            "group1": np.random.exponential(scale=2, size=50),
            "group2": np.random.exponential(scale=2, size=50),
        }
        result = self.evaluator.test_normality(non_normal_data)
        assert not result

    def test_select_best_dataset_by_rmse(self):
        results_dict = {
            "full": {"rmse": [100.0] * 5, "r2": [0.9] * 5, "mae": [80.0] * 5},
            "selected": {"rmse": [150.0] * 5, "r2": [0.85] * 5, "mae": [120.0] * 5},
            "pca": {"rmse": [120.0] * 5, "r2": [0.88] * 5, "mae": [100.0] * 5},
        }
        best_ds, metrics = self.evaluator.select_best_dataset(results_dict)
        assert best_ds == "full"

    def test_select_best_dataset_tie_breakers(self):
        # Aumentamos o tamanho da amostra e adicionamos ruído mínimo para evitar avisos do Scipy
        results_dict = {
            "ds1": {"rmse": [100.0, 100.1, 99.9, 100.0, 100.1], "r2": [0.80] * 5, "mae": [50.0] * 5},
            "ds2": {"rmse": [100.0, 100.1, 99.9, 100.0, 100.1], "r2": [0.90] * 5, "mae": [60.0] * 5},
            "ds3": {"rmse": [100.0, 100.1, 99.9, 100.0, 100.1], "r2": [0.90] * 5, "mae": [40.0] * 5},
        }
        best_ds, _ = self.evaluator.select_best_dataset(results_dict)
        assert best_ds == "ds3"  # Empata RMSE e R2, ganha pelo menor MAE

    def test_select_best_strategy(self):
        strategy_results = {
            "fixed_rolling": {"metrics": {"rmse": [100.0] * 5, "r2": [0.9] * 5, "mae": [80.0] * 5}},
            "expanding": {"metrics": {"rmse": [150.0] * 5, "r2": [0.8] * 5, "mae": [100.0] * 5}},
            "nested": {"metrics": {"rmse": [120.0] * 5, "r2": [0.85] * 5, "mae": [90.0] * 5}},
        }
        best_strat = self.evaluator.select_best_strategy(strategy_results)
        assert best_strat == "fixed_rolling"


class TestModelManager:
    """Testes para a classe ModelManager"""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.temp_dir = tmp_path
        self.manager = ModelManager()
        self.manager.models_dir = self.temp_dir

        dates = pd.date_range(start="2018-01-01", end="2024-12-31", freq="D")
        self.test_data = pd.DataFrame(
            {
                "datetime": dates,
                "Load_MW": np.random.normal(loc=2000, scale=300, size=len(dates)),
                "feature1": np.random.normal(loc=0, scale=1, size=len(dates)),
            }
        )

    def test_generate_splits_temporal_order(self):
        splits = self.manager.generate_splits(self.test_data, strategy="fixed_rolling")
        assert len(splits) > 0
        for train_idx, test_idx in splits:
            assert max(train_idx) < min(test_idx)
            assert len(set(train_idx) & set(test_idx)) == 0

    def test_generate_splits_edge_case_insufficient_data(self):
        dates = pd.date_range(start="2020-01-01", end="2021-12-31", freq="D")
        small_data = pd.DataFrame(
            {
                "datetime": dates,
                "Load_MW": np.random.normal(loc=2000, scale=300, size=len(dates)),
            }
        )
        splits = self.manager.generate_splits(small_data)
        assert len(splits) == 0

    def test_train_baseline_valid_data(self):
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f"feat{i}" for i in range(5)])
        y = pd.Series(np.random.randn(100))
        model = self.manager.train_baseline(X, y)
        assert model is not None

    @patch("data_pipeline.modeling.optuna.create_study")
    def test_train_flexible_mocked_optuna(self, mock_create_study):
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 20, "max_depth": 5}
        mock_create_study.return_value = mock_study

        X_train = self.test_data[["datetime", "feature1"]].copy()
        y_train = self.test_data["Load_MW"].copy()

        model = self.manager.train_flexible(X_train, y_train, strategy="expanding")
        assert model is not None

    @patch("data_pipeline.modeling.optuna.create_study")
    def test_train_flexible_nested_strategy(self, mock_create_study):
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 10, "max_depth": 3}
        mock_create_study.return_value = mock_study

        X_train = self.test_data[["datetime", "feature1"]].copy()
        y_train = self.test_data["Load_MW"].copy()

        model = self.manager.train_flexible(X_train, y_train, strategy="nested")
        assert model is not None

    @patch("data_pipeline.modeling.Path.exists")
    @patch("data_pipeline.modeling.pd.read_csv")
    def test_load_all_datasets(self, mock_read_csv, mock_exists):
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame({"datetime": ["2023-01-01"], "val": [1]})

        datasets = self.manager.load_all_datasets()
        assert "full" in datasets
        assert "pca" in datasets

    @patch("data_pipeline.modeling.Path.glob")
    def test_get_next_version(self, mock_glob):
        mock_file1, mock_file3 = MagicMock(), MagicMock()
        mock_file1.name = "LR_v1.joblib"
        mock_file3.name = "LR_v3.joblib"
        mock_glob.return_value = [mock_file1, mock_file3]

        next_v = self.manager._get_next_version("LR")
        assert next_v == 4


class TestDatabaseManager:
    """Testes dedicados à integração com a Base de Dados"""

    def test_save_model_metrics_no_config(self):
        """Garante que o código não 'quebra' se a configuração da BD for nula"""
        manager = DatabaseManager(None)
        # Usar keyword arguments (nome=valor) evita que a ordem troque as voltas!
        manager.save_model_metrics(
            model_type="RF", model_pred_type="hourly", file_path="path", rmse=1.0, mae=1.0, r2=1.0
        )

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_success(self, mock_connect):
        """Testa se a query de inserção correta é chamada sem erros"""
        db_config = {"dbname": "test_db", "user": "test"}
        manager = DatabaseManager(db_config)

        # Simula o Context Manager do psycopg2 (with conn.cursor()...)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Adicionado o 'hourly' como 2º argumento
        manager.save_model_metrics("Random Forest", "hourly", "models/hourly/RF_v1.joblib", 10.5, 5.2, 0.95)

        # Garante que o cur.execute foi chamado
        assert mock_cursor.execute.called

        # Verifica se os argumentos passados para a BD estão corretos
        call_args = mock_cursor.execute.call_args[0]
        assert "INSERT INTO model" in call_args[0]

        # Adicionado o 'hourly' na verificação da tupla também!
        assert call_args[1] == ("Random Forest", "hourly", "models/hourly/RF_v1.joblib", 10.5, 5.2, 0.95)


class TestPipelineOrchestrator:
    """Testa a nova classe de orquestração do pipeline completo"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.orchestrator = PipelineOrchestrator(db_config=None)

    def test_find_best_fold_index(self):
        """Testa a lógica de desempate para o melhor Fold interno"""
        vencedora_metrics = {
            "rmse": [15.0, 10.0, 10.0, 12.0],
            "r2": [0.80, 0.90, 0.90, 0.85],
            "mae": [8.0, 5.0, 4.0, 6.0],  # No índice 2 e 3 há empate de RMSE/R2. Ganha o menor MAE (índice 2).
        }

        best_idx = self.orchestrator._find_best_fold_index(vencedora_metrics)
        assert best_idx == 2

    @patch("data_pipeline.modeling.joblib.dump")
    @patch("data_pipeline.modeling.ModelManager.load_all_datasets")
    @patch("data_pipeline.modeling.PipelineOrchestrator._run_strategy_loops")
    @patch("data_pipeline.modeling.DatabaseManager.save_model_metrics")
    def test_pipeline_run_integration(self, mock_db_save, mock_run_loops, mock_load, mock_dump, tmp_path):
        """Testa o flow global da aplicação mockando as partes pesadas de treino e disco"""

        # 1. Cria DataFrames Falsos com ruído para evitar erros estatísticos
        dates = pd.date_range("2018-01-01", end="2024-01-01", freq="W")
        df = pd.DataFrame(
            {
                "datetime": dates,
                "Load_MW": np.random.normal(2000, 500, len(dates)),
                "Load_MWh": np.random.normal(50000, 5000, len(dates)),
            }
        )

        # Simula o load_datasets
        mock_load.return_value = {"full": df}

        # Simula o _run_strategy_loops para devolver métricas variadas
        # 2 frequencies * 2 model types * 3 strategies = 12 calls
        mock_run_loops.side_effect = [
            {
                "dataset": "full",
                "metrics": {
                    "rmse": np.random.uniform(10, 20, 5),
                    "r2": np.random.uniform(0.7, 0.9, 5),
                    "mae": np.random.uniform(5, 10, 5),
                    "models": ["MockedModelObject"] * 5,
                },
            }
            for _ in range(12)
        ]

        # Injetamos o tmp_path no orquestrador
        self.orchestrator.models_dir = tmp_path

        # 2. Executa a classe
        try:
            self.orchestrator.run()
            pipeline_ran = True
        except Exception as e:
            pipeline_ran = False
            print(f"Pipeline falhou com erro: {e}")

        # 3. Asserções rigorosas
        assert pipeline_ran, "A pipeline orquestrada quebrou."
        assert mock_dump.called, "O orquestrador não tentou guardar o modelo."
        assert mock_run_loops.called, "O orquestrador não chamou as estratégias de validação cruzada."
