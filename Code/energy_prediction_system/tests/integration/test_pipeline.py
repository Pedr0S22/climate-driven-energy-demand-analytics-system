import pytest
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from unittest.mock import MagicMock, patch

# Importações do projeto
from data_pipeline.cleaning import cleaning
from data_pipeline.feature_engineering import FeatureEngineer
from data_pipeline.modeling import (
    ModelManager,
    PipelineOrchestrator,
)

class TestPipelineIntegration:
    
    @pytest.fixture
    def project_env(self, tmp_path):
        """Simula a estrutura completa do projeto para o ModelManager."""
        base = tmp_path / "energy_system"
        # Estrutura exigida pelo ModelManager e Pipeline
        (base / "data/raw/energy").mkdir(parents=True)
        (base / "data/raw/weather").mkdir(parents=True)
        (base / "data/processed/feat-engineering").mkdir(parents=True)
        (base / "models/hourly").mkdir(parents=True)
        (base / "models/daily").mkdir(parents=True)
        return base

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_end_to_end_pipeline(self, mock_db, project_env):
        # 1. MOCK DA BASE DE DADOS
        mock_db.return_value = MagicMock()
        
        # 2. DADOS SINTÉTICOS - Aumentado para 4 anos para garantir splits válidos
        # O ModelManager (modeling.py) precisa de: 1 ano treino + 1 ano gap + 1 ano teste.
        start_date = "2020-01-01"
        times = pd.date_range(start_date, periods=24*365*4, freq="h", tz="UTC")
        
        df_e = pd.DataFrame({
            "Unnamed: 0": times, 
            "Load_MW": np.random.uniform(20000, 30000, len(times))
        })
        df_e.to_csv(project_env / "data/raw/energy/energy.csv", index=False)
        
        df_w = pd.DataFrame({
            "valid_time": times, 
            "t2m": np.random.uniform(280, 290, len(times)), 
            "skt": np.random.uniform(280, 290, len(times)), 
            "ssrd": 100.0,
            "latitude": 40.4, 
            "longitude": -3.7
        })
        df_w.to_csv(project_env / "data/raw/weather/weather.csv", index=False)

        # 3. LIMPEZA
        # Patch para evitar que o tratamento de outliers remova os nossos dados aleatórios
        with patch("data_pipeline.cleaning.DataCleaner.treat_weather_outliers", side_effect=lambda x: x):
            df_h, _ = cleaning(
                energy_dir=project_env / "data/raw/energy",
                weather_dir=project_env / "data/raw/weather",
                train_data=True,
                output_dir=project_env / "data/processed"
            )

        # 4. FEATURE ENGINEERING
        fe = FeatureEngineer(threshold=0.6, models_dir=project_env / "models", frequency="hourly")
        results = fe.run_pipeline(df_h, fit=True)
        
        # Guardar os ficheiros processados na pasta esperada pelo ModelManager
        for ds_type, df_feat in results.items():
            dest = project_env / f"data/processed/feat-engineering/features_hourly_{ds_type}.csv"
            df_feat.to_csv(dest, index=False)

        # 5. MODELAÇÃO
        orchestrator = PipelineOrchestrator(db_config={"fake": "config"})
        
        # Injeção manual e configuração do Manager para usar as pastas de teste
        orchestrator.manager = ModelManager(frequency="hourly")
        orchestrator.manager.data_dir = project_env / "data/processed/feat-engineering"
        orchestrator.manager.models_dir = project_env / "models/hourly"
        # Reduzimos n_partitions para 3 para o teste ser mais rápido e caber nos 4 anos
        orchestrator.manager.n_partitions = 3 

        # Carregar datasets gerados no passo 4
        datasets = orchestrator.manager.load_all_datasets()
        assert len(datasets) > 0, "Deveria ter carregado datasets do Feature Engineering"

        # Calcular splits temporais (Expanding, Fixed, Nested)
        splits_by_strategy = orchestrator._precalculate_splits(datasets)
        
        # Verificar se foram gerados splits (evita o erro AttributeError: 'NoneType')
        for strat, ds_splits in splits_by_strategy.items():
            for ds_name, s in ds_splits.items():
                assert len(s) > 0, f"Estratégia {strat} no dataset {ds_name} não gerou splits!"

        # Executar apenas o baseline para validar o fluxo de treino e gravação na DB mockada
        orchestrator._evaluate_and_save_model(
            model_type="baseline", 
            freq="hourly", 
            datasets=datasets, 
            splits_by_strategy=splits_by_strategy
        )

        # 6. ASSERÇÕES FINAIS
        # O prefixo definido no modeling.py para baseline é "LR"
        model_files = list((project_env / "models/hourly").glob("LR_v*.joblib"))
        assert len(model_files) > 0, "O modelo LR deveria ter sido gravado em disco."
        
        saved_model = joblib.load(model_files[0])
        assert hasattr(saved_model, "predict"), "O ficheiro guardado deve ser um modelo válido."