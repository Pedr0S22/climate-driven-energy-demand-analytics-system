import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from data_pipeline.modeling import (
    DatabaseManager,
    ModelManager,
    PipelineOrchestrator,
    StatisticalEvaluator,
)

logging.getLogger("data_pipeline.modeling").setLevel(logging.CRITICAL)


class TestStatisticalEvaluator:
    """Testes para a classe StatisticalEvaluator"""

    def test_normality_true(self):
        np.random.seed(42)
        # Gerar dados normais sintéticos
        normal_data = np.random.normal(loc=0, scale=1, size=100)
        data_groups = {"group1": normal_data}
        
        result = StatisticalEvaluator.test_normality(data_groups)
        assert result is True

    def test_normality_zero_std(self):
        data_groups = {"group1": [5, 5, 5, 5, 5]}
        
        result = StatisticalEvaluator.test_normality(data_groups)
        assert result is False

    def test_normality_false_non_normal_data(self):
        """Testa o caso em que os dados não são normais e o desvio padrão é diferente de zero."""
        np.random.seed(42)

        non_normal_data = np.random.exponential(scale=1.0, size=100)

        assert np.std(non_normal_data) > 0
        
        data_groups = {"group1": non_normal_data}
        
        result = StatisticalEvaluator.test_normality(data_groups)

        assert result is False

    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_dataset_anova_diff_win_rmse(self, mock_normality, mock_anova):
        """
        CENÁRIO 1: Dados normais (Usa ANOVA), com diferença estatística (p < 0.05).
        Desempate resolvido logo no primeiro critério: Menor RMSE.
        """
        # Arrange: Forçar comportamento dos testes estatísticos
        mock_normality.return_value = True
        mock_anova.return_value = (10.5, 0.02)  # p-value < 0.05 (Há diferença estatística)

        # Dataset A tem pior RMSE (10) | Dataset B tem melhor RMSE (5)
        results = {
            "Dataset_A": {"rmse": [10.0]*3, "r2": [0.5]*3, "mae": [4.0]*3},
            "Dataset_B": {"rmse": [5.0]*3,  "r2": [0.8]*3, "mae": [2.0]*3}
        }

        # Act
        best_ds, metrics = StatisticalEvaluator.select_best_dataset(results)

        # Assert
        mock_normality.assert_called_once()
        mock_anova.assert_called_once()
        assert best_ds == "Dataset_B"
        assert metrics["rmse"] == 5.0


    @patch("data_pipeline.modeling.friedmanchisquare")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_dataset_friedman_no_diff_win_r2(self, mock_normality, mock_friedman):
        """
        CENÁRIO 2: Dados NÃO normais (Usa Friedman), sem diferença estatística (p >= 0.05).
        Empate no RMSE. Desempate resolvido no segundo critério: Maior R2.
        """
        # Arrange
        mock_normality.return_value = False
        mock_friedman.return_value = (2.1, 0.15)  # p-value > 0.05 (Sem diferença estatística)

        # Empatam no RMSE (5.0). Dataset_A ganha no R2 (0.9 vs 0.8)
        results = {
            "Dataset_A": {"rmse": [5.0]*3, "r2": [0.9]*3, "mae": [2.0]*3},
            "Dataset_B": {"rmse": [5.0]*3, "r2": [0.8]*3, "mae": [2.0]*3}
        }

        # Act
        best_ds, metrics = StatisticalEvaluator.select_best_dataset(results)

        # Assert
        mock_normality.assert_called_once()
        mock_friedman.assert_called_once()
        assert best_ds == "Dataset_A"
        assert metrics["r2"] == 0.9


    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_dataset_win_mae(self, mock_normality, mock_anova):
        """
        CENÁRIO 3: Empate em RMSE e R2.
        Desempate resolvido no último critério: Menor MAE.
        """
        # Arrange
        mock_normality.return_value = True
        mock_anova.return_value = (5.0, 0.01)

        # Empatam no RMSE (5.0) e R2 (0.9). Dataset_B ganha no MAE (1.0 vs 3.0)
        results = {
            "Dataset_A": {"rmse": [5.0]*3, "r2": [0.9]*3, "mae": [3.0]*3},
            "Dataset_B": {"rmse": [5.0]*3, "r2": [0.9]*3, "mae": [1.0]*3}
        }

        # Act
        best_ds, metrics = StatisticalEvaluator.select_best_dataset(results)

        # Assert
        assert best_ds == "Dataset_B"
        assert metrics["mae"] == 1.0

    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_strategy_anova_win_rmse(self, mock_normality, mock_anova):
        """
        CENÁRIO 1: Dados normais (Usa ANOVA).
        Desempate resolvido logo no primeiro critério: Menor RMSE.
        """
        # Arrange
        mock_normality.return_value = True
        mock_anova.return_value = (12.5, 0.01) # Simula p-value < 0.05

        # Estratégia B tem o melhor RMSE (5.0 vs 10.0)
        strategy_results = {
            "expanding": {"metrics": {"rmse": [10.0]*3, "r2": [0.5]*3, "mae": [4.0]*3}},
            "fixed_rolling": {"metrics": {"rmse": [5.0]*3,  "r2": [0.8]*3, "mae": [2.0]*3}}
        }

        # Act
        best_strat = StatisticalEvaluator.select_best_strategy(strategy_results)

        # Assert
        mock_normality.assert_called_once()
        mock_anova.assert_called_once()
        assert best_strat == "fixed_rolling"


    @patch("data_pipeline.modeling.kruskal")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_strategy_kruskal_win_r2(self, mock_normality, mock_kruskal):
        """
        CENÁRIO 2: Dados NÃO normais (Usa Kruskal-Wallis).
        Empate no RMSE. Desempate resolvido no segundo critério: Maior R2.
        """
        # Arrange
        mock_normality.return_value = False
        mock_kruskal.return_value = (3.0, 0.1) # Simula p-value > 0.05

        # Empatam no RMSE (5.0). Estratégia "nested" ganha no R2 (0.9 vs 0.8)
        strategy_results = {
            "expanding": {"metrics": {"rmse": [5.0]*3, "r2": [0.8]*3, "mae": [2.0]*3}},
            "nested": {"metrics": {"rmse": [5.0]*3, "r2": [0.9]*3, "mae": [2.0]*3}}
        }

        # Act
        best_strat = StatisticalEvaluator.select_best_strategy(strategy_results)

        # Assert
        mock_normality.assert_called_once()
        mock_kruskal.assert_called_once()
        assert best_strat == "nested"


    @patch("data_pipeline.modeling.f_oneway")
    @patch.object(StatisticalEvaluator, "test_normality")
    def test_select_best_strategy_win_mae(self, mock_normality, mock_anova):
        """
        CENÁRIO 3: Empate no RMSE e R2. 
        Desempate resolvido no último critério: Menor MAE.
        """
        # Arrange
        mock_normality.return_value = True
        mock_anova.return_value = (1.5, 0.4)

        # Empatam no RMSE (5.0) e R2 (0.9). Estratégia "expanding" ganha no MAE (1.0 vs 3.0)
        strategy_results = {
            "expanding": {"metrics": {"rmse": [5.0]*3, "r2": [0.9]*3, "mae": [1.0]*3}},
            "fixed_rolling": {"metrics": {"rmse": [5.0]*3, "r2": [0.9]*3, "mae": [3.0]*3}}
        }

        # Act
        best_strat = StatisticalEvaluator.select_best_strategy(strategy_results)

        # Assert
        assert best_strat == "expanding"

