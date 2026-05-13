import logging
from pathlib import Path
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

logging.getLogger("data_pipeline.modeling").setLevel(logging.CRITICAL)


class TestStatisticalEvaluator:
    """Tests for model selection statistical tests."""

    def test_normality_true(self):
        """Validate normality test with normal distribution."""
        np.random.seed(42)
        normal_data = np.random.normal(loc=0, scale=1, size=100)
        data_groups = {"group1": normal_data}

        result = StatisticalEvaluator.test_normality(data_groups)
        assert result is True

    def test_normality_zero_std(self):
        """Validate normality test with zero standard deviation data."""
        data_groups = {"group1": [5, 5, 5, 5, 5]}

        result = StatisticalEvaluator.test_normality(data_groups)
        assert result is False

    def test_normality_false_non_normal_data(self):
        """Validate normality test with exponential distribution."""
        np.random.seed(42)
        non_normal_data = np.random.exponential(scale=1.0, size=100)
        assert np.std(non_normal_data) > 0
        data_groups = {"group1": non_normal_data}
        result = StatisticalEvaluator.test_normality(data_groups)
        assert result is False

    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_dataset_anova_diff_win_rmse(self, mock_normality, mock_anova):
        """Verify dataset selection using ANOVA and RMSE."""
        mock_normality.return_value = True
        mock_anova.return_value = (10.5, 0.02)

        results = {
            "Dataset_A": {"rmse": [10.0] * 3, "r2": [0.5] * 3, "mae": [4.0] * 3},
            "Dataset_B": {"rmse": [5.0] * 3, "r2": [0.8] * 3, "mae": [2.0] * 3},
        }

        best_ds, metrics = StatisticalEvaluator.select_best_dataset(results)

        mock_normality.assert_called_once()
        mock_anova.assert_called_once()
        assert best_ds == "Dataset_B"
        assert metrics["rmse"] == 5.0

    @patch("data_pipeline.modeling.friedmanchisquare")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_dataset_friedman_no_diff_win_r2(self, mock_normality, mock_friedman):
        """Verify dataset selection using Friedman and R2."""
        mock_normality.return_value = False
        mock_friedman.return_value = (2.1, 0.15)

        results = {
            "Dataset_A": {"rmse": [5.0] * 3, "r2": [0.9] * 3, "mae": [2.0] * 3},
            "Dataset_B": {"rmse": [5.0] * 3, "r2": [0.8] * 3, "mae": [2.0] * 3},
        }

        best_ds, metrics = StatisticalEvaluator.select_best_dataset(results)

        mock_normality.assert_called_once()
        mock_friedman.assert_called_once()
        assert best_ds == "Dataset_A"
        assert metrics["r2"] == 0.9

    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_dataset_win_mae(self, mock_normality, mock_anova):
        """Verify dataset selection using MAE as tie-breaker."""
        mock_normality.return_value = True
        mock_anova.return_value = (5.0, 0.01)

        results = {
            "Dataset_A": {"rmse": [5.0] * 3, "r2": [0.9] * 3, "mae": [3.0] * 3},
            "Dataset_B": {"rmse": [5.0] * 3, "r2": [0.9] * 3, "mae": [1.0] * 3},
        }

        best_ds, metrics = StatisticalEvaluator.select_best_dataset(results)

        assert best_ds == "Dataset_B"
        assert metrics["mae"] == 1.0

    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_strategy_anova_win_rmse(self, mock_normality, mock_anova):
        """Verify strategy selection using ANOVA and RMSE."""
        mock_normality.return_value = True
        mock_anova.return_value = (12.5, 0.01)

        strategy_results = {
            "expanding": {"metrics": {"rmse": [10.0] * 3, "r2": [0.5] * 3, "mae": [4.0] * 3}},
            "fixed_rolling": {"metrics": {"rmse": [5.0] * 3, "r2": [0.8] * 3, "mae": [2.0] * 3}},
        }

        best_strat = StatisticalEvaluator.select_best_strategy(strategy_results)

        mock_normality.assert_called_once()
        mock_anova.assert_called_once()
        assert best_strat == "fixed_rolling"

    @patch("data_pipeline.modeling.kruskal")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_strategy_kruskal_win_r2(self, mock_normality, mock_kruskal):
        """Verify strategy selection using Kruskal-Wallis and R2."""
        mock_normality.return_value = False
        mock_kruskal.return_value = (3.0, 0.1)

        strategy_results = {
            "expanding": {"metrics": {"rmse": [5.0] * 3, "r2": [0.8] * 3, "mae": [2.0] * 3}},
            "nested": {"metrics": {"rmse": [5.0] * 3, "r2": [0.9] * 3, "mae": [2.0] * 3}},
        }

        best_strat = StatisticalEvaluator.select_best_strategy(strategy_results)

        mock_normality.assert_called_once()
        mock_kruskal.assert_called_once()
        assert best_strat == "nested"

    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_strategy_win_mae(self, mock_normality, mock_anova):
        """Verify strategy selection using MAE as tie-breaker."""
        mock_normality.return_value = True
        mock_anova.return_value = (1.5, 0.4)

        strategy_results = {
            "expanding": {"metrics": {"rmse": [5.0] * 3, "r2": [0.9] * 3, "mae": [1.0] * 3}},
            "fixed_rolling": {"metrics": {"rmse": [5.0] * 3, "r2": [0.9] * 3, "mae": [3.0] * 3}},
        }

        best_strat = StatisticalEvaluator.select_best_strategy(strategy_results)

        assert best_strat == "expanding"


