import logging
import re
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
from scipy.stats import f_oneway, friedmanchisquare, kruskal, shapiro
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from pandas.tseries.offsets import DateOffset
import psycopg2 

# =======================================
# CONFIGURATION
# =======================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

class StatisticalEvaluator:
    """Handles the statistical testing logic for model selection."""
    
    @staticmethod
    def test_normality(data_groups, alpha=0.05):
        """Tests if all groups are normally distributed using Shapiro-Wilk."""
        for _ , data in data_groups.items():
            # If standard deviation is 0, shapiro fails. 
            if np.std(data) == 0:
                return False
            stat, p_val = shapiro(data)
            if p_val < alpha:
                return False  # Not normal
        return True

    @staticmethod
    def select_best_dataset(results_dict):
        """
        Implements Rules 6.1, 6.2, 6.3:
        Selects best dataset based on 30-partition RMSE using Shapiro -> ANOVA/Friedman.
        """
        # results_dict format: {dataset_name: {'rmse': [30 values], 'r2': [30 values], 'mae': [30 values]}}
        datasets = list(results_dict.keys())
        rmse_groups = {ds: results_dict[ds]['rmse'] for ds in datasets}
        
        all_normal = StatisticalEvaluator.test_normality(rmse_groups)
        arrays = [rmse_groups[ds] for ds in datasets]
        
        is_diff = False
        if all_normal:
            # Note: Scipy doesn't have native Repeated Measures ANOVA, using standard oneway as approximation
            stat, p_val = f_oneway(*arrays)
            test_used = "ANOVA"
        else:
            stat, p_val = friedmanchisquare(*arrays)
            test_used = "Friedman"
            
        if p_val < 0.05:
            is_diff = True
            
        # Select best by mean RMSE -> R2 -> MAE
        best_ds = None
        best_metrics = {'rmse': float('inf'), 'r2': float('-inf'), 'mae': float('inf')}
        
        for ds in datasets:
            mean_rmse = np.mean(results_dict[ds]['rmse'])
            mean_r2 = np.mean(results_dict[ds]['r2'])
            mean_mae = np.mean(results_dict[ds]['mae'])
            
            if mean_rmse < best_metrics['rmse']:
                best_ds = ds
                best_metrics = {'rmse': mean_rmse, 'r2': mean_r2, 'mae': mean_mae}
            elif mean_rmse == best_metrics['rmse']:
                if mean_r2 > best_metrics['r2']:
                    best_ds = ds
                    best_metrics = {'rmse': mean_rmse, 'r2': mean_r2, 'mae': mean_mae}
                elif mean_r2 == best_metrics['r2'] and mean_mae < best_metrics['mae']:
                    best_ds = ds
                    best_metrics = {'rmse': mean_rmse, 'r2': mean_r2, 'mae': mean_mae}
                    
        if not is_diff:
            logger.info(f"    -> {test_used} showed NO stat diff (p={p_val:.4e}). Choosing {best_ds} by raw means.")
        else:
            logger.info(f"    -> {test_used} showed stat diff (p={p_val:.4e}). Selected {best_ds}.")
        return best_ds, best_metrics

    @staticmethod
    def select_best_strategy(strategy_results):
        """
        Implements Rules 7.1, 7.2, 7.3:
        Selects best split strategy using Shapiro -> ANOVA/Kruskal-Wallis.
        """
        strategies = list(strategy_results.keys())
        rmse_groups = {strat: strategy_results[strat]['metrics']['rmse'] for strat in strategies}
        
        all_normal = StatisticalEvaluator.test_normality(rmse_groups)
        arrays = [rmse_groups[strat] for strat in strategies]
        
        if all_normal:
            stat, p_val = f_oneway(*arrays)
            test_used = "ANOVA"
        else:
            stat, p_val = kruskal(*arrays)
            test_used = "Kruskal-Wallis"
            
        best_strat = None
        best_metrics = {'rmse': float('inf'), 'r2': float('-inf'), 'mae': float('inf')}
        
        for strat in strategies:
            mean_rmse = np.mean(strategy_results[strat]['metrics']['rmse'])
            mean_r2 = np.mean(strategy_results[strat]['metrics']['r2'])
            mean_mae = np.mean(strategy_results[strat]['metrics']['mae'])
            
            # 1. Ganha pelo RMSE
            if mean_rmse < best_metrics['rmse']:
                best_strat = strat
                best_metrics = {'rmse': mean_rmse, 'r2': mean_r2, 'mae': mean_mae}
            
            # 2. Empate no RMSE -> Ganha pelo melhor R2
            elif mean_rmse == best_metrics['rmse']:
                if mean_r2 > best_metrics['r2']:
                    best_strat = strat
                    best_metrics = {'rmse': mean_rmse, 'r2': mean_r2, 'mae': mean_mae}
                
                # 3. Empate no RMSE e R2 -> Ganha pelo menor MAE
                elif mean_r2 == best_metrics['r2']:
                    if mean_mae < best_metrics['mae']:
                        best_strat = strat
                        best_metrics = {'rmse': mean_rmse, 'r2': mean_r2, 'mae': mean_mae}
                    
        logger.info(f"  => {test_used} evaluation (p={p_val:.4e}). Winning Strategy: {best_strat}")
        return best_strat


