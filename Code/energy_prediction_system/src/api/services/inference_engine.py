import logging
import threading
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class InferenceEngine:
    """
    Singleton que gere os modelos ML em memória.
    Mantém modelos, scalers e PCA components carregados para predições rápidas.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._models: dict[str, Any] = {}  # frequency -> modelo
        self._scalers: dict[str, Any] = {}  # frequency -> scaler
        self._pca: dict[str, Any] = {}  # frequency -> PCA

        logger.info("InferenceEngine inicializado")

    def load_active_model(self, model_record) -> bool:
        freq = model_record.model_pred_type

        try:
            model_path = Path(model_record.model_server_relative_path)
            app_root = Path(__file__).resolve().parent.parent.parent.parent

            # Ajuste de caminho se estiver a correr fora do container ou num root diferente
            if not model_path.is_absolute():
                potential_paths = [
                    Path.cwd() / model_path,
                    app_root / model_path,
                ]
                for p in potential_paths:
                    if p.exists():
                        model_path = p
                        break

            if not model_path.exists():
                logger.error(f"Modelo não encontrado no caminho: {model_path}")
                return False

            logger.info(f"Carregando modelo {freq} de {model_path}")
            self._models[freq] = joblib.load(model_path)

            # Localização de Transformers (Scaler/PCA)
            # Prioridade 1: Mesma pasta do modelo
            # Prioridade 2: Pasta central models/feat-engineering/
            feat_eng_dir = app_root / "models" / "feat-engineering"

            # Carregar scaler real
            scaler_name = f"scaler_{freq}.joblib"
            scaler_path = model_path.parent / scaler_name
            if not scaler_path.exists():
                scaler_path = feat_eng_dir / scaler_name

            if scaler_path.exists():
                self._scalers[freq] = joblib.load(scaler_path)
                logger.info(f"Scaler carregado para {freq} de {scaler_path}")

            # Carregar PCA real se necessário
            if model_record.dataset_selected == "pca":
                pca_name = f"pca_{freq}.joblib"
                pca_path = model_path.parent / pca_name
                if not pca_path.exists():
                    pca_path = feat_eng_dir / pca_name

                if pca_path.exists():
                    self._pca[freq] = joblib.load(pca_path)
                    logger.info(f"PCA carregado para {freq} de {pca_path}")

            return True

        except Exception as e:
            logger.error(f"Erro ao carregar modelo {freq}: {e}")
            return False

    def load_all_active_models(self, db: Session):
        """Carrega todos os modelos que estão marcados como ativos na DB"""
        from src.api.models.model import Model

        active_models = db.query(Model).filter(Model.is_active).all()

        count = 0
        for m in active_models:
            if self.load_active_model(m):
                count += 1

        logger.info(f"InferenceEngine: {count} modelos carregados com sucesso na inicialização.")

    def get_model(self, frequency: str) -> Any | None:
        """Retorna o modelo carregado para a frequência"""
        return self._models.get(frequency)

    def get_scaler(self, frequency: str) -> Any | None:
        """Retorna o scaler para a frequência"""
        return self._scalers.get(frequency)

    def get_pca(self, frequency: str) -> Any | None:
        """Retorna o PCA para a frequência"""
        return self._pca.get(frequency)

    def predict(self, frequency: str, features: Any) -> float:
        model = self.get_model(frequency)
        if model is None:
            logger.error(f"Predição falhou: Nenhum modelo em memória para '{frequency}'")
            raise ValueError(f"Nenhum modelo ativo carregado em memória para '{frequency}'")

        # Converter dict para array respeitando a ordem das colunas do modelo/scaler
        if isinstance(features, dict):
            # Tentar obter a ordem das colunas do modelo ou do scaler
            feature_names = None
            if hasattr(model, "feature_names_in_"):
                feature_names = model.feature_names_in_
            elif self.get_scaler(frequency) and hasattr(self.get_scaler(frequency), "feature_names_in_"):
                feature_names = self.get_scaler(frequency).feature_names_in_

            if feature_names is not None:
                try:
                    features_array = np.array([features[name] for name in feature_names]).reshape(1, -1)
                except KeyError as e:
                    logger.error(f"Dicionário de features incompleto. Falta: {e}")
                    # Fallback para o comportamento anterior se falhar, mas logar aviso
                    features_array = np.array(list(features.values())).reshape(1, -1)
            else:
                # Se não houver informação de nomes, usamos a ordem atual das chaves (frágil)
                features_array = np.array(list(features.values())).reshape(1, -1)
        else:
            features_array = np.array(features)

        # Garantir 2D
        if features_array.ndim == 1:
            features_array = features_array.reshape(1, -1)

        # Pipeline
        transformed = features_array

        # 1. Scaler
        scaler = self.get_scaler(frequency)
        if scaler:
            try:
                transformed = scaler.transform(transformed)
            except ValueError as e:
                logger.warning(f"Aviso de Scaling para {frequency}: {e}. Continuando sem scaling.")

        # 2. PCA
        pca = self.get_pca(frequency)
        if pca:
            transformed = pca.transform(transformed)

        # 3. Modelo
        prediction = model.predict(transformed)

        if isinstance(prediction, np.ndarray):
            return float(prediction[0])
        return float(prediction)


def get_inference_engine() -> InferenceEngine:
    """Retorna a instância singleton do InferenceEngine"""
    return InferenceEngine()