class TestModelManager:
    """Tests for model training and version management."""

    @pytest.fixture
    def dummy_df(self):
        """Fixture for synthetic temporal data."""
        np.random.seed(42)
        dates = pd.date_range(start="2016-01-01", end="2022-01-01", freq="D")
        df = pd.DataFrame(
            {
                "datetime": dates,
                "Feature_A": np.random.rand(len(dates)),
                "Feature_B": np.random.rand(len(dates)),
                "Feature_C": np.random.rand(len(dates)),
                "Load_MW": np.random.rand(len(dates)),
            }
        )
        return df

    def test_init_target_col_assignment(self):
        """Verify target column assignment by frequency."""
        manager_hourly = ModelManager(frequency="hourly")
        assert manager_hourly.target_col == "Load_MW"

        manager_daily = ModelManager(frequency="daily")
        assert manager_daily.target_col == "Load_MWh"

    @patch("pandas.read_csv")
    @patch.object(Path, "exists")
    def test_load_all_datasets(self, mock_exists, mock_read_csv):
        """Verify loading of all available datasets."""
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame({"datetime": ["2020-01-01"], "val": [1]})

        manager = ModelManager()
        datasets = manager.load_all_datasets()

        assert "full" in datasets
        assert "selected" in datasets
        assert "pca" in datasets
        assert pd.api.types.is_datetime64_any_dtype(datasets["full"]["datetime"])

    def test_generate_splits_fixed_rolling_gap(self, dummy_df):
        """Verify temporal gap in fixed rolling splits."""
        manager = ModelManager()
        splits = manager.generate_splits(dummy_df, strategy="fixed_rolling")

        assert len(splits) > 0
        train_idx, test_idx = splits[-1]

        train_dates = dummy_df.iloc[train_idx]["datetime"]
        test_dates = dummy_df.iloc[test_idx]["datetime"]

        assert (test_dates.max() - test_dates.min()).days >= 364
        assert (train_dates.max() - train_dates.min()).days >= 364
        assert (test_dates.min() - train_dates.max()).days >= 364

    def test_generate_splits_expanding(self, dummy_df):
        """Verify common start date in expanding window splits."""
        manager = ModelManager()
        splits = manager.generate_splits(dummy_df, strategy="expanding")

        primeiro_split_treino_idx = splits[0][0]
        ultimo_split_treino_idx = splits[-1][0]

        start_date_primeiro = dummy_df.iloc[primeiro_split_treino_idx]["datetime"].min()
        start_date_ultimo = dummy_df.iloc[ultimo_split_treino_idx]["datetime"].min()

        assert start_date_primeiro == start_date_ultimo == dummy_df["datetime"].min()

    @patch.object(Path, "glob")
    def test_get_next_version(self, mock_glob):
        """Verify model versioning increment logic."""
        manager = ModelManager()

        mock_path_v1 = MagicMock()
        mock_path_v1.name = "LR_v1.joblib"
        mock_path_v3 = MagicMock()
        mock_path_v3.name = "LR_v3.joblib"

        mock_glob.return_value = [mock_path_v1, mock_path_v3]

        next_version = manager._get_next_version("LR")
        assert next_version == 4

    def test_train_baseline(self):
        """Verify baseline model training and driver extraction."""
        manager = ModelManager()
        X_train = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
        y_train = pd.Series([10, 20, 30])

        model, drivers = manager.train_baseline(X_train, y_train)

        assert model is not None
        assert len(drivers) == 2
        assert isinstance(drivers, list)

    @patch("data_pipeline.modeling.optuna.create_study")
    @patch("data_pipeline.modeling.RandomForestRegressor")
    def test_train_flexible_nested(self, mock_rf_class, mock_create_study):
        """Verify flexible model training with nested cross-validation."""
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 5, "max_depth": 3}
        mock_create_study.return_value = mock_study

        mock_rf_instance = MagicMock()
        mock_rf_instance.feature_importances_ = np.array([0.4, 0.1, 0.5])
        mock_rf_class.return_value = mock_rf_instance

        manager = ModelManager()

        X_train = pd.DataFrame(
            {
                "datetime": pd.date_range("2021-01-01", periods=10, freq="ME"),
                "Feature_A": range(10),
                "Feature_B": range(10),
                "Feature_C": range(10),
            }
        )
        y_train = pd.Series(range(10))

        model, drivers = manager.train_flexible(X_train, y_train, strategy="nested")

        assert len(drivers) == 2
        assert "Feature_C" in drivers
        assert "Feature_A" in drivers
        assert "datetime" not in drivers


