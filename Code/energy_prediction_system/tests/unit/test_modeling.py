"""
Unit Tests para o módulo data_pipeline.modeling
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import tempfile
import logging

# IMPORTANTE: Confirma se o teu import funciona assim, caso contrário usa "from src.data_pipeline.modeling import ..."
from data_pipeline.modeling import (
    StatisticalEvaluator, 
    ModelManager, 
    DatabaseManager, 
    PipelineOrchestrator
)

# Silenciar os logs durante os testes para não sujar a consola
logging.getLogger("data_pipeline.modeling").setLevel(logging.CRITICAL)

class TestStatisticalEvaluator(unittest.TestCase):
    """Testes para a classe StatisticalEvaluator"""
    
    def setUp(self):
        self.evaluator = StatisticalEvaluator()

    def test_normality_with_normal_data(self):
        np.random.seed(42)
        normal_data = {
            'group1': np.random.normal(loc=100, scale=5, size=50),
            'group2': np.random.normal(loc=100, scale=5, size=50),
        }
        self.assertTrue(self.evaluator.test_normality(normal_data))

    def test_normality_with_non_normal_data(self):
        np.random.seed(42)
        non_normal_data = {
            'group1': np.random.exponential(scale=2, size=50),
            'group2': np.random.exponential(scale=2, size=50),
        }
        self.assertFalse(self.evaluator.test_normality(non_normal_data))
        
    def test_normality_zero_variance(self):
        """Testa a quebra de variância zero no Shapiro-Wilk"""
        zero_var_data = {'g1': np.ones(50), 'g2': np.ones(50)}
        self.assertFalse(self.evaluator.test_normality(zero_var_data))

    def test_select_best_dataset_by_rmse_anova(self):
        # Dados perfeitos (normais) forçam o caminho do ANOVA
        results_dict = {
            'full': {'rmse': np.random.normal(100, 1, 30), 'r2': [0.9] * 30, 'mae': [80.0] * 30},
            'selected': {'rmse': np.random.normal(150, 1, 30), 'r2': [0.85] * 30, 'mae': [120.0] * 30},
        }
        best_ds, metrics = self.evaluator.select_best_dataset(results_dict)
        self.assertEqual(best_ds, 'full')

    def test_select_best_dataset_friedman(self):
        """Força o caminho do Friedman Test com dados não-normais e arrays maiores"""
        results_dict = {
            'ds1': {'rmse': np.random.exponential(100, 30), 'r2': [0.8] * 30, 'mae': [50.0] * 30},
            'ds2': {'rmse': np.random.exponential(10, 30), 'r2': [0.9] * 30, 'mae': [5.0] * 30}, 
        }
        best_ds, _ = self.evaluator.select_best_dataset(results_dict)
        self.assertEqual(best_ds, 'ds2') # Deve ganhar o ds2 com menor RMSE exponencial

    def test_select_best_strategy_kruskal(self):
        """Força o caminho do Kruskal-Wallis com dados não-normais"""
        strategy_results = {
            'fixed': {'metrics': {'rmse': np.random.exponential(100, 30), 'r2': [0.8]*30, 'mae': [50]*30}},
            'expanding': {'metrics': {'rmse': np.random.exponential(10, 30), 'r2': [0.9]*30, 'mae': [5]*30}},
        }
        best_strat = self.evaluator.select_best_strategy(strategy_results)
        self.assertEqual(best_strat, 'expanding')

class TestModelManager(unittest.TestCase):
    """Testes para a classe ModelManager"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ModelManager() 
        dates = pd.date_range(start='2018-01-01', end='2024-12-31', freq='D')
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
            'feature1': np.random.normal(loc=0, scale=1, size=len(dates)),
        })

    def test_generate_splits_temporal_order(self):
        for strat in ["fixed_rolling", "expanding"]:
            splits = self.manager.generate_splits(self.test_data, strategy=strat)
            self.assertTrue(len(splits) > 0)
            for train_idx, test_idx in splits:
                self.assertTrue(max(train_idx) < min(test_idx))
                self.assertEqual(len(set(train_idx) & set(test_idx)), 0)

    def test_generate_splits_edge_case_insufficient_data(self):
        dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='D')
        small_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(2000, 300, len(dates)),
        })
        splits = self.manager.generate_splits(small_data)
        self.assertEqual(len(splits), 0)

    def test_train_baseline_valid_data(self):
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feat{i}' for i in range(5)])
        y = pd.Series(np.random.randn(100))
        model = self.manager.train_baseline(X, y)
        self.assertIsNotNone(model)

    @patch('data_pipeline.modeling.optuna.create_study')
    def test_train_flexible_mocked_optuna(self, mock_create_study):
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 20, 'max_depth': 5}
        mock_create_study.return_value = mock_study
        
        X_train = self.test_data[['datetime', 'feature1']].copy()
        y_train = self.test_data['Load_MW'].copy()
        
        model = self.manager.train_flexible(X_train, y_train, strategy="expanding")
        self.assertIsNotNone(model)
        
    @patch('data_pipeline.modeling.optuna.create_study')
    def test_train_flexible_fallback_small_data(self, mock_create_study):
        """Testa o fallback quando os dados não chegam para o gap temporal de 2 anos"""
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 10, 'max_depth': 3}
        mock_create_study.return_value = mock_study
        
        dates = pd.date_range(start='2023-01-01', end='2023-06-01', freq='D')
        small_data = pd.DataFrame({'datetime': dates, 'Load_MW': range(len(dates)), 'feat1': range(len(dates))})
        
        model = self.manager.train_flexible(small_data[['datetime', 'feat1']], small_data['Load_MW'], strategy="expanding")
        self.assertIsNotNone(model)

    @patch('data_pipeline.modeling.optuna.create_study')
    def test_train_flexible_nested_strategy(self, mock_create_study):
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 10, 'max_depth': 3}
        mock_create_study.return_value = mock_study
        
        X_train = self.test_data[['datetime', 'feature1']].copy()
        y_train = self.test_data['Load_MW'].copy()
        
        model = self.manager.train_flexible(X_train, y_train, strategy="nested")
        self.assertIsNotNone(model)

    @patch('data_pipeline.modeling.Path.exists')
    @patch('data_pipeline.modeling.pd.read_csv')
    def test_load_all_datasets(self, mock_read_csv, mock_exists):
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame({'datetime': ['2023-01-01'], 'val': [1]})
        
        datasets = self.manager.load_all_datasets()
        self.assertIn('full', datasets)

    def test_get_next_version(self):
        """Testa o versionamento em memória criando ficheiros dummy localmente no temp_dir"""
        self.manager.models_dir = Path(self.temp_dir)
        (self.manager.models_dir / "LR_v1.joblib").touch()
        (self.manager.models_dir / "LR_v3.joblib").touch()
        
        next_v = self.manager._get_next_version("LR")
        self.assertEqual(next_v, 4)

