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

# IMPORTANTE: Confirma o import, dependendo de como o pytest está a ler.
from data_pipeline.modeling import ModelManager, StatisticalEvaluator, run_evaluation_pipeline

class TestModelingFullCoverage(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.models_dir = Path(self.temp_dir) / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # DADOS SINTÉTICOS: 3 anos e 2 meses de dados diários.
        # Isto garante dados suficientes para passar na tua rigorosa matemática
        # de splits temporais (que exige gap de 1 ano + 1 ano de teste).
        dates = pd.date_range(start='2020-01-01', end='2023-03-01', freq='D')
        
        self.df = pd.DataFrame({
            'datetime': dates,
            'Load_MW': np.random.normal(2000, 100, size=len(dates)),   # Usado para hourly
            'Load_MWh': np.random.normal(2000, 100, size=len(dates)),  # Usado para daily
            'temperatura': np.random.normal(15, 5, size=len(dates))
        })

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('data_pipeline.modeling.joblib.dump')
    @patch('data_pipeline.modeling.optuna.create_study')
    @patch('data_pipeline.modeling.ModelManager.load_all_datasets')
    def test_run_evaluation_pipeline_full_coverage(self, mock_load, mock_create_study, mock_dump):
        """
        Executa a mega pipeline real! Isto vai ler os dados sintéticos, calcular
        as métricas todas, testar desempates, estatística de Friedman, etc.
        """
        # 1. OPTUNA RÁPIDO: Enganamos o Optuna para não demorar horas
        # Em vez de 30 trials pesadas, ele pensa que já encontrou o melhor modelo super rápido
        mock_study = MagicMock()
        mock_study.best_params = {'n_estimators': 2, 'max_depth': 2}
        mock_create_study.return_value = mock_study
        
        # 2. DATASETS FALSOS: Evita ter de ler do disco. 
        # Passamos as 3 versões (full, selected, pca) para o Friedman Test passar!
        mock_load.return_value = {
            'full': self.df.copy(),
            'selected': self.df.copy(),
            'pca': self.df.copy()
        }
        
        # 3. EXECUTA O CÓDIGO REAL (A magia da cobertura acontece aqui)
        try:
            # Esta única linha vai visitar mais de 100 linhas do teu modeling.py!
            run_evaluation_pipeline()
            sucesso = True
        except Exception as e:
            print(f"A pipeline quebrou: {e}")
            sucesso = False
            
        self.assertTrue(sucesso, "A função principal falhou ao processar os dados!")
        self.assertTrue(mock_dump.called, "Os modelos não foram guardados com o joblib!")

    # =========================================================================
    # Testes Auxiliares (Para tapar os "buracos" que a pipeline pode não tocar)
    # =========================================================================

    def test_get_next_version_file_reading(self):
        """Testa diretamente a função que gere as versões dos ficheiros"""
        manager = ModelManager()
        manager.models_dir = self.models_dir # Desvia para a nossa pasta temporária
        
        # Criamos 2 ficheiros falsos no disco: v1 e v3
        (self.models_dir / "LR_v1.joblib").touch()
        (self.models_dir / "LR_v3.joblib").touch()
        
        version = manager._get_next_version("LR")
        self.assertEqual(version, 4)
        
    @patch('data_pipeline.modeling.Path.exists')
    @patch('data_pipeline.modeling.pd.read_csv')
    def test_load_all_datasets_disk_reading(self, mock_read, mock_exists):
        """Testa o carregador inicial de ficheiros"""
        manager = ModelManager()
        mock_exists.return_value = True
        # Quando ele tentar fazer read_csv, recebe este mini DataFrame
        mock_read.return_value = pd.DataFrame({'datetime': ['2020-01-01'], 'val': [1]})
        
        ds = manager.load_all_datasets()
        self.assertIn('full', ds)
        self.assertIn('pca', ds)