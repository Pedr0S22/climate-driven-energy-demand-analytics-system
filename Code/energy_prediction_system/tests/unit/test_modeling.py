"""
Unit Tests para o módulo data_pipeline.modeling
"""

import unittest
import numpy as np
import pandas as pd
import tempfile

# IMPORTANTE: Estamos a importar as tuas classes REAIS para as testar
from data_pipeline.modeling import StatisticalEvaluator, ModelManager

class TestStatisticalEvaluator(unittest.TestCase):
    """Testes para a classe StatisticalEvaluator"""
    
    def setUp(self):
        # Instancia a classe real antes de cada teste
        self.evaluator = StatisticalEvaluator()

    def test_normality_with_normal_data(self):
        np.random.seed(42)
        normal_data = {
            'group1': np.random.normal(loc=100, scale=15, size=30),
            'group2': np.random.normal(loc=100, scale=15, size=30),
        }
        
        # Chama o TEU método real (ajusta o nome 'check_normality' se necessário)
        result = self.evaluator.check_normality(normal_data)
        self.assertTrue(result, "Expected normal data to pass Shapiro-Wilk test")

    def test_normality_with_non_normal_data(self):
        np.random.seed(42)
        non_normal_data = {
            'group1': np.random.exponential(scale=2, size=30),
            'group2': np.random.exponential(scale=2, size=30),
        }
        
        result = self.evaluator.check_normality(non_normal_data)
        self.assertFalse(result, "Expected non-normal data to fail Shapiro-Wilk test")

    def test_select_best_dataset_by_rmse(self):
        results_dict = {
            'full': {'rmse': [100.0] * 5, 'r2': [0.9] * 5, 'mae': [80.0] * 5},
            'selected': {'rmse': [150.0] * 5, 'r2': [0.85] * 5, 'mae': [120.0] * 5},
        }
        
        # Chama o TEU método real (ajusta o nome 'select_best_dataset' se necessário)
        best_ds = self.evaluator.select_best_dataset(results_dict)
        self.assertEqual(best_ds, 'full')


class TestModelManager(unittest.TestCase):
    """Testes para a classe ModelManager"""
    
    def setUp(self):
        """Setup: Cria dados sintéticos e a instância do manager"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ModelManager() # Instancia a tua classe real
        
        dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='h')
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
            'feature1': np.random.normal(loc=0, scale=1, size=len(dates)),
        })

    def test_generate_splits_temporal_order(self):
        """Testa se o teu método real gera splits corretamente"""
        # Chama o TEU método real em vez de simular a lógica de split
        splits = self.manager.generate_splits(self.test_data)
        
        self.assertTrue(len(splits) > 0, "Expected at least one valid split")
        
        for train_idx, test_idx in splits:
            self.assertTrue(max(train_idx) < min(test_idx), "Train must come before test")
            overlap = set(train_idx) & set(test_idx)
            self.assertEqual(len(overlap), 0, "Train and test sets must not overlap")

    def test_generate_splits_edge_case_insufficient_data(self):
        """Testa como o teu código reage a dados pequenos"""
        dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='h')
        small_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
        })
        
        # Verifica se o método lida bem com poucos dados (pode retornar lista vazia)
        splits = self.manager.generate_splits(small_data)
        self.assertEqual(len(splits), 0, "Should not generate splits with insufficient data")

    def test_train_baseline_valid_data(self):
        """Testa o teu método de treino de baseline"""
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        
        # Chama o TEU método real
        model = self.manager.train_baseline(X, y)
        self.assertIsNotNone(model)

    def test_metric_calculation(self):
        """Testa o teu método de calcular métricas"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 1.9, 3.1, 3.9, 5.1])
        
        # Chama o TEU método real que calcula as métricas (ajusta o nome)
        metrics = self.manager.calculate_metrics(y_true, y_pred)
        
        self.assertIn('r2', metrics)
        self.assertIn('rmse', metrics)
        self.assertTrue(0.9 <= metrics['r2'] <= 1.0)
        self.assertTrue(0 <= metrics['rmse'] < 0.5)