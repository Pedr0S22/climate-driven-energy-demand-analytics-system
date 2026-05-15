import logging
from datetime import timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import and_
from sqlalchemy.orm import Session

from src.api.models.model import Model
from src.api.services.inference_engine import get_inference_engine

logger = logging.getLogger(__name__)


class PredictionService:
    @staticmethod
    def get_realtime_prediction(
            db: Session,
            frequency: str,
            historical_points: int,
            predicted_points: int) -> dict:
        """
        Gera uma predição autoregressiva baseada nos dados real-time mais recentes.
        """
        # 1. Obter Modelo Ativo da DB
        active_model = db.query(Model).filter(
            and_(
                Model.model_pred_type == frequency,
                Model.is_active)).first()

        if not active_model:
            logger.error(f"Nenhum modelo ativo encontrado para {frequency}")
            raise ValueError(
                f"Nenhum modelo ativo encontrado para a frequência '{frequency}'")

        # 2. Carregar Dados Engineered Real-time
        app_root = Path(__file__).resolve().parent.parent.parent.parent
        ds_type = active_model.dataset_selected

        # FIX: Para modelos PCA, carregamos o dataset 'full' (raw features).
        ds_type_to_load = "full" if ds_type == "pca" else ds_type

        data_path = (
            app_root
            / "data"
            / "processed"
            / "feat-engineering"
            / "real-time"
            / f"realtime_{frequency}_{ds_type_to_load}.csv"
        )

        if not data_path.exists():
            data_path = (
                app_root /
                "data" /
                "processed" /
                "feat-engineering" /
                f"realtime_{frequency}_{ds_type_to_load}.csv")
            if not data_path.exists():
                raise FileNotFoundError(
                    f"Dados real-time para {frequency} não disponíveis.")

        df = pd.read_csv(data_path)
        df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
        df = df.sort_values("datetime")

        if df.empty:
            raise ValueError("O dataset real-time está vazio.")

        # 3. Extrair Valores Históricos
        target_col = "Load_MWh" if frequency == "daily" else "Load_MW"
        hist_df = df.tail(historical_points)
        historical_load = hist_df[target_col].tolist()
        historical_timestamps = hist_df["datetime"].tolist()

        # 4. Preparação para Loop Autoregressivo
        last_row = df.iloc[-1].to_dict()
        current_features = last_row.copy()
        predictions = []
        prediction_timestamps = []
        last_time = last_row["datetime"]
        delta = timedelta(
            days=1) if frequency == "daily" else timedelta(
            hours=1)
        engine = get_inference_engine()

        # 5. Loop Autoregressivo
        for i in range(predicted_points):
            # FIX: Remove metadata and target from features before prediction
            # to match scaler/model expected input
            predict_features = current_features.copy()
            predict_features.pop("datetime", None)
            predict_features.pop("Load_MW", None)
            predict_features.pop("Load_MWh", None)

            pred_value = engine.predict(frequency, predict_features)
            predictions.append(pred_value)
            next_time = last_time + delta
            prediction_timestamps.append(next_time)

            # Atualizar lags
            current_features["L1_Load"] = pred_value
            if frequency == "hourly":
                if i >= 23:
                    current_features["L24_Load"] = predictions[i - 23]
                if i >= 167:
                    current_features["L168_Load"] = predictions[i - 167]
            else:
                if i >= 6:
                    current_features["L7_Load"] = predictions[i - 6]
                if i >= 27:
                    current_features["L28_Load"] = predictions[i - 27]

            # Atualizar tempo
            current_features["datetime"] = next_time
            if frequency == "hourly":
                current_features["hour"] = next_time.hour
            current_features["day_of_week"] = next_time.weekday()
            current_features["month"] = next_time.month
            current_features["year"] = next_time.year
            current_features["season"] = (next_time.month % 12 // 3) + 1
            last_time = next_time

        return {
            "status": 200,
            "historical_load": historical_load,
            "load_predicted": predictions,
            "timestamps": [
                t.isoformat() for t in (
                    historical_timestamps +
                    prediction_timestamps)],
            "top2_drivers": active_model.top2_drivers.split(", "),
        }