class TestDatabaseManager:
    """Tests for database metric logging."""

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_success(self, mock_connect):
        """Verify successful model metrics insertion."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        db_config = {"dbname": "test_db", "user": "test_user"}
        db_manager = DatabaseManager(db_config)

        db_manager.save_model_metrics(
            model_type="Random Forest",
            model_pred_type="hourly",
            file_path="models/RF_v1.joblib",
            dataset_selected="full",
            top2_drivers=["Feature_A", "Feature_B"],
            rmse=np.float64(1.23),
            mae=np.float64(0.8),
            r2=np.float64(0.95),
        )

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

        args_passed_to_execute = mock_cursor.execute.call_args[0][1]

        assert args_passed_to_execute[4] == "Feature_A, Feature_B"
        assert isinstance(args_passed_to_execute[5], float)
        assert args_passed_to_execute[5] == 1.23

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_no_config(self, mock_connect):
        """Verify handling of missing database configuration."""
        db_manager = DatabaseManager(None)

        db_manager.save_model_metrics("LR", "daily", "path", "pca", ["A"], 1.0, 1.0, 1.0)

        mock_connect.assert_not_called()

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_string_driver(self, mock_connect):
        """Verify handling of single driver string."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        db_manager = DatabaseManager({"dbname": "test_db"})

        db_manager.save_model_metrics("LR", "daily", "path", "pca", "ApenasUmDriver", 1.0, 1.0, 1.0)

        args_passed_to_execute = mock_cursor.execute.call_args[0][1]
        assert args_passed_to_execute[4] == "ApenasUmDriver"

    @patch("builtins.print")
    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_exception_handling(self, mock_connect, mock_print):
        """Verify database exception logging."""
        mock_connect.side_effect = Exception("Erro fictício de Timeout do Servidor")

        db_manager = DatabaseManager({"dbname": "test_db"})

        db_manager.save_model_metrics("LR", "daily", "path", "pca", ["A", "B"], 1.0, 1.0, 1.0)

        mock_print.assert_called_once_with("Erro ao guardar na base de dados: Erro fictício de Timeout do Servidor")


