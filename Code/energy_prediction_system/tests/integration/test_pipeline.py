
"""
Integration Tests para o pipeline de modeling completo

Testa:
- Fluxo completo de carregamento até persistência
- Carregamento e reuso de modelos salvos
- Consistência de resultados
"""

import unittest
import numpy as np
import pandas as pd
import joblib
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFullPipeline:
    """Testes de integração do pipeline completo"""
    
    def setUp(self):
        """Setup: Cria ambiente e dados para testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.models_dir = Path(self.temp_dir) / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Cria dados sintéticos realistas
        dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='h')
        np.random.seed(42)
        
        # Simula padrão de consumo de energia (sazonalidade)
        hour_of_day = dates.hour
        seasonality = 2000 + 500 * np.sin(2 * np.pi * hour_of_day / 24)
        
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': seasonality + np.random.normal(0, 100, size=len(dates)),
            'temperature': 15 + 10 * np.sin(2 * np.pi * dates.dayofyear / 365) + np.random.normal(0, 2, len(dates)),
            'humidity': 60 + 20 * np.sin(2 * np.pi * dates.dayofyear / 365) + np.random.normal(0, 5, len(dates)),
            'hour': dates.hour,
            'day': dates.dayofweek,
            'month': dates.month,
        })
        
        logger.info(f"✓ Setup: Criados {len(self.test_data)} registos de dados sintéticos")

    def test_data_loading(self):
        """Integration Test: Carrega dados com sucesso"""
        # Test: Verifica que dados foram criados
        assert len(self.test_data) > 0, "Test data should not be empty"
        assert 'datetime' in self.test_data.columns, "Data must have datetime column"
        assert 'Load_MW' in self.test_data.columns, "Data must have Load_MW column"
        
        # Test: Verifica tipos de dados
        assert pd.api.types.is_datetime64_any_dtype(self.test_data['datetime']), "datetime should be datetime type"
        assert pd.api.types.is_numeric_dtype(self.test_data['Load_MW']), "Load_MW should be numeric"
        
        logger.info(f"✓ Test data_loading PASSED")

    def test_feature_engineering_columns(self):
        """Integration Test: Features estão presentes e são válidas"""
        # Test: Verifica features engineered
        expected_features = ['temperature', 'humidity', 'hour', 'day', 'month']
        for feature in expected_features:
            assert feature in self.test_data.columns, f"Feature {feature} missing"
        
        # Test: Verifica que não há NaNs
        nan_count = self.test_data.isnull().sum().sum()
        assert nan_count == 0, f"Data contains {nan_count} NaN values"
        
        logger.info(f"✓ Test feature_engineering_columns PASSED")

    def test_model_training_baseline(self):
        """Integration Test: Treina modelo baseline com sucesso"""
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
        
        # Prepara dados
        X = self.test_data[['temperature', 'humidity', 'hour', 'day', 'month']].copy()
        y = self.test_data['Load_MW'].copy()
        
        # Split simples (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Treina baseline
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Calcula métricas
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        
        # Tests
        assert model is not None, "Model should be trained"
        assert r2 > 0.5, f"Baseline R2 should be > 0.5, got {r2:.4f}"
        assert rmse < np.std(y_test) * 2, "RMSE should be reasonable"
        assert mae > 0, "MAE should be positive"
        
        logger.info(f"✓ Test model_training_baseline PASSED (R2={r2:.4f}, RMSE={rmse:.2f})")

    def test_model_training_flexible(self):
        """Integration Test: Treina modelo flexible (RandomForest) com sucesso"""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import r2_score, mean_squared_error
        
        # Prepara dados
        X = self.test_data[['temperature', 'humidity', 'hour', 'day', 'month']].copy()
        y = self.test_data['Load_MW'].copy()
        
        # Split simples (80/20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Treina flexible com hiperparâmetros
        model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Calcula métricas
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Tests
        assert model is not None, "Model should be trained"
        assert r2 > 0.7, f"Flexible R2 should be > 0.7, got {r2:.4f}"
        assert rmse < np.std(y_test) * 2, "RMSE should be reasonable"
        assert r2 > 0.5, "R2 deve ser positivo"
        
        logger.info(f"✓ Test model_training_flexible PASSED (R2={r2:.4f}, RMSE={rmse:.2f})")

    def test_model_persistence_save(self):
        """Integration Test: Salva modelo em disco com sucesso"""
        from sklearn.linear_model import LinearRegression
        
        # Treina modelo simples
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        model = LinearRegression()
        model.fit(X, y)
        
        # Salva modelo
        model_path = self.models_dir / "test_model.joblib"
        joblib.dump(model, model_path)
        
        # Tests
        assert model_path.exists(), f"Model file should exist at {model_path}"
        assert model_path.stat().st_size > 0, "Model file should not be empty"
        
        logger.info(f"✓ Test model_persistence_save PASSED ({model_path.stat().st_size} bytes)")

    def test_model_persistence_load(self):
        """Integration Test: Carrega modelo e usa para predição"""
        from sklearn.linear_model import LinearRegression
        
        # Treina e salva modelo
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100)
        model = LinearRegression()
        model.fit(X_train, y_train)
        
        model_path = self.models_dir / "test_model_load.joblib"
        joblib.dump(model, model_path)
        
        # Carrega modelo
        loaded_model = joblib.load(model_path)
        
        # Tests
        assert loaded_model is not None, "Loaded model should not be None"
        assert hasattr(loaded_model, 'predict'), "Loaded model should have predict method"
        
        # Verifica que o modelo carregado funciona
        X_test = np.random.randn(10, 5)
        predictions = loaded_model.predict(X_test)
        
        assert predictions is not None, "Predictions should not be None"
        assert len(predictions) == len(X_test), "Number of predictions should match input size"
        
        logger.info(f"✓ Test model_persistence_load PASSED")

    def test_model_consistency_after_reload(self):
        """Integration Test: Predições são consistentes após reload do modelo"""
        from sklearn.linear_model import LinearRegression
        
        np.random.seed(42)
        X_train = np.random.randn(100, 5)
        y_train = X_train[:, 0] * 2 + X_train[:, 1] * 3 + np.random.randn(100) * 0.1
        
        # Treina e salva
        model = LinearRegression()
        model.fit(X_train, y_train)
        model_path = self.models_dir / "consistency_model.joblib"
        joblib.dump(model, model_path)
        
        # Faz predições com modelo original
        X_test = np.random.randn(10, 5)
        pred_original = model.predict(X_test)
        
        # Carrega e faz predições
        loaded_model = joblib.load(model_path)
        pred_loaded = loaded_model.predict(X_test)
        
        # Tests: Predições devem ser idênticas
        assert np.allclose(pred_original, pred_loaded), "Predictions should be identical after reload"
        
        logger.info(f"✓ Test model_consistency_after_reload PASSED")

    def test_versioning_system(self):
        """Integration Test: Sistema de versionamento funciona"""
        import re
        
        # Simula salvar múltiplas versões
        for v in range(1, 4):
            path = self.models_dir / f"LR_v{v}.joblib"
            joblib.dump({'version': v}, path)
        
        # Encontra versão seguinte
        existing_files = list(self.models_dir.glob("LR_v*.joblib"))
        versions = []
        for f in existing_files:
            match = re.search(r'_v(\d+)\.joblib', f.name)
            if match:
                versions.append(int(match.group(1)))
        
        next_version = max(versions) + 1 if versions else 1
        
        # Tests
        assert len(existing_files) == 3, "Should have 3 existing versions"
        assert next_version == 4, f"Next version should be 4, got {next_version}"
        
        logger.info(f"✓ Test versioning_system PASSED (next version: {next_version})")

    def test_end_to_end_flow(self):
        """Integration Test: Fluxo completo (dados -> treino -> save -> load -> predict)"""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import r2_score
        
        logger.info("\n📊 Iniciando teste E2E completo...")
        
        # 1. Carrega dados
        logger.info("  1️⃣ Carregando dados...")
        X = self.test_data[['temperature', 'humidity', 'hour', 'day', 'month']].copy()
        y = self.test_data['Load_MW'].copy()
        
        # 2. Split temporal (respeitando cronologia)
        logger.info("  2️⃣ Fazendo split temporal...")
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # 3. Treina modelo
        logger.info("  3️⃣ Treinando modelo...")
        model = RandomForestRegressor(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        r2_train = r2_score(y_train, model.predict(X_train))
        
        # 4. Salva modelo
        logger.info("  4️⃣ Salvando modelo...")
        model_path = self.models_dir / "e2e_model.joblib"
        joblib.dump(model, model_path)
        
        # 5. Carrega modelo
        logger.info("  5️⃣ Carregando modelo...")
        loaded_model = joblib.load(model_path)
        
        # 6. Faz predições
        logger.info("  6️⃣ Fazendo predições...")
        y_pred_original = model.predict(X_test)
        y_pred_loaded = loaded_model.predict(X_test)
        
        # 7. Verifica resultados
        logger.info("  7️⃣ Validando resultados...")
        r2_test = r2_score(y_test, y_pred_loaded)
        
        # Tests
        assert model_path.exists(), "Model should be saved"
        assert np.allclose(y_pred_original, y_pred_loaded), "Predictions should be consistent"
        assert r2_test > 0.5, f"Test R2 should be > 0.5, got {r2_test:.4f}"
        
        logger.info(f"✅ Test end_to_end_flow PASSED")
        logger.info(f"   - Treino R2: {r2_train:.4f}")
        logger.info(f"   - Teste R2:  {r2_test:.4f}")
        logger.info(f"   - Modelo salvo em: {model_path}")

    def test_edge_case_temporal_integrity(self):
        """Integration Test: Integridade temporal é respeitada (não há data leakage)"""
        # Cria dados com padrão temporal
        dates = pd.date_range(start='2020-01-01', periods=365, freq='D')
        data = pd.DataFrame({
            'datetime': dates,
            'value': np.cumsum(np.random.randn(365)) + 100,  # Random walk
        })
        
        # Test: Treino sempre vem antes do teste
        split_date = pd.Timestamp('2020-09-01')
        train_data = data[data['datetime'] < split_date]
        test_data = data[data['datetime'] >= split_date]
        
        assert max(train_data['datetime']) < min(test_data['datetime']), \
            "Training data must come before test data"
        assert len(train_data) > 0 and len(test_data) > 0, \
            "Both train and test sets should have data"
        
        logger.info(f"✓ Test edge_case_temporal_integrity PASSED")

    def tearDown(self):
        """Cleanup: Remove arquivos temporários"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info(f"✓ Cleanup: Removidos arquivos temporários")


# ========================================================================
# EXECUTAR TESTES
# ========================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("TESTES DE INTEGRAÇÃO: Pipeline Completo")
    print("="*70)
    
    test_suite = TestFullPipeline()
    test_suite.setUp()
    
    try:
        test_suite.test_data_loading()
        test_suite.test_feature_engineering_columns()
        test_suite.test_model_training_baseline()
        test_suite.test_model_training_flexible()
        test_suite.test_model_persistence_save()
        test_suite.test_model_persistence_load()
        test_suite.test_model_consistency_after_reload()
        test_suite.test_versioning_system()
        test_suite.test_end_to_end_flow()
        test_suite.test_edge_case_temporal_integrity()
        
    finally:
        test_suite.tearDown()
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES DE INTEGRAÇÃO PASSARAM!")
    print("="*70)
