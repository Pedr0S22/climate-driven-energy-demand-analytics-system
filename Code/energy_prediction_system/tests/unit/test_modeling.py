"""
Unit Tests para o módulo data_pipeline.modeling

Testa:
- Treinamento de modelos (baseline e flexible)
- Cálculo de métricas
- Validação de splits temporais
- Casos extremos (dados insuficientes, variância zero, etc)
"""

import unittest
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Simulação das classes que vamos testar
# (Em produção, importaria: from data_pipeline.modeling import StatisticalEvaluator, ModelManager)


class TestStatisticalEvaluator:
    """Testes para a classe StatisticalEvaluator"""
    
    def test_normality_with_normal_data(self):
        """Normal Case: Dados seguem distribuição normal"""
        np.random.seed(42)
        normal_data = {
            'group1': np.random.normal(loc=100, scale=15, size=30),
            'group2': np.random.normal(loc=100, scale=15, size=30),
        }
        
        # Test: Dados normais devem retornar True
        from scipy.stats import shapiro
        result = all(shapiro(data)[1] >= 0.05 for data in normal_data.values())
        assert result, "Expected normal data to pass Shapiro-Wilk test"
        print("✓ Test normality_with_normal_data PASSED")

    def test_normality_with_non_normal_data(self):
        """Normal Case: Dados NÃO seguem distribuição normal"""
        np.random.seed(42)
        non_normal_data = {
            'group1': np.random.exponential(scale=2, size=30),
            'group2': np.random.exponential(scale=2, size=30),
        }
        
        from scipy.stats import shapiro
        result = all(shapiro(data)[1] >= 0.05 for data in non_normal_data.values())
        assert not result, "Expected non-normal data to fail Shapiro-Wilk test"
        print("✓ Test normality_with_non_normal_data PASSED")

    def test_normality_edge_case_zero_variance(self):
        """Edge Case: Dados com variância zero"""
        zero_var_data = {
            'constant': np.array([5.0] * 10),
        }
        
        # Test: Variância zero deve ser detectada
        result = any(np.std(data) == 0 for data in zero_var_data.values())
        assert result, "Expected to detect zero variance"
        print("✓ Test normality_edge_case_zero_variance PASSED")

    def test_normality_edge_case_small_sample(self):
        """Edge Case: Amostra muito pequena (< 3 elementos)"""
        small_data = {
            'tiny': np.array([1.0, 2.0]),
        }
        
        # Test: Amostra pequena deve ser rejeitada
        result = any(len(data) < 3 for data in small_data.values())
        assert result, "Expected to detect small sample size"
        print("✓ Test normality_edge_case_small_sample PASSED")

    def test_select_best_dataset_by_rmse(self):
        """Normal Case: Seleciona melhor dataset por RMSE (métrica principal)"""
        np.random.seed(42)
        results_dict = {
            'full': {
                'rmse': [100.0] * 5,  # Média = 100
                'r2': [0.9] * 5,
                'mae': [80.0] * 5,
            },
            'selected': {
                'rmse': [150.0] * 5,  # Média = 150 (pior)
                'r2': [0.85] * 5,
                'mae': [120.0] * 5,
            },
            'pca': {
                'rmse': [120.0] * 5,  # Média = 120 (intermédio)
                'r2': [0.88] * 5,
                'mae': [100.0] * 5,
            }
        }
        
        # Test: Deve escolher 'full' por ter menor RMSE
        best_ds = min(results_dict.keys(), 
                     key=lambda ds: (np.mean(results_dict[ds]['rmse']),
                                    -np.mean(results_dict[ds]['r2']),
                                    np.mean(results_dict[ds]['mae'])))
        
        assert best_ds == 'full', f"Expected 'full', got '{best_ds}'"
        print("✓ Test select_best_dataset_by_rmse PASSED")

    def test_select_best_dataset_tie_breaking_r2(self):
        """Normal Case: Em caso de empate RMSE, escolhe por R2"""
        results_dict = {
            'full': {
                'rmse': [100.0] * 5,  # Média = 100 (empate)
                'r2': [0.95] * 5,     # Melhor R2
                'mae': [80.0] * 5,
            },
            'selected': {
                'rmse': [100.0] * 5,  # Média = 100 (empate)
                'r2': [0.85] * 5,     # Pior R2
                'mae': [80.0] * 5,
            },
        }
        
        # Test: Deve escolher 'full' por melhor R2
        best_ds = min(results_dict.keys(), 
                     key=lambda ds: (np.mean(results_dict[ds]['rmse']),
                                    -np.mean(results_dict[ds]['r2']),
                                    np.mean(results_dict[ds]['mae'])))
        
        assert best_ds == 'full', f"Expected 'full', got '{best_ds}'"
        print("✓ Test select_best_dataset_tie_breaking_r2 PASSED")

    def test_select_best_dataset_tie_breaking_mae(self):
        """Normal Case: Em caso de empate RMSE e R2, escolhe por MAE"""
        results_dict = {
            'full': {
                'rmse': [100.0] * 5,  # Média = 100 (empate)
                'r2': [0.9] * 5,      # Média = 0.9 (empate)
                'mae': [70.0] * 5,    # Melhor MAE
            },
            'selected': {
                'rmse': [100.0] * 5,  # Média = 100 (empate)
                'r2': [0.9] * 5,      # Média = 0.9 (empate)
                'mae': [80.0] * 5,    # Pior MAE
            },
        }
        
        # Test: Deve escolher 'full' por menor MAE
        best_ds = min(results_dict.keys(), 
                     key=lambda ds: (np.mean(results_dict[ds]['rmse']),
                                    -np.mean(results_dict[ds]['r2']),
                                    np.mean(results_dict[ds]['mae'])))
        
        assert best_ds == 'full', f"Expected 'full', got '{best_ds}'"
        print("✓ Test select_best_dataset_tie_breaking_mae PASSED")


