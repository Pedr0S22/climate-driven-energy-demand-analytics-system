"""
Integration Tests com foco EXCLUSIVO no modeling.py para garantir >90% de coverage.
"""
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import tempfile
import shutil
from pathlib import Path
import logging

# IMPORTANTE: Atualizado para refletir a nova arquitetura orientada a objetos!
from data_pipeline.modeling import (
    ModelManager, 
    StatisticalEvaluator, 
    DatabaseManager, 
    PipelineOrchestrator
)

# Silenciar os logs para os testes não encherem o ecrã
logging.getLogger("data_pipeline.modeling").setLevel(logging.CRITICAL)

class TestModelingFullCoverage(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.models_dir = Path(self.temp_dir) / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # DADOS SINTÉTICOS: 3 anos e 2 meses de dados diários.
        # Isto garante dados suficientes para passar na matemática rigorosa
        # de splits temporais (que exige gap de 1 ano + 1 ano de teste).
        dates = pd.date_range(start='2020-01-01', end='2023-03-01', freq='D')
        
        self.df = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(2000, 100, size=len(dates)),   # Para hourly
            'Load_MWh': np.random.normal(48000, 2000, size=len(dates)),# Para daily
            'temperatura': np.random.normal(15, 5, size=len(dates))
        })

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('data_pipeline.modeling.psycopg2.connect')
    @patch('data_pipeline.modeling.joblib.dump')
    @patch('data_pipeline.modeling.optuna.create_study')
    @patch('data_pipeline.modeling.ModelManager.load_all_datasets')
    def test_run_orchestrator_pipeline_full_coverage(self, mock_load, mock_create_study, mock_dump, mock_db_connect):
        """
        Executa a mega pipeline real (Orchestrator)! 
        Cobre os loops Hourly e Daily, as 3 estratégias e a inserção na BD.
        """
        # 1. OPTUNA RÁPIDO: Enganamos o Optuna para não demorar horas
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 2, 'max_depth': 2}
        mock_create_study.return_value = mock_study
        
        # 2. DATASETS FALSOS: Retornamos os 3 datasets para a estatística completa
        mock_load.return_value = {
            'full': self.df.copy(),
            'selected': self.df.copy(),
            'pca': self.df.copy()
        }

        # 3. MOCK BASE DE DADOS: Finge que ligou ao PostgreSQL sem falhar
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # 4. EXECUTA O CÓDIGO REAL DA PIPELINE
        db_config = {"dbname": "test", "user": "test"} # Passamos config para forçar a entrada no bloco da BD
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
            
        self.assertTrue(sucesso, "O PipelineOrchestrator falhou ao processar os dados!")
        self.assertTrue(mock_dump.called, "Os modelos não foram guardados no disco!")
        self.assertTrue(mock_cursor.execute.called, "A pipeline não tentou gravar na Base de Dados!")

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
        self.assertEqual(version, 4)
        
    @patch('data_pipeline.modeling.Path.exists')
    @patch('data_pipeline.modeling.pd.read_csv')
    def test_load_all_datasets_disk_reading(self, mock_read, mock_exists):
        """Cobre o carregamento do disco quando os ficheiros existem."""
        manager = ModelManager()
        mock_exists.return_value = True
        mock_read.return_value = pd.DataFrame({'datetime': ['2020-01-01'], 'val': [1]})
        
        ds = manager.load_all_datasets()
        self.assertIn('full', ds)

    @patch('data_pipeline.modeling.optuna.create_study')
    def test_train_flexible_edge_cases(self, mock_create_study):
        """Cobre a estratégia 'nested' e o fallback de dados insuficientes."""
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 2, 'max_depth': 2}
        mock_create_study.return_value = mock_study
        
        manager = ModelManager()
        
        # 1. Testar modo Nested explícito
        model_nested = manager.train_flexible(self.df[['datetime', 'temperatura']], self.df['Load_MW'], strategy="nested")
        self.assertIsNotNone(model_nested)
        
        # 2. Testar modo Expanding com poucos dados (aciona o fallback do split 80/20)
        small_df = self.df.iloc[:50].copy() # Apenas 50 dias, insuficiente para gap de 2 anos
        model_small = manager.train_flexible(small_df[['datetime', 'temperatura']], small_df['Load_MW'], strategy="expanding")
        self.assertIsNotNone(model_small)

    @patch('data_pipeline.modeling.psycopg2.connect')
    def test_database_manager_exception(self, mock_connect):
        """Cobre o except bloco se a Base de Dados estiver desligada."""
        manager = DatabaseManager({"dbname": "test"})
        # Força o PostgreSQL a atirar um erro
        mock_connect.side_effect = Exception("Docker is down!")
        
        # Se a pipeline quebrar aqui, o teste falha (o objetivo é que o except apanhe o erro silenciosamente)
        try:
            manager.save_model_metrics("RF", "path/model.joblib", 1.0, 1.0, 1.0)
            passed = True
        except Exception:
            passed = False
            
        self.assertTrue(passed, "Uma falha na base de dados parou a execução da pipeline!")

if __name__ == '__main__':
    unittest.main()