class ModelManager:
    def __init__(self, frequency="hourly"):
        self.frequency = frequency.lower()
        self.target_col = "Load_MWh" if self.frequency == "daily" else "Load_MW"
        self.app_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = self.app_root / "data" / "processed" / "feat-engineering"
        self.models_dir = self.app_root / "models" / self.frequency
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.n_partitions = 2

    def load_all_datasets(self) -> dict:
        datasets = {}
        for ds_type in ["full", "selected", "pca"]:
            file_path = self.data_dir / f"features_{self.frequency}_{ds_type}.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                if "datetime" in df.columns:
                    df["datetime"] = pd.to_datetime(df["datetime"])
                datasets[ds_type] = df
        return datasets



    def generate_splits(self, df, strategy="fixed_rolling"):
        """
        Gera 30 splits rigorosos para avaliação estatística.
        Estrutura: [Treino (1 ano)] -> [Gap (1 ano)] -> [Teste (1 ano)]
        Configurado para 5 anos de dados com salto semanal.
        """
        splits = []
        # 1. Garantir integridade temporal
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        current_test_end = df['datetime'].max()
        start_date = df['datetime'].min()
        
        # 2. Definição dos Offsets Rigorosos (Lida com anos bissextos)
        one_year = DateOffset(years=1)
        two_years = DateOffset(years=2) # Ponto onde o treino termina (1 ano de Gap + 1 ano de Teste)
        

        step_offset = DateOffset(months=1)

        for i in range(self.n_partitions):
            # Definição do bloco de Teste (Sempre 1 ano)
            current_test_start = current_test_end - one_year
            
            # Definição do fim do Treino (Respeitando o Gap de 1 ano)
            training_end_cutoff = current_test_end - two_years
            
            # Definição do início do Treino baseada na estratégia
            if strategy == "fixed_rolling":
                # Treino de tamanho fixo (1 ano)
                training_start_cutoff = training_end_cutoff - one_year
            else: 
                # Expanding & Nested: Treino acumulado desde o início dos tempos
                training_start_cutoff = start_date

            # 4. Verificação de consistência: temos dados suficientes para esta janela de 3 anos?
            if training_start_cutoff < start_date:
                if i < self.n_partitions:
                    logger.warning(f"Aviso: Dados insuficientes para {self.n_partitions} folds.")
                break
                
            # 5. Extração dos índices
            train_mask = (df['datetime'] >= training_start_cutoff) & (df['datetime'] < training_end_cutoff)
            test_mask = (df['datetime'] >= current_test_start) & (df['datetime'] < current_test_end)
            
            train_idx = df.index[train_mask].to_numpy()
            test_idx = df.index[test_mask].to_numpy()
            
            # Só adiciona se o fold for válido (tiver dados em ambos)
            if len(train_idx) > 0 and len(test_idx) > 0:
                splits.insert(0, (train_idx, test_idx))
                
            # 6. Desliza a janela para o passado
            current_test_end = current_test_end - step_offset

        return splits
        
    def _get_next_version(self, model_prefix):
        """Implements Rule 8: Versioning format LR_vx, RF_vx."""
        existing_files = list(self.models_dir.glob(f"{model_prefix}_v*.joblib"))
        if not existing_files:
            return 1
        versions = []
        for f in existing_files:
            match = re.search(r'_v(\d+)\.joblib', f.name)
            if match:
                versions.append(int(match.group(1)))
        return max(versions) + 1 if versions else 1

    def train_baseline(self, X_train, y_train):
        model = LinearRegression()
        model.fit(X_train, y_train)
        return model



    def train_flexible(self, X_train, y_train, strategy):
        """
        Treina o modelo RandomForest com otimização Optuna.
        Utiliza a coluna 'datetime' para criar um Gap de segurança de 1 ano
        durante a validação interna, removendo-a antes do treino real.
        """
        
        def objective(trial):
            # 1. Sugestão de Hiperparâmetros
            n_estimators = trial.suggest_int('n_estimators', 20, 100)
            max_depth = trial.suggest_int('max_depth', 5, 15)
            
            model = RandomForestRegressor(
                n_estimators=n_estimators, 
                max_depth=max_depth, 
                random_state=42, 
                n_jobs=-1
            )
            
            # 2. Extração das datas para lógica de Gap
            # Assume-se que 'datetime' está no X_train enviado pelo pipeline
            dates = pd.to_datetime(X_train['datetime'])
            val_end = dates.max()
            one_year = DateOffset(years=1)
            two_years = DateOffset(years=2) # 1 ano de teste + 1 ano de Gap

            if strategy == "nested":
                # No modo Nested, o Optuna faz uma validação cruzada interna rigorosa
                scores = []
                curr_val_end = val_end
                
                # Fazemos 2 sub-folds internos para média de erro
                for _ in range(2):
                    curr_val_start = curr_val_end - one_year
                    curr_train_end = curr_val_end - two_years
                    
                    if curr_train_end <= dates.min():
                        break
                    
                    # Máscaras de tempo
                    train_mask = dates < curr_train_end
                    val_mask = (dates >= curr_val_start) & (dates < curr_val_end)
                    
                    # EXTRAÇÃO E LIMPEZA: Removemos 'datetime' antes do fit
                    X_tr = X_train[train_mask].drop(columns=['datetime'])
                    y_tr = y_train[train_mask]
                    X_va = X_train[val_mask].drop(columns=['datetime'])
                    y_va = y_train[val_mask]
                    
                    if len(X_tr) > 0 and len(X_va) > 0:
                        model.fit(X_tr, y_tr)
                        preds = model.predict(X_va)
                        scores.append(np.sqrt(mean_squared_error(y_va, preds)))
                    
                    # Salto trimestral para o próximo fold interno
                    curr_val_end = curr_val_end - DateOffset(months=3)
                    
                return np.mean(scores) if scores else float('inf')
            
            else:
                # Estratégia Expanding/Fixed: 1 único split interno com Gap
                val_start = val_end - one_year
                train_end = val_end - two_years
                
                if train_end <= dates.min():
                    # Fallback simples se o histórico for insuficiente para o Gap
                    split_idx = int(len(X_train) * 0.8)
                    X_tr = X_train.iloc[:split_idx].drop(columns=['datetime'])
                    X_va = X_train.iloc[split_idx:].drop(columns=['datetime'])
                    y_tr, y_va = y_train.iloc[:split_idx], y_train.iloc[split_idx:]
                else:
                    train_mask = dates < train_end
                    val_mask = dates >= val_start
                    
                    X_tr = X_train[train_mask].drop(columns=['datetime'])
                    y_tr = y_train[train_mask]
                    X_va = X_train[val_mask].drop(columns=['datetime'])
                    y_va = y_train[val_mask]

                model.fit(X_tr, y_tr)
                preds = model.predict(X_va)
                return np.sqrt(mean_squared_error(y_va, preds))

        # 3. Execução da Otimização
        study = optuna.create_study(direction="minimize")
        # n_trials=30 para garantir uma busca sólida
        study.optimize(objective, n_trials=30)
        
        # 4. Treino Final do Vencedor
        best_model = RandomForestRegressor(**study.best_params, random_state=42, n_jobs=-1)
        
        # LIMPEZA FINAL: Remover o datetime para o treino que será guardado em disco
        X_final = X_train.drop(columns=['datetime']) if 'datetime' in X_train.columns else X_train
        best_model.fit(X_final, y_train)
        
        return best_model