class TestModelManager:

    @pytest.fixture
    def dummy_df(self):
        """Cria um DataFrame sintético com 6 anos de dados para testar os splits temporais."""
        np.random.seed(42)
        dates = pd.date_range(start="2016-01-01", end="2022-01-01", freq="D")
        df = pd.DataFrame({
            "datetime": dates,
            "Feature_A": np.random.rand(len(dates)),
            "Feature_B": np.random.rand(len(dates)),
            "Feature_C": np.random.rand(len(dates)),
            "Load_MW": np.random.rand(len(dates))
        })
        return df

    # ==========================================
    # 1. Testes de Inicialização e Configuração
    # ==========================================
    def test_init_target_col_assignment(self):
        """Garante que a coluna alvo (target_col) muda conforme a frequência."""
        manager_hourly = ModelManager(frequency="hourly")
        assert manager_hourly.target_col == "Load_MW"

        manager_daily = ModelManager(frequency="daily")
        assert manager_daily.target_col == "Load_MWh"

    @patch("pandas.read_csv")
    @patch.object(Path, "exists")
    def test_load_all_datasets(self, mock_exists, mock_read_csv):
        """Testa se carrega os datasets corretamente apenas se existirem no disco."""
        
        # CORREÇÃO: Forçar a devolver True para todos (evita problemas com binds do Path.exists)
        mock_exists.return_value = True
        
        # Simulamos o DataFrame que o pandas lê do CSV
        mock_read_csv.return_value = pd.DataFrame({"datetime": ["2020-01-01"], "val": [1]})

        manager = ModelManager()
        datasets = manager.load_all_datasets()

        # Deve conter os 3 datasets e a coluna datetime deve ter sido convertida
        assert "full" in datasets
        assert "selected" in datasets
        assert "pca" in datasets
        assert pd.api.types.is_datetime64_any_dtype(datasets["full"]["datetime"])       
    
    # ==========================================
    # 2. Testes de Janelas Temporais (Splits)
    # ==========================================
    def test_generate_splits_fixed_rolling_gap(self, dummy_df):
        """Testa se a estratégia 'fixed_rolling' respeita o Gap de 1 ano entre treino e teste."""
        manager = ModelManager()
        splits = manager.generate_splits(dummy_df, strategy="fixed_rolling")

        # Verifica se gerou splits
        assert len(splits) > 0

        # Pega no split mais recente (o último da lista)
        train_idx, test_idx = splits[-1]
        
        train_dates = dummy_df.iloc[train_idx]["datetime"]
        test_dates = dummy_df.iloc[test_idx]["datetime"]

        # 1. Teste deve ter 1 ano
        test_duration = test_dates.max() - test_dates.min()
        assert test_duration.days >= 364

        # 2. Treino deve ter 1 ano (na estratégia fixed_rolling)
        train_duration = train_dates.max() - train_dates.min()
        assert train_duration.days >= 364

        # 3. O GAP DEVE SER DE 1 ANO (A diferença entre o fim do treino e o início do teste)
        gap_duration = test_dates.min() - train_dates.max()
        assert gap_duration.days >= 364

    def test_generate_splits_expanding(self, dummy_df):
        """Testa se a estratégia 'expanding' usa todos os dados do passado disponíveis."""
        manager = ModelManager()
        splits = manager.generate_splits(dummy_df, strategy="expanding")
        
        # No expanding, o primeiro split da lista (o mais antigo) deve começar
        # na exata mesma data que o último split da lista (o mais recente).
        primeiro_split_treino_idx = splits[0][0]
        ultimo_split_treino_idx = splits[-1][0]

        start_date_primeiro = dummy_df.iloc[primeiro_split_treino_idx]["datetime"].min()
        start_date_ultimo = dummy_df.iloc[ultimo_split_treino_idx]["datetime"].min()

        assert start_date_primeiro == start_date_ultimo == dummy_df["datetime"].min()

    # ==========================================
    # 3. Testes de Sistema de Ficheiros
    # ==========================================
    @patch.object(Path, "glob")
    def test_get_next_version(self, mock_glob):
        """Garante que o versionamento automático deteta a versão mais alta e soma 1."""
        manager = ModelManager()
        
        # Simula ficheiros existentes: LR_v1.joblib e LR_v3.joblib (saltou o 2)
        mock_path_v1 = MagicMock()
        mock_path_v1.name = "LR_v1.joblib"
        mock_path_v3 = MagicMock()
        mock_path_v3.name = "LR_v3.joblib"
        
        mock_glob.return_value = [mock_path_v1, mock_path_v3]

        next_version = manager._get_next_version("LR")
        assert next_version == 4  # O maior era 3, o próximo tem de ser 4

    # ==========================================
    # 4. Testes de Modelação (Treino)
    # ==========================================
    def test_train_baseline(self):
        """Testa se a baseline (Linear Regression) treina e devolve os top 2 drivers."""
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
        """
        Usa Mocks no Optuna e RandomForest para testar o train_flexible sem 
        fazer computação pesada, testando a extração dos drivers.
        """
        # 1. Configurar Mock do Optuna (simular que já encontrou os melhores parâmetros)
        mock_study = MagicMock()
        mock_study.best_params = {"n_estimators": 5, "max_depth": 3}
        mock_create_study.return_value = mock_study

        # 2. Configurar Mock do modelo final para devolver feature_importances falsas
        mock_rf_instance = MagicMock()
        mock_rf_instance.feature_importances_ = np.array([0.4, 0.1, 0.5]) 
        mock_rf_class.return_value = mock_rf_instance

        manager = ModelManager()
        
        # DataFrame simulado (precisa da coluna datetime para a lógica de nested cross-validation)
        X_train = pd.DataFrame({
            "datetime": pd.date_range("2021-01-01", periods=10, freq="ME"),
            "Feature_A": range(10),
            "Feature_B": range(10),
            "Feature_C": range(10)
        })
        y_train = pd.Series(range(10))

        # Act
        model, drivers = manager.train_flexible(X_train, y_train, strategy="nested")

        # Assert
        assert len(drivers) == 2
        assert "Feature_C" in drivers
        assert "Feature_A" in drivers
        assert "datetime" not in drivers