class TestPipelineOrchestrator:
    """Tests for pipeline orchestration and fold selection."""

    def test_find_best_fold_index(self):
        """Verify logic for selecting best individual fold."""
        orchestrator = PipelineOrchestrator()

        metrics = {"rmse": [10.0, 5.0, 5.0, 5.0], "r2": [0.1, 0.8, 0.9, 0.9], "mae": [5.0, 3.0, 3.0, 1.0]}

        melhor_idx = orchestrator._find_best_fold_index(metrics)

        assert melhor_idx == 3

    def test_precalculate_splits(self):
        """Verify construction of strategy-split mapping."""
        orchestrator = PipelineOrchestrator()

        orchestrator.manager = MagicMock()
        orchestrator.manager.generate_splits.return_value = [("treino1", "teste1"), ("treino2", "teste2")]

        datasets = {"full": pd.DataFrame(), "pca": pd.DataFrame()}

        splits_by_strategy = orchestrator._precalculate_splits(datasets)

        assert "expanding" in splits_by_strategy
        assert "fixed_rolling" in splits_by_strategy
        assert "nested" in splits_by_strategy

        assert "full" in splits_by_strategy["expanding"]
        assert splits_by_strategy["expanding"]["pca"] == [("treino1", "teste1"), ("treino2", "teste2")]

    @patch("data_pipeline.modeling.PipelineOrchestrator._precalculate_splits")
    def test_run_strategy_loops(self, mock_precalc):
        """Verify training loop execution and metric extraction."""
        orchestrator = PipelineOrchestrator()
        orchestrator.manager = MagicMock()
        orchestrator.manager.target_col = "Load_MW"

        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([10, 20])
        orchestrator.manager.train_baseline.return_value = (mock_model, ["DriverA", "DriverB"])

        orchestrator.evaluator.select_best_dataset = MagicMock(
            return_value=("full", {"rmse": 2.0, "r2": 0.9, "mae": 1.5})
        )

        df = pd.DataFrame({"Load_MW": [10, 20, 30, 40], "Feature": [1, 2, 3, 4]})
        datasets = {"full": df}

        splits_by_strategy = {"fixed_rolling": {"full": [([0, 1], [2, 3])]}}

        resultado = orchestrator._run_strategy_loops(
            model_type="baseline", strategy="fixed_rolling", datasets=datasets, splits_by_strategy=splits_by_strategy
        )

        assert resultado["dataset"] == "full"
        assert "metrics" in resultado
        assert len(resultado["metrics"]["models"]) == 1
        assert resultado["metrics"]["drivers"][0] == ["DriverA", "DriverB"]

    @patch("data_pipeline.modeling.joblib.dump")
    def test_evaluate_and_save_model(self, mock_joblib_dump):
        """Verify end-to-end model evaluation and persistence."""
        orchestrator = PipelineOrchestrator()
        orchestrator.manager = MagicMock()
        orchestrator.manager._get_next_version.return_value = 1
        orchestrator.manager.models_dir = MagicMock()
        orchestrator.manager.models_dir.__truediv__.return_value = "caminho/falso/LR_v1.joblib"

        orchestrator.db_manager = MagicMock()

        orchestrator._run_strategy_loops = MagicMock(
            return_value={
                "dataset": "pca",
                "metrics": {
                    "rmse": [10.0, 5.0, 2.0],
                    "r2": [0.5, 0.7, 0.9],
                    "mae": [3.0, 2.0, 1.0],
                    "models": ["modelo_mau", "modelo_medio", "modelo_bom"],
                    "drivers": [["D1"], ["D2"], ["Top1", "Top2"]],
                },
            }
        )

        orchestrator.evaluator.select_best_strategy.return_value = "expanding"

        orchestrator._evaluate_and_save_model(model_type="baseline", freq="hourly", datasets={}, splits_by_strategy={})

        mock_joblib_dump.assert_called_once_with("modelo_bom", "caminho/falso/LR_v1.joblib")

        orchestrator.db_manager.save_model_metrics.assert_called_once()
        args_chamados = orchestrator.db_manager.save_model_metrics.call_args[1]

        assert args_chamados["dataset_selected"] == "pca"
        assert args_chamados["top2_drivers"] == ["Top1", "Top2"]
        assert args_chamados["rmse"] == 2.0

    @patch("data_pipeline.modeling.ModelManager")
    def test_run_empty_datasets(self, mock_model_manager_class):
        """Verify orchestration behavior with no input data."""
        orchestrator = PipelineOrchestrator()

        mock_manager_instance = MagicMock()
        mock_manager_instance.load_all_datasets.return_value = {}
        mock_model_manager_class.return_value = mock_manager_instance

        orchestrator.run()

        mock_manager_instance.generate_splits.assert_not_called()

    @patch("data_pipeline.modeling.ModelManager")
    def test_run_full_flow(self, mock_model_manager_class):
        """Verify complete pipeline orchestration flow."""
        orchestrator = PipelineOrchestrator()

        orchestrator._precalculate_splits = MagicMock()
        orchestrator._evaluate_and_save_model = MagicMock()

        mock_manager_instance = MagicMock()
        mock_manager_instance.load_all_datasets.return_value = {"full": "dataset_falso"}
        mock_model_manager_class.return_value = mock_manager_instance

        orchestrator.run()

        assert mock_model_manager_class.call_count == 2
        assert orchestrator._evaluate_and_save_model.call_count == 4
