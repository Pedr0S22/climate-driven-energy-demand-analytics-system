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

            # Ajuste de caminho se estiver a correr fora do container ou num root diferente
            # No docker, o WORKDIR é /app, e os caminhos relativos na DB são 'models/...'
            if not model_path.is_absolute():
                # Tentar encontrar no diretório de trabalho atual
                potential_path = Path.cwd() / model_path
                if not potential_path.exists():
                    # Tentar encontrar relativo ao root da app
                    potential_path = Path(__file__).resolve().parent.parent.parent.parent / model_path

                if potential_path.exists():
                    model_path = potential_path

            if not model_path.exists():
                logger.error(f"Modelo não encontrado no caminho: {model_path}")
                return False

            logger.info(f"Carregando modelo {freq} de {model_path}")

            # Carregar modelo real
            self._models[freq] = joblib.load(model_path)

            # Carregar scaler real
            scaler_path = model_path.parent / f"scaler_{freq}.joblib"
            if scaler_path.exists():
                self._scalers[freq] = joblib.load(scaler_path)
                logger.info(f"Scaler carregado para {freq}")

            # Carregar PCA real se necessário
            if model_record.dataset_selected == "pca":
                pca_path = model_path.parent / f"pca_{freq}.joblib"
                if pca_path.exists():
                    self._pca[freq] = joblib.load(pca_path)
                    logger.info(f"PCA carregado para {freq}")

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

    def predict(self, frequency: str, features: np.ndarray) -> float:
        model = self.get_model(frequency)
        if model is None:
            logger.error(f"Predição falhou: Nenhum modelo em memória para '{frequency}'")
            logger.info(f"Modelos disponíveis em memória: {list(self._models.keys())}")
            raise ValueError(f"Nenhum modelo ativo carregado em memória para '{frequency}'")

        # Converter dict para array se necessário
        if isinstance(features, dict):
            features = np.array(list(features.values())).reshape(1, -1)

        # Garantir 2D
        if features.ndim == 1:
            features = features.reshape(1, -1)

        # Pipeline
        transformed = features

        # 1. Scaler
        scaler = self.get_scaler(frequency)
        if scaler:
            transformed = scaler.transform(transformed)

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