class TestDatabaseManager:

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_success(self, mock_connect):
        """
        CENÁRIO 1: Caminho feliz. 
        Garante que a query é executada e as conversões de tipos são feitas.
        """
        # Arrange: Configurar os Mocks para simular a ligação à BD (with conn e with cursor)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        db_config = {"dbname": "test_db", "user": "test_user"}
        db_manager = DatabaseManager(db_config)

        # Act: Passar numpy floats e uma lista de drivers
        db_manager.save_model_metrics(
            model_type="Random Forest",
            model_pred_type="hourly",
            file_path="models/RF_v1.joblib",
            dataset_selected="full",
            top2_drivers=["Feature_A", "Feature_B"],
            rmse=np.float64(1.23),
            mae=np.float64(0.8),
            r2=np.float64(0.95)
        )

        # Assert: Verificar se executou a query uma vez
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        
        # Extrair os argumentos que foram passados para dentro do cur.execute
        args_passed_to_execute = mock_cursor.execute.call_args[0][1]
        
        # Garante que a lista foi convertida para uma string separada por vírgulas
        assert args_passed_to_execute[4] == "Feature_A, Feature_B" 
        # Garante que os numpy floats foram convertidos para native python floats puros
        assert isinstance(args_passed_to_execute[5], float)
        assert args_passed_to_execute[5] == 1.23

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_no_config(self, mock_connect):
        """
        CENÁRIO 2: Early return. 
        Se db_config for None ou vazio, a função não deve tentar conectar à BD.
        """
        # Arrange: Passar None como config
        db_manager = DatabaseManager(None)

        # Act
        db_manager.save_model_metrics(
            "LR", "daily", "path", "pca", ["A"], 1.0, 1.0, 1.0
        )

        # Assert: Garante que nunca tentou conectar ao psycopg2
        mock_connect.assert_not_called()

    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_string_driver(self, mock_connect):
        """
        CENÁRIO 3: Parâmetro de drivers diferente. 
        Se top2_drivers não for lista (for string), o sistema deve lidar com isso graciosamente.
        """
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        db_manager = DatabaseManager({"dbname": "test_db"})

        # Act: Passar uma string direta no lugar da lista
        db_manager.save_model_metrics(
            "LR", "daily", "path", "pca", "ApenasUmDriver", 1.0, 1.0, 1.0
        )

        # Assert
        args_passed_to_execute = mock_cursor.execute.call_args[0][1]
        assert args_passed_to_execute[4] == "ApenasUmDriver"

    @patch("builtins.print")
    @patch("data_pipeline.modeling.psycopg2.connect")
    def test_save_model_metrics_exception_handling(self, mock_connect, mock_print):
        """
        CENÁRIO 4: Tratamento de exceção. 
        Garante que o erro da BD não rebenta a aplicação, apenas imprime o log.
        """
        # Arrange: Forçar o connect a lançar um erro quando for chamado
        mock_connect.side_effect = Exception("Erro fictício de Timeout do Servidor")
        
        db_manager = DatabaseManager({"dbname": "test_db"})

        # Act: Tentamos gravar. Como há um try/except, não deve gerar crash (o teste não falha se não houver crash)
        db_manager.save_model_metrics(
            "LR", "daily", "path", "pca", ["A", "B"], 1.0, 1.0, 1.0
        )

        mock_print.assert_called_once_with("Erro ao guardar na base de dados: Erro fictício de Timeout do Servidor")

