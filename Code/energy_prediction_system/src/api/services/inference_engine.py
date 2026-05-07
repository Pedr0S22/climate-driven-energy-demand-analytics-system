import logging
import threading
from typing import Optional, Any, Dict
import numpy as np
import joblib
from pathlib import Path

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

        self._models: Dict[str, Any] = {}       # frequency -> modelo
        self._scalers: Dict[str, Any] = {}      # frequency -> scaler
        self._pca: Dict[str, Any] = {}          # frequency -> PCA

        logger.info("InferenceEngine inicializado")

    def load_active_model(self, model_record) -> bool:
        freq = model_record.model_pred_type

        try:
            model_path = Path(model_record.model_server_relative_path)

            if not model_path.exists():
                raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

            # Carregar modelo real
            self._models[freq] = joblib.load(model_path)

            # Carregar scaler real
            scaler_path = model_path.parent / f"scaler_{freq}.joblib"
            if scaler_path.exists():
                self._scalers[freq] = joblib.load(scaler_path)  # ✅ Objeto real

            # Carregar PCA real se necessário
            if model_record.dataset_selected == "pca":
                pca_path = model_path.parent / f"pca_{freq}.joblib"
                if pca_path.exists():
                    self._pca[freq] = joblib.load(pca_path)  # ✅ Objeto real

            return True

        except Exception as e:
            logger.error(f"Erro ao carregar modelo {freq}: {e}")
            return False

    def get_model(self, frequency: str) -> Optional[Any]:
        """Retorna o modelo carregado para a frequência"""
        return self._models.get(frequency)

    def get_scaler(self, frequency: str) -> Optional[Any]:
        """Retorna o scaler para a frequência"""
        return self._scalers.get(frequency)

    def get_pca(self, frequency: str) -> Optional[Any]:
        """Retorna o PCA para a frequência"""
        return self._pca.get(frequency)

    def predict(self, frequency: str, features: np.ndarray) -> float:
        model = self.get_model(frequency)
        if model is None:
            raise ValueError(f"Nenhum modelo ativo para '{frequency}'")

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