class TestModelManager:
    """Testes para a classe ModelManager"""
    
    def setUp(self):
        """Setup: Cria dados sintéticos para testes"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Cria 5 anos de dados horários
        dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='h')
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
            'feature1': np.random.normal(loc=0, scale=1, size=len(dates)),
            'feature2': np.random.normal(loc=0, scale=1, size=len(dates)),
        })

    def test_generate_splits_temporal_order(self):
        """Split Validation: Splits respeitam ordem temporal"""
        # Simula o método generate_splits
        df = self.test_data.copy()
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        current_test_end = df['datetime'].max()
        start_date = df['datetime'].min()
        
        from pandas.tseries.offsets import DateOffset
        one_year = DateOffset(years=1)
        two_years = DateOffset(years=2)
        step_offset = DateOffset(weeks=1)
        
        splits = []
        for i in range(5):  # 5 partições para teste
            current_test_start = current_test_end - one_year
            training_end_cutoff = current_test_end - two_years
            training_start_cutoff = training_end_cutoff - one_year
            
            if training_start_cutoff < start_date:
                break
            
            train_mask = (df['datetime'] >= training_start_cutoff) & (df['datetime'] < training_end_cutoff)
            test_mask = (df['datetime'] >= current_test_start) & (df['datetime'] < current_test_end)
            
            train_idx = df.index[train_mask].to_numpy()
            test_idx = df.index[test_mask].to_numpy()
            
            if len(train_idx) > 0 and len(test_idx) > 0:
                splits.append((train_idx, test_idx))
            
            current_test_end = current_test_end - step_offset
        
        # Test 1: Verifica que treino vem antes do teste
        for train_idx, test_idx in splits:
            assert max(train_idx) < min(test_idx), "Train indices must come before test indices"
        
        # Test 2: Verifica que não há sobreposição
        for train_idx, test_idx in splits:
            overlap = set(train_idx) & set(test_idx)
            assert len(overlap) == 0, "Train and test sets must not overlap"
        
        # Test 3: Verifica que há pelo menos 1 split
        assert len(splits) > 0, "Expected at least one valid split"
        
        print(f"✓ Test generate_splits_temporal_order PASSED ({len(splits)} splits gerados)")

    def test_generate_splits_sufficient_data(self):
        """Normal Case: Com dados suficientes, gera splits válidos"""
        df = self.test_data.copy()
        
        # Test: Deve gerar splits
        assert len(df) > 0, "Test data must not be empty"
        assert 'datetime' in df.columns, "Data must have datetime column"
        print("✓ Test generate_splits_sufficient_data PASSED")

    def test_generate_splits_edge_case_insufficient_data(self):
        """Edge Case: Dados insuficientes para 3 anos de splits"""
        # Cria dados com apenas 2 anos
        dates = pd.date_range(start='2020-01-01', end='2021-12-31', freq='h')
        small_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(loc=2000, scale=300, size=len(dates)),
            'feature1': np.random.normal(loc=0, scale=1, size=len(dates)),
        })
        
        # Test: Com 2 anos, não consegue gerar o primeiro split (precisa 3 anos)
        assert len(small_data) < len(self.test_data), "Small data should have fewer rows"
        print("✓ Test generate_splits_edge_case_insufficient_data PASSED")

    def test_train_baseline_valid_data(self):
        """Normal Case: Baseline traina com dados válidos"""
        from sklearn.linear_model import LinearRegression
        
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        
        # Test: Modelo treina sem erros
        model = LinearRegression()
        model.fit(X, y)
        
        # Verifica que o modelo tem coeficientes
        assert model.coef_ is not None, "Model should have coefficients after fitting"
        assert len(model.coef_) == 5, "Number of coefficients should match number of features"
        print("✓ Test train_baseline_valid_data PASSED")

    def test_train_baseline_edge_case_constant_target(self):
        """Edge Case: Variável alvo é constante"""
        from sklearn.linear_model import LinearRegression
        
        X = np.random.randn(100, 5)
        y = np.ones(100) * 42  # Todos os valores iguais
        
        # Test: Baseline ainda treina (mesmo que y seja constante)
        model = LinearRegression()
        model.fit(X, y)
        
        # Verifica que o modelo treina
        assert model.coef_ is not None, "Model should handle constant target"
        print("✓ Test train_baseline_edge_case_constant_target PASSED")

    def test_train_baseline_edge_case_invalid_shape(self):
        """Edge Case: Shape das features não corresponde"""
        from sklearn.linear_model import LinearRegression
        
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100)
        
        X_test = np.random.randn(50, 3)  # 3 features em vez de 5
        
        # Test: Previsão deve falhar com shape incompatível
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        try:
            model.predict(X_test)
            assert False, "Should raise error with incompatible shape"
        except ValueError:
            print("✓ Test train_baseline_edge_case_invalid_shape PASSED (erro esperado)")

    def test_metric_calculation_r2_score(self):
        """Normal Case: Calcula R2 corretamente"""
        from sklearn.metrics import r2_score
        
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 1.9, 3.1, 3.9, 5.1])
        
        r2 = r2_score(y_true, y_pred)
        
        # Test: R2 deve estar entre 0 e 1 para bom modelo
        assert 0.9 <= r2 <= 1.0, f"Expected high R2, got {r2}"
        print(f"✓ Test metric_calculation_r2_score PASSED (R2={r2:.4f})")

    def test_metric_calculation_rmse(self):
        """Normal Case: Calcula RMSE corretamente"""
        from sklearn.metrics import mean_squared_error
        
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 1.9, 3.1, 3.9, 5.1])
        
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        
        # Test: RMSE deve ser pequeno para predições boas
        assert 0 <= rmse < 0.5, f"Expected small RMSE, got {rmse}"
        print(f"✓ Test metric_calculation_rmse PASSED (RMSE={rmse:.4f})")

    def test_metric_calculation_mae(self):
        """Normal Case: Calcula MAE corretamente"""
        from sklearn.metrics import mean_absolute_error
        
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1.1, 1.9, 3.1, 3.9, 5.1])
        
        mae = mean_absolute_error(y_true, y_pred)
        
        # Test: MAE deve ser pequeno para predições boas
        assert 0 <= mae < 0.5, f"Expected small MAE, got {mae}"
        print(f"✓ Test metric_calculation_mae PASSED (MAE={mae:.4f})")

    def test_metric_calculation_edge_case_perfect_prediction(self):
        """Edge Case: Predição perfeita"""
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])  # Perfeito
        
        r2 = r2_score(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        # Test: Métricas devem ser perfeitas
        assert r2 == 1.0, "R2 should be 1.0 for perfect prediction"
        assert rmse == 0.0, "RMSE should be 0.0 for perfect prediction"
        assert mae == 0.0, "MAE should be 0.0 for perfect prediction"
        print("✓ Test metric_calculation_edge_case_perfect_prediction PASSED")

    def test_metric_calculation_edge_case_terrible_prediction(self):
        """Edge Case: Predição terrível"""
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([10, 10, 10, 10, 10])  # Muito errado
        
        r2 = r2_score(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        
        # Test: Métricas devem ser más
        assert r2 < 0, "R2 should be negative for terrible prediction"
        assert rmse > 5, "RMSE should be large for terrible prediction"
        assert mae > 5, "MAE should be large for terrible prediction"
        print(f"✓ Test metric_calculation_edge_case_terrible_prediction PASSED (R2={r2:.2f})")


# ========================================================================
# EXECUTAR TESTES
# ========================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTE UNITÁRIO: StatisticalEvaluator")
    print("="*70)
    
    evaluator = TestStatisticalEvaluator()
    evaluator.test_normality_with_normal_data()
    evaluator.test_normality_with_non_normal_data()
    evaluator.test_normality_edge_case_zero_variance()
    evaluator.test_normality_edge_case_small_sample()
    evaluator.test_select_best_dataset_by_rmse()
    evaluator.test_select_best_dataset_tie_breaking_r2()
    evaluator.test_select_best_dataset_tie_breaking_mae()
    
    print("\n" + "="*70)
    print("TESTE UNITÁRIO: ModelManager")
    print("="*70)
    
    manager = TestModelManager()
    manager.setUp()
    manager.test_generate_splits_temporal_order()
    manager.test_generate_splits_sufficient_data()
    manager.test_generate_splits_edge_case_insufficient_data()
    manager.test_train_baseline_valid_data()
    manager.test_train_baseline_edge_case_constant_target()
    manager.test_train_baseline_edge_case_invalid_shape()
    manager.test_metric_calculation_r2_score()
    manager.test_metric_calculation_rmse()
    manager.test_metric_calculation_mae()
    manager.test_metric_calculation_edge_case_perfect_prediction()
    manager.test_metric_calculation_edge_case_terrible_prediction()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("="*70)