class TestPipelineOrchestrator:

    # ==========================================
    # 1. Teste Lógico de Desempate (Puro)
    # ==========================================
    def test_find_best_fold_index(self):
        """Testa a lógica complexa de desempate de folds (RMSE -> R2 -> MAE)."""
        orchestrator = PipelineOrchestrator()
        
        metrics = {
            "rmse": [10.0, 5.0, 5.0, 5.0],  # Folds 1, 2 e 3 empatam no RMSE (índices 1, 2, 3)
            "r2":   [0.1,  0.8, 0.9, 0.9],  # Folds 2 e 3 empatam no R2 (índices 2 e 3)
            "mae":  [5.0,  3.0, 3.0, 1.0]   # Fold 3 ganha no MAE (índice 3 tem o menor MAE)
        }
        
        melhor_idx = orchestrator._find_best_fold_index(metrics)
        
        # O vencedor deve ser o índice 3 (o 4º fold)
        assert melhor_idx == 3


    # ==========================================
    # 2. Teste de Pré-cálculo de Janelas
    # ==========================================
    def test_precalculate_splits(self):
        """Garante que a estrutura de dicionários dos splits é montada corretamente."""
        orchestrator = PipelineOrchestrator()
        
        # Fazer mock do manager que ainda não existe no init
        orchestrator.manager = MagicMock()
        # Simular que a função generate_splits devolve uma lista fictícia de 2 splits
        orchestrator.manager.generate_splits.return_value = [("treino1", "teste1"), ("treino2", "teste2")]
        
        datasets = {"full": pd.DataFrame(), "pca": pd.DataFrame()}
        
        splits_by_strategy = orchestrator._precalculate_splits(datasets)
        
        # Verifica se criou as chaves das 3 estratégias
        assert "expanding" in splits_by_strategy
        assert "fixed_rolling" in splits_by_strategy
        assert "nested" in splits_by_strategy
        
        # Verifica se dentro de cada estratégia estão os datasets
        assert "full" in splits_by_strategy["expanding"]
        assert splits_by_strategy["expanding"]["pca"] == [("treino1", "teste1"), ("treino2", "teste2")]


    # ==========================================
    # 3. Teste do Loop de Treino
    # ==========================================
    @patch("data_pipeline.modeling.PipelineOrchestrator._precalculate_splits")
    def test_run_strategy_loops(self, mock_precalc):
        """Testa se o loop extrai métricas, treina o modelo e guarda os drivers."""
        orchestrator = PipelineOrchestrator()
        orchestrator.manager = MagicMock()
        orchestrator.manager.target_col = "Load_MW"
        
        # Mock do treino (devolve um modelo mock e os drivers)
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([10, 20])  # Previsões falsas
        orchestrator.manager.train_baseline.return_value = (mock_model, ["DriverA", "DriverB"])
        
        # Mock do avaliador estatístico
        orchestrator.evaluator.select_best_dataset = MagicMock(return_value=("full", {"rmse": 2.0, "r2": 0.9, "mae": 1.5}))

        # DataFrame falso
        df = pd.DataFrame({"Load_MW": [10, 20, 30, 40], "Feature": [1, 2, 3, 4]})
        datasets = {"full": df}
        
        # Splits falsos (1 fold: treino índices 0,1; teste índices 2,3)
        splits_by_strategy = {"fixed_rolling": {"full": [([0, 1], [2, 3])]}}
        
        # Executar
        resultado = orchestrator._run_strategy_loops(
            model_type="baseline", 
            strategy="fixed_rolling", 
            datasets=datasets, 
            splits_by_strategy=splits_by_strategy
        )
        
        # Asserts
        assert resultado["dataset"] == "full"
        assert "metrics" in resultado
        # Verifica se guardou os modelos e os drivers na memória
        assert len(resultado["metrics"]["models"]) == 1
        assert resultado["metrics"]["drivers"][0] == ["DriverA", "DriverB"]


    # ==========================================
    # 4. Teste de Avaliação e Gravação
    # ==========================================
    @patch("data_pipeline.modeling.joblib.dump")  # Evita criar ficheiros físicos
    def test_evaluate_and_save_model(self, mock_joblib_dump):
        """Testa se encontra a melhor estratégia, o melhor fold e grava tudo (Disco + BD)."""
        orchestrator = PipelineOrchestrator()
        orchestrator.manager = MagicMock()
        orchestrator.manager._get_next_version.return_value = 1
        orchestrator.manager.models_dir = MagicMock()
        orchestrator.manager.models_dir.__truediv__.return_value = "caminho/falso/LR_v1.joblib"
        
        # Fazer mock da Base de Dados
        orchestrator.db_manager = MagicMock()
        
        # Fazer mock para não correr os loops de verdade
        orchestrator._run_strategy_loops = MagicMock(return_value={
            "dataset": "pca", 
            "metrics": {
                "rmse": [10.0, 5.0, 2.0], 
                "r2": [0.5, 0.7, 0.9], 
                "mae": [3.0, 2.0, 1.0], 
                "models": ["modelo_mau", "modelo_medio", "modelo_bom"], 
                "drivers": [["D1"], ["D2"], ["Top1", "Top2"]]
            }
        })
        
        # Fazer mock do evaluator para forçar a estratégia "expanding" a ganhar
        orchestrator.evaluator.select_best_strategy.return_value = "expanding"
        
        # Executar
        orchestrator._evaluate_and_save_model(
            model_type="baseline", freq="hourly", datasets={}, splits_by_strategy={}
        )
        
        # Asserts: Garantir que gravou no disco o "modelo_bom" (que estava no índice 1)
        mock_joblib_dump.assert_called_once_with("modelo_bom", "caminho/falso/LR_v1.joblib")
        
        # Asserts: Garantir que gravou na BD com os top drivers certos
        orchestrator.db_manager.save_model_metrics.assert_called_once()
        args_chamados = orchestrator.db_manager.save_model_metrics.call_args[1] # kwargs
        
        assert args_chamados["dataset_selected"] == "pca"
        assert args_chamados["top2_drivers"] == ["Top1", "Top2"]
        assert args_chamados["rmse"] == 2.0


    # ==========================================
    # 5. Teste do Fluxo Principal (Run)
    # ==========================================
    @patch("data_pipeline.modeling.ModelManager")
    def test_run_empty_datasets(self, mock_model_manager_class):
        """Testa o bypass caso não encontre ficheiros de dados (não deve falhar)."""
        orchestrator = PipelineOrchestrator()
        
        # O mock do ModelManager vai devolver um dicionário de datasets vazio
        mock_manager_instance = MagicMock()
        mock_manager_instance.load_all_datasets.return_value = {}
        mock_model_manager_class.return_value = mock_manager_instance
        
        # Executar (Não pode rebentar)
        orchestrator.run()
        
        # Como está vazio, o pipeline dá "continue" e nunca chama as funções abaixo:
        mock_manager_instance.generate_splits.assert_not_called()

    @patch("data_pipeline.modeling.ModelManager")
    def test_run_full_flow(self, mock_model_manager_class):
        """Testa se o método run chama a orquestração completa para hourly e daily."""
        orchestrator = PipelineOrchestrator()
        
        # Substituímos os métodos pesados por Mocks
        orchestrator._precalculate_splits = MagicMock()
        orchestrator._evaluate_and_save_model = MagicMock()
        
        # Forçamos o load_datasets a devolver algo para ele não dar 'continue'
        mock_manager_instance = MagicMock()
        mock_manager_instance.load_all_datasets.return_value = {"full": "dataset_falso"}
        mock_model_manager_class.return_value = mock_manager_instance
        
        # Executar
        orchestrator.run()
        
        # Verifica se o ModelManager foi instanciado para "hourly" e "daily"
        assert mock_model_manager_class.call_count == 2
        
        # Como há hourly e daily, e 2 tipos de modelos (baseline, flexible),
        # a função de avaliação e gravação tem de ter sido chamada exatamente 4 vezes!
        assert orchestrator._evaluate_and_save_model.call_count == 4