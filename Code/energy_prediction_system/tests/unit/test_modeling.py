"""
Unit Tests para o módulo data_pipeline.modeling
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import tempfile

# IMPORTANTE: Garante que o caminho de importação reflete a estrutura do teu projeto.
# Se der erro, experimenta "from data_pipeline.modeling import ..."
from data_pipeline.modeling import StatisticalEvaluator, ModelManager

class TestStatisticalEvaluator(unittest.TestCase):
    """Testes para a classe StatisticalEvaluator"""
    
    def setUp(self):
        # Instancia a classe real antes de cada teste
        self.evaluator = StatisticalEvaluator()

    def test_normality_with_normal_data(self):
        np.random.seed(42)
        normal_data = {
            'group1': np.random.normal(loc=100, scale=5, size=50),
            'group2': np.random.normal(loc=100, scale=5, size=50),
        }
        
        # Chama o método test_normality real
        result = self.evaluator.test_normality(normal_data)
        self.assertTrue(result, "Expected normal data to pass Shapiro-Wilk test")

    def test_normality_with_non_normal_data(self):
        np.random.seed(42)
        non_normal_data = {
            'group1': np.random.exponential(scale=2, size=50),
            'group2': np.random.exponential(scale=2, size=50),
        }
        
        result = self.evaluator.test_normality(non_normal_data)
        self.assertFalse(result, "Expected non-normal data to fail Shapiro-Wilk test")

    def test_select_best_dataset_by_rmse(self):
        # 3 Datasets fornecidos para evitar o ValueError do Friedman Test
        results_dict = {
            'full': {'rmse': [100.0] * 5, 'r2': [0.9] * 5, 'mae': [80.0] * 5},
            'selected': {'rmse': [150.0] * 5, 'r2': [0.85] * 5, 'mae': [120.0] * 5},
            'pca': {'rmse': [120.0] * 5, 'r2': [0.88] * 5, 'mae': [100.0] * 5},
        }
        
        # A função devolve um tuplo: best_ds, best_metrics
        best_ds, metrics = self.evaluator.select_best_dataset(results_dict)
        self.assertEqual(best_ds, 'full')
        self.assertEqual(metrics['rmse'], 100.0)

    def test_select_best_strategy(self):
        # Testa a seleção da melhor estratégia
        strategy_results = {
            'fixed_rolling': {'metrics': {'rmse': [100.0] * 5, 'r2': [0.9] * 5, 'mae': [80.0] * 5}},
            'expanding': {'metrics': {'rmse': [150.0] * 5, 'r2': [0.8] * 5, 'mae': [100.0] * 5}},
            'nested': {'metrics': {'rmse': [120.0] * 5, 'r2': [0.85] * 5, 'mae': [90.0] * 5}},
        }
        best_strat = self.evaluator.select_best_strategy(strategy_results)
        self.assertEqual(best_strat, 'fixed_rolling')

    def test_select_best_dataset_tie_breakers(self):
        """Testa o desempate: RMSE igual, ganha R2. Se R2 igual, ganha MAE."""
        results_dict = {
            'ds1': {'rmse': [100.0], 'r2': [0.80], 'mae': [50.0]},
            'ds2': {'rmse': [100.0], 'r2': [0.90], 'mae': [60.0]}, # Ganha no R2
            'ds3': {'rmse': [100.0], 'r2': [0.90], 'mae': [40.0]}, # Empata R2, ganha no MAE
        }
        best_ds, _ = self.evaluator.select_best_dataset(results_dict)
        self.assertEqual(best_ds, 'ds3')
        
        # Fazer o mesmo para a estratégia
        strategy_results = {
            'strat1': {'metrics': {'rmse': [100.0], 'r2': [0.8], 'mae': [50.0]}},
            'strat2': {'metrics': {'rmse': [100.0], 'r2': [0.9], 'mae': [40.0]}},
        }
        best_strat = self.evaluator.select_best_strategy(strategy_results)
        self.assertEqual(best_strat, 'strat2')

    @patch('data_pipeline.modeling.Path.exists')
    @patch('data_pipeline.modeling.pd.read_csv')
    def test_load_all_datasets(self, mock_read_csv, mock_exists):
        """Testa o carregamento de datasets simulando o disco."""
        mock_exists.return_value = True
        mock_read_csv.return_value = pd.DataFrame({'datetime': ['2023-01-01'], 'val': [1]})
        
        datasets = self.manager.load_all_datasets()
        self.assertIn('full', datasets)
        self.assertIn('pca', datasets)

    def test_get_next_version(self):
        """Testa o versionamento (ex: LR_v1.joblib -> LR_v2.joblib)"""
        with patch.object(self.manager.models_dir, 'glob') as mock_glob:
            # Simula que já existem a versão 1 e 3
            mock_file1, mock_file3 = MagicMock(), MagicMock()
            mock_file1.name = "LR_v1.joblib"
            mock_file3.name = "LR_v3.joblib"
            mock_glob.return_value = [mock_file1, mock_file3]
            
            # A próxima versão deve ser a 4
            next_v = self.manager._get_next_version("LR")
            self.assertEqual(next_v, 4)

    @patch('data_pipeline.modeling.optuna.create_study')
    def test_train_flexible_nested_strategy(self, mock_create_study):
        """Força a execução da lógica interna de validação cruzada do Nested."""
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 10, 'max_depth': 3}
        mock_create_study.return_value = mock_study
        
        X_train = self.test_data[['datetime', 'feature1']].copy()
        y_train = self.test_data['Load_MW'].copy()
        
        # Testar a estratégia nested
        model = self.manager.train_flexible(X_train, y_train, strategy="nested")
        self.assertIsNotNone(model)


class TestModelManager(unittest.TestCase):
    """Testes para a classe ModelManager"""
    
    def setUp(self):
        """Setup: Cria dados sintéticos e a instância do manager"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ModelManager() 
        
        dates = pd.date_range(start='2018-01-01', end='2024-12-31', freq='D')
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
            'feature1': np.random.normal(loc=0, scale=1, size=len(dates)),
        })

    def test_generate_splits_temporal_order(self):
        """Testa se o teu método real gera splits corretamente"""
        splits = self.manager.generate_splits(self.test_data, strategy="fixed_rolling")
        
        self.assertTrue(len(splits) > 0, "Expected at least one valid split")
        
        for train_idx, test_idx in splits:
            # O índice máximo de treino tem de ser menor que o mínimo de teste
            self.assertTrue(max(train_idx) < min(test_idx), "Train must come before test")
            # Não podem existir dados sobrepostos
            overlap = set(train_idx) & set(test_idx)
            self.assertEqual(len(overlap), 0, "Train and test sets must not overlap")

    def test_generate_splits_edge_case_insufficient_data(self):
        """Testa como o teu código reage a dados insuficientes (menos de 3 anos)"""
        dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='D')
        small_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
        })
        
        splits = self.manager.generate_splits(small_data)
        self.assertEqual(len(splits), 0, "Should not generate splits with insufficient data")

    def test_train_baseline_valid_data(self):
        """Testa o teu método de treino do baseline (Linear Regression)"""
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feat{i}' for i in range(5)])
        y = pd.Series(np.random.randn(100))
        
        model = self.manager.train_baseline(X, y)
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'predict'))

    @patch('data_pipeline.modeling.optuna.create_study')
    def test_train_flexible_mocked_optuna(self, mock_create_study):
        """Testa o RandomForest sem executar 30 trials do Optuna (simulado)"""
        # Configuramos o Mock para "enganar" o Optuna e devolver logo os melhores parâmetros
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 20, 'max_depth': 5}
        mock_create_study.return_value = mock_study
        
        # O train_flexible exige a coluna 'datetime' para calcular os gaps
        X_train = self.test_data[['datetime', 'feature1']].copy()
        y_train = self.test_data['Load_MW'].copy()
        
        model = self.manager.train_flexible(X_train, y_train, strategy="expanding")
        
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'predict'))
        # Garante que a simulação foi chamada
        mock_create_study.assert_called_once()
    
    @patch('data_pipeline.modeling.joblib.dump')
    @patch('data_pipeline.modeling.ModelManager.load_all_datasets')
    @patch('data_pipeline.modeling.ModelManager.train_flexible')
    def test_run_evaluation_pipeline_mocked(self, mock_train_flex, mock_load, mock_dump):
        from data_pipeline.modeling import run_evaluation_pipeline
        
        # Cria um dataset miniatura para a pipeline não demorar tempo a processar
        dates = pd.date_range('2018-01-01', end='2024-01-01', freq='W') # Semanal para ser leve
        df = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.rand(len(dates)),
            'Load_MWh': np.random.rand(len(dates)), # Necessário para freq="daily"
            'feat1': np.random.rand(len(dates))
        })
        
        # Diz ao ModelManager para carregar apenas este dataset pequenino
        mock_load.return_value = {'full': df}
        
        # Finge o modelo "flexible" para não perdermos tempo a treinar Random Forests aqui
        mock_rf = MagicMock()
        mock_rf.predict.side_effect = lambda X: np.zeros(len(X)) # Previsões dummy
        mock_train_flex.return_value = mock_rf
        
        # Executa a pipeline
        try:
            run_evaluation_pipeline()
            pipeline_ran = True
        except Exception as e:
            pipeline_ran = False
            print(f"Pipeline falhou: {e}")
            
        # Verifica se passou sem quebrar e se guardou ficheiros (Regra 8)
        self.assertTrue(pipeline_ran)
        self.assertTrue(mock_dump.called, "A pipeline não guardou nenhum modelo no disco.")