class DatabaseManager:
    """Gere as operações de base de dados (PostgreSQL) para o registo de modelos."""
    def __init__(self, db_config):
        self.db_config = db_config

    def save_model_metrics(self, model_type, file_path, rmse, mae, r2):
        """Guarda os metadados do modelo na base de dados."""
        if not self.db_config:
            logger.warning("Nenhuma configuração de base de dados fornecida. Registo ignorado.")
            return

        query = """
            INSERT INTO model (model_type, model_server_relative_path, rmse, mae, r2)
            VALUES (%s, %s, %s, %s, %s);
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Converte o path para string caso seja um objeto Path do pathlib
                    cur.execute(query, (model_type, str(file_path), float(rmse), float(mae), float(r2)))
            logger.info("✅ Metadados do modelo guardados na base de dados com sucesso.")
        except Exception as e:
            logger.error(f"❌ Erro ao guardar na base de dados: {e}")


class PipelineOrchestrator:
    """Orquestra a execução modular do pipeline de avaliação e treino."""
    def __init__(self, db_config=None):
        self.evaluator = StatisticalEvaluator()
        self.db_manager = DatabaseManager(db_config)

    def run(self):
        overall_start = time.time()
        
        for freq in ["hourly", "daily"]:
            logger.info(f"\n{'='*60}\nSTARTING MASSIVE PIPELINE FOR: {freq.upper()}\n{'='*60}")
            self.manager = ModelManager(frequency=freq)
            datasets = self.manager.load_all_datasets()
            
            if not datasets:
                logger.warning(f"No datasets found for {freq}. Skipping.")
                continue
                
            splits_by_strategy = self._precalculate_splits(datasets)
            
            for model_type in ["baseline", "flexible"]:
                self._evaluate_and_save_model(model_type, freq, datasets, splits_by_strategy)

        total_duration = time.time() - overall_start
        logger.info(f"\nTotal execution time: {total_duration/60:.2f} minutes")

    def _precalculate_splits(self, datasets):
        """Isola a lógica de pré-cálculo dos splits temporais."""
        logger.info("Pre-calculating strict temporal splits...")
        precalculated_splits = {}
        for strategy in ["expanding", "fixed_rolling", "nested"]:
            precalculated_splits[strategy] = {}
            for ds_name, df in datasets.items():
                precalculated_splits[strategy][ds_name] = self.manager.generate_splits(df, strategy=strategy)
        return precalculated_splits

    def _evaluate_and_save_model(self, model_type, freq, datasets, splits_by_strategy):
        """Gere a avaliação de um tipo de modelo específico e o respetivo salvamento."""
        logger.info(f"\n--- Evaluating Model: {model_type.upper()} ---")
        strategy_results = {}
        if model_type == "baseline":
            strategies_to_run = ["expanding", "fixed_rolling"]
        else:
            strategies_to_run = ["expanding", "fixed_rolling", "nested"]

        # 1. Avaliar todas as estratégias
        for strategy in strategies_to_run:
            strategy_results[strategy] = self._run_strategy_loops(model_type, strategy, datasets, splits_by_strategy)
        
        # 2. Encontrar a melhor estratégia
        best_strat = self.evaluator.select_best_strategy(strategy_results)
        vencedora_metrics = strategy_results[best_strat]['metrics']
        
        # 3. Encontrar o melhor fold individual
        melhor_idx = self._find_best_fold_index(vencedora_metrics)
        best_final_model = vencedora_metrics['models'][melhor_idx]
        
        # Métricas do melhor modelo
        best_rmse = vencedora_metrics['rmse'][melhor_idx]
        best_r2 = vencedora_metrics['r2'][melhor_idx]
        best_mae = vencedora_metrics['mae'][melhor_idx]

        logger.info(f"  => [Best Individual Fold: #{melhor_idx}] RMSE: {best_rmse:.2f} | R2: {best_r2:.4f} | MAE: {best_mae:.2f}")

        # ---------------------------------------------------------
        # 4. GUARDAR NO DISCO E NA BASE DE DADOS
        # ---------------------------------------------------------
        prefix = "LR" if model_type == "baseline" else "RF"
        version = self.manager._get_next_version(prefix)
        file_name = f"{prefix}_v{version}.joblib"

        save_path = self.manager.models_dir / file_name
        joblib.dump(best_final_model, save_path)
        
        logger.info(f"✅ WINNER for {model_type.upper()} ({freq}): Strategy='{best_strat}',"
                    f"Dataset='{strategy_results[best_strat]['dataset']}'")
        logger.info(f"✅ Ficheiro guardado fisicamente em: {save_path}")

        # B. Caminho Relativo (A partir da raiz 'energy/' para ir para a Base de Dados)
        # Vai gerar algo como: "models/hourly/RF_v1.joblib"
        caminho_relativo = f"models/{freq}/{file_name}"

        # C. Guardar na BD com o caminho correto
        db_model_name = "Linear Regression" if model_type == "baseline" else "Random Forest"
        self.db_manager.save_model_metrics(
            model_type=db_model_name,
            file_path=caminho_relativo,  # <-- O caminho limpo vai aqui!
            rmse=best_rmse,
            mae=best_mae,
            r2=best_r2
        )
    def _run_strategy_loops(self, model_type, strategy, datasets, splits_by_strategy):
        """Executa os loops de treino para uma estratégia específica sobre os datasets."""
        logger.info(f"  Strategy: {strategy}")
        dataset_results = {ds: {'rmse': [], 'r2': [], 'mae': [], 'models': []} for ds in datasets.keys()}
        
        for ds_name, df in datasets.items():
            X = df.drop(columns=[self.manager.target_col])
            y = df[self.manager.target_col]
            splits = splits_by_strategy[strategy][ds_name]
            
            for train_idx, test_idx in splits:
                X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
                X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]
                
                if model_type == "baseline":
                    X_train_b = X_train.drop(columns=['datetime']) if 'datetime' in X_train.columns else X_train
                    model = self.manager.train_baseline(X_train_b, y_train)
                else:
                    model = self.manager.train_flexible(X_train, y_train, strategy)
                    
                X_test = X_test.drop(columns=['datetime']) if 'datetime' in X_test.columns else X_test
                y_pred = model.predict(X_test)
                
                dataset_results[ds_name]['rmse'].append(np.sqrt(mean_squared_error(y_test, y_pred)))
                dataset_results[ds_name]['r2'].append(r2_score(y_test, y_pred))
                dataset_results[ds_name]['mae'].append(mean_absolute_error(y_test, y_pred))
                dataset_results[ds_name]['models'].append(model)
        
        # Avalia qual foi o melhor dataset para esta estratégia
        best_ds, metrics = self.evaluator.select_best_dataset(dataset_results)
        logger.info(f"    [Métricas Dataset {best_ds.upper()}] RMSE Médio: {metrics['rmse']:.2f}")
        
        return {'dataset': best_ds, 'metrics': dataset_results[best_ds]}

    def _find_best_fold_index(self, vencedora_metrics):
        """Lógica de desempate para encontrar o melhor fold individual da estratégia vencedora."""
        melhor_idx = 0
        for i in range(1, len(vencedora_metrics['rmse'])):
            curr_rmse = vencedora_metrics['rmse'][i]
            best_rmse = vencedora_metrics['rmse'][melhor_idx]
            
            if curr_rmse < best_rmse:
                melhor_idx = i
            elif curr_rmse == best_rmse:
                if vencedora_metrics['r2'][i] > vencedora_metrics['r2'][melhor_idx]:
                    melhor_idx = i
                elif vencedora_metrics['r2'][i] == vencedora_metrics['r2'][melhor_idx]:
                    if vencedora_metrics['mae'][i] < vencedora_metrics['mae'][melhor_idx]:
                        melhor_idx = i
        return melhor_idx


if __name__ == "__main__":

    DB_CONFIG = {
        "dbname": "energy_db",
        "user": "piacd_energy",
        "password": "postgres_Piacd_energy",
        "host": "localhost", # (Lê a nota importante abaixo sobre o host)
        "port": "5433"
    }
    
    # Inicia a orquestração do pipeline de forma limpa
    orchestrator = PipelineOrchestrator(db_config=DB_CONFIG)
    orchestrator.run()