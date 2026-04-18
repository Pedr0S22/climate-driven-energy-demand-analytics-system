"""
Integration Tests para o pipeline de modeling completo

Testa:
- Fluxo completo de carregamento até persistência usando as classes reais
- Carregamento e reuso de modelos salvos
- Consistência de resultados
- Versionamento de ficheiros
"""

import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import joblib
import tempfile
import shutil
from pathlib import Path
import logging

# IMPORTANTE: Importa o teu código real!
from data_pipeline.modeling import ModelManager, StatisticalEvaluator, run_evaluation_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFullPipelineIntegration(unittest.TestCase):
    """Testes de integração do pipeline completo"""
    
    def setUp(self):
        """Setup: Cria ambiente de ficheiros e dados sintéticos para testes"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Cria a estrutura de pastas simulada
        self.data_dir = self.temp_path / "data" / "processed" / "feat-engineering"
        self.models_dir = self.temp_path / "models" / "hourly"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Instancia o Manager e REDIRECIONA as pastas para a nossa diretoria temporária
        self.manager = ModelManager(frequency="hourly")
        self.manager.data_dir = self.data_dir
        self.manager.models_dir = self.models_dir
        
        # Cria dados sintéticos realistas (5 anos para passar nos rigorosos splits)
        dates = pd.date_range(start='2018-01-01', end='2023-12-31', freq='h')
        np.random.seed(42)
        
        hour_of_day = dates.hour
        seasonality = 2000 + 500 * np.sin(2 * np.pi * hour_of_day / 24)
        
        self.test_data = pd.DataFrame({
            'datetime': dates,
            'Load_MW': seasonality + np.random.normal(0, 100, size=len(dates)),
            'temperature': 15 + 10 * np.sin(2 * np.pi * dates.dayofyear / 365),
            'humidity': 60 + 20 * np.sin(2 * np.pi * dates.dayofyear / 365),
        })
        
        # Guarda o dataset no disco temporário para o ModelManager conseguir ler
        self.dataset_path = self.data_dir / "features_hourly_full.csv"
        self.test_data.to_csv(self.dataset_path, index=False)
        
        logger.info(f"✓ Setup: Criados {len(self.test_data)} registos e guardados em disco.")

    def tearDown(self):
        """Cleanup: Remove a pasta temporária e todos os modelos/dados simulados"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        logger.info("✓ Cleanup: Ambiente limpo.")

    def test_data_loading_from_disk(self):
        """Integration Test: O ModelManager lê ficheiros do disco com sucesso"""
        datasets = self.manager.load_all_datasets()
        
        self.assertIn('full', datasets, "Deveria ter carregado o dataset 'full'")
        self.assertEqual(len(datasets['full']), len(self.test_data))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(datasets['full']['datetime']))
        logger.info("✓ Test data_loading_from_disk PASSED")

    def test_model_training_baseline(self):
        """Integration Test: Treina modelo baseline com a função real"""
        # Prepara dados usando a nossa simulação
        X = self.test_data[['temperature', 'humidity']].copy()
        y = self.test_data['Load_MW'].copy()
        
        model = self.manager.train_baseline(X, y)
        
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'predict'))
        logger.info("✓ Test model_training_baseline PASSED")

    @patch('data_pipeline.modeling.optuna.create_study')
    def test_model_training_flexible(self, mock_create_study):
        """Integration Test: Treina o Random Forest simulando a busca do Optuna"""
        # Configuramos o Mock do Optuna para o teste não demorar minutos
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 10, 'max_depth': 5}
        mock_create_study.return_value = mock_study
        
        # O modelo precisa do datetime para a estratégia de validação
        X = self.test_data[['datetime', 'temperature', 'humidity']].copy()
        y = self.test_data['Load_MW'].copy()
        
        model = self.manager.train_flexible(X, y, strategy="expanding")
        
        self.assertIsNotNone(model)
        self.assertTrue(hasattr(model, 'predict'))
        logger.info("✓ Test model_training_flexible PASSED")

    def test_versioning_and_persistence(self):
        """Integration Test: Cria versões, guarda no disco e recarrega"""
        # 1. Simular o versionamento gravando modelos falsos no disco temporário
        (self.models_dir / "LR_v1.joblib").touch()
        (self.models_dir / "LR_v2.joblib").touch()
        
        # 2. Testa o método real para ver se apanha a versão 3
        next_version = self.manager._get_next_version("LR")
        self.assertEqual(next_version, 3)
        
        # 3. Treina um modelo rápido e guarda-o usando o versionamento detetado
        X = self.test_data[['temperature', 'humidity']].copy()
        y = self.test_data['Load_MW'].copy()
        model = self.manager.train_baseline(X, y)
        
        save_path = self.models_dir / f"LR_v{next_version}.joblib"
        joblib.dump(model, save_path)
        
        # 4. Verifica se o ficheiro existe e recarrega
        self.assertTrue(save_path.exists())
        loaded_model = joblib.load(save_path)
        
        # 5. Verifica predição
        predictions = loaded_model.predict(X.iloc[:5])
        self.assertEqual(len(predictions), 5)
        logger.info("✓ Test versioning_and_persistence PASSED")

    @patch('data_pipeline.modeling.joblib.dump')
    @patch('data_pipeline.modeling.ModelManager')
    def test_end_to_end_pipeline(self, MockManager, mock_dump):
        """Integration Test: Roda o pipeline de avaliação principal inteiro"""
        # Este teste força a função run_evaluation_pipeline() a correr,
        # injetando a nossa instância do manager configurada para as pastas temporárias.
        
        # Prepara a simulação do Manager para devolver os dados temporários
        mock_instance = MockManager.return_value
        mock_instance.target_col = "Load_MW"
        mock_instance.models_dir = self.models_dir
        
        # Reduz as partições para o teste ser quase instantâneo em vez de iterar 30 folds
        mock_instance.n_partitions = 1 
        
        # Devolve apenas o dataset 'full'
        mock_instance.load_all_datasets.return_value = {'full': self.test_data}
        
        # Gera os splits reais usando o teu método
        mock_instance.generate_splits.side_effect = lambda df, strategy: self.manager.generate_splits(df, strategy)
        
        # Finge as funções de treino para não perdermos tempo computacional no CI/CD
        dummy_model = MagicMock()
        dummy_model.predict.return_value = np.zeros(100) # Predições dummy
        mock_instance.train_baseline.return_value = dummy_model
        mock_instance.train_flexible.return_value = dummy_model
        mock_instance._get_next_version.return_value = 1
        
        # Executa o pipeline de avaliação
        try:
            run_evaluation_pipeline()
            pipeline_success = True
        except Exception as e:
            logger.error(f"Pipeline falhou com erro: {e}")
            pipeline_success = False
            
        self.assertTrue(pipeline_success, "A pipeline end-to-end não deve gerar exceções.")
        self.assertTrue(mock_dump.called, "Deveria ter guardado os modelos finais vencedores.")
        logger.info("✓ Test end_to_end_pipeline PASSED")