class TestDatabaseManager(unittest.TestCase):
    """Testes dedicados à integração com a Base de Dados"""
    
    @patch('data_pipeline.modeling.psycopg2.connect')
    def test_save_model_metrics_success(self, mock_connect):
        db_config = {"dbname": "test_db", "user": "test"}
        manager = DatabaseManager(db_config)
        
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        manager.save_model_metrics("RF", "models/hourly/RF_v1.joblib", 10.5, 5.2, 0.95)
        self.assertTrue(mock_cursor.execute.called)

    def test_save_model_metrics_no_config(self):
        manager = DatabaseManager(None)
        manager.save_model_metrics("RF", "path", 1.0, 1.0, 1.0) 

    @patch('data_pipeline.modeling.psycopg2.connect')
    def test_save_model_metrics_exception(self, mock_connect):
        db_config = {"dbname": "test_db"}
        manager = DatabaseManager(db_config)
        mock_connect.side_effect = Exception("Database is down!")
        
        try:
            manager.save_model_metrics("RF", "path", 1.0, 1.0, 1.0)
            failed = False
        except Exception:
            failed = True
            
        self.assertFalse(failed, "A exceção da BD não foi apanhada!")

from pathlib import Path

class TestPipelineOrchestrator(unittest.TestCase):
    """Testa a nova classe de orquestração do pipeline completo"""

    def setUp(self):
        self.orchestrator = PipelineOrchestrator(db_config=None)

    def test_find_best_fold_index(self):
        vencedora_metrics = {
            'rmse': [15.0, 10.0, 10.0, 12.0],
            'r2':   [0.80, 0.90, 0.90, 0.85],
            'mae':  [8.0,  5.0,  4.0,  6.0] 
        }
        best_idx = self.orchestrator._find_best_fold_index(vencedora_metrics)
        self.assertEqual(best_idx, 2)

    def test_precalculate_splits(self):
        """Testa o pré-cálculo dos splits de todas as estratégias"""
        dates = pd.date_range('2018-01-01', end='2024-01-01', freq='M') 
        df = pd.DataFrame({'datetime': dates, 'Load_MW': np.random.rand(len(dates))})
        
        # Injeta um ModelManager falso no orquestrador
        self.orchestrator.manager = ModelManager("hourly")
        splits = self.orchestrator._precalculate_splits({'full': df})
        
        self.assertIn('expanding', splits)