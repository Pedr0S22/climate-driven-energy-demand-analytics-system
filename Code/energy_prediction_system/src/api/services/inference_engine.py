import logging
import threading
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
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

            # Ajuste de caminho se estiver a correr fora do container ou num
            # root diferente
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

            # Apenas carregar Scaler e PCA se o modelo os usar (dataset =
            # 'pca')
            if model_record.dataset_selected == "pca":
                # Carregar scaler real
                scaler_name = f"scaler_{freq}.joblib"
                scaler_path = model_path.parent / scaler_name
                if not scaler_path.exists():
                    scaler_path = feat_eng_dir / scaler_name

                if scaler_path.exists():
                    self._scalers[freq] = joblib.load(scaler_path)
                    logger.info(
                        f"Scaler carregado para {freq} de {scaler_path}")

                # Carregar PCA real se necessário
                pca_name = f"pca_{freq}.joblib"
                pca_path = model_path.parent / pca_name
                if not pca_path.exists():
                    pca_path = feat_eng_dir / pca_name

                if pca_path.exists():
                    self._pca[freq] = joblib.load(pca_path)
                    logger.info(f"PCA carregado para {freq} de {pca_path}")
            else:
                # Limpar estado anterior se houver
                self._scalers.pop(freq, None)
                self._pca.pop(freq, None)

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

        logger.info(
            f"InferenceEngine: {count} modelos carregados com sucesso na inicialização.")

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
            logger.error(
                f"Predição falhou: Nenhum modelo em memória para '{frequency}'")
            raise ValueError(
                f"Nenhum modelo ativo carregado em memória para '{frequency}'")

        scaler = self.get_scaler(frequency)
        pca = self.get_pca(frequency)

        # 1. Determinar nomes das features e preparar entrada
        feature_names = self._determine_feature_names(model, scaler)
        transformed = self._prepare_features(features, feature_names)

        # 2. Aplicar transformações (Scaler e PCA)
        transformed = self._apply_scaling(transformed, scaler)
        transformed = self._apply_pca(transformed, pca)

        # 3. Executar predição
        prediction = model.predict(transformed)

        if isinstance(prediction, np.ndarray):
            return float(prediction[0])
        return float(prediction)

    def _determine_feature_names(
            self,
            model: Any,
            scaler: Any) -> list[str] | None:
        """Determina nomes das features esperadas (lógica original)."""
        if scaler and hasattr(scaler, "feature_names_in_"):
            return scaler.feature_names_in_.tolist()
        elif hasattr(model, "feature_names_in_"):
            return model.feature_names_in_.tolist()
        return None

    def _prepare_features(
            self,
            features: Any,
            feature_names: list[str] | None) -> Any:
        """Converte e alinha a entrada (lógica original)."""
        if isinstance(features, dict):
            if feature_names:
                X_dict = {f: features.get(f, 0) for f in feature_names}
                return pd.DataFrame([X_dict])
            return pd.DataFrame([features])
        elif isinstance(features, pd.DataFrame):
            if feature_names:
                return features.reindex(columns=feature_names, fill_value=0)
            return features.copy()
        else:
            transformed = np.array(features)
            if transformed.ndim == 1:
                transformed = transformed.reshape(1, -1)
            if feature_names and transformed.shape[1] == len(feature_names):
                transformed = pd.DataFrame(transformed, columns=feature_names)
            return transformed

    def _apply_scaling(self, transformed: Any, scaler: Any) -> Any:
        """Aplica scaling se disponível (lógica original)."""
        if not scaler:
            return transformed
        try:
            expected_scaler_feats = len(
                scaler.feature_names_in_) if hasattr(
                scaler, "feature_names_in_") else None
            actual_feats = transformed.shape[1]

            if expected_scaler_feats and actual_feats != expected_scaler_feats:
                pass
            else:
                scaled_array = scaler.transform(transformed)
                if hasattr(scaler, "feature_names_in_"):
                    transformed = pd.DataFrame(
                        scaled_array, columns=scaler.feature_names_in_)
                else:
                    transformed = scaled_array
        except ValueError:
            pass
        return transformed

    def _apply_pca(self, transformed: Any, pca: Any) -> Any:
        """Aplica PCA se disponível (lógica original)."""
        if not pca:
            return transformed
        try:
            pca_array = pca.transform(transformed)
            transformed = pd.DataFrame(
                pca_array, columns=[
                    f"PCA_{i}" for i in range(
                        pca_array.shape[1])])
        except ValueError:
            pass
        return transformed


def get_inference_engine() -> InferenceEngine:
    """Retorna a instância singleton do InferenceEngine"""
    return InferenceEngine()
