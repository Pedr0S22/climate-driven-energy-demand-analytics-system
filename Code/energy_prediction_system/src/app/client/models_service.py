# app/client/models_service.py
import logging
from app.client.api_client import APIClient

logger = logging.getLogger(__name__)


class ModelsService:
    def __init__(self):
        self.client = APIClient()

    def get_all_models(self):
        endpoint = "/models/"
        try:
            response = self.client.get(endpoint)
            if response.status_code == 200:
                return response.json(), 200
            else:
                logger.error(f"Failed to fetch models: {response.status_code}")
                return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return {
                "detail": "Unable to reach the server. Please check your connection."}, 500

    def activate_model(self, model_id: int) -> tuple:
        endpoint = f"/models/{model_id}/activate"
        payload = {"is_active": True}
        try:
            response = self.client.patch(endpoint, json=payload)
            if response.status_code == 200:
                logger.info(f"Model {model_id} activated successfully")
                return response.json(), 200
            else:
                logger.error(
                    f"Failed to activate model {model_id}: {response.status_code}")
                return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error activating model {model_id}: {e}")
            return {
                "detail": "Unable to reach the server. Please check your connection."}, 500


class PredictionService:
    """Serviço para obter predições em tempo real."""

    def __init__(self):
        self.client = APIClient()

    def get_daily_prediction(
            self,
            historical_points: int = 3,
            predicted_points: int = 7):
        """
        GET /predictions/daily
        Args:
            historical_points: dias históricos (1-5)
            predicted_points: dias a prever (1-14)
        """
        endpoint = "/predictions/daily"
        params = {
            "historical_points": historical_points,
            "predicted_points": predicted_points,
        }
        try:
            response = self.client.get(endpoint, params=params)
            if response.status_code == 200:
                return response.json(), 200
            else:
                logger.error(
                    f"Daily prediction failed: {response.status_code}")
                return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error fetching daily prediction: {e}")
            return {"detail": "Unable to reach the server."}, 500

    def get_hourly_prediction(
            self,
            historical_points: int = 3,
            predicted_points: int = 12):
        """
        GET /predictions/hourly
        Args:
            historical_points: horas históricas (3-5)
            predicted_points: horas a prever (1-24)
        """
        endpoint = "/predictions/hourly"
        params = {
            "historical_points": historical_points,
            "predicted_points": predicted_points,
        }
        try:
            response = self.client.get(endpoint, params=params)
            if response.status_code == 200:
                return response.json(), 200
            else:
                logger.error(
                    f"Hourly prediction failed: {response.status_code}")
                return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error fetching hourly prediction: {e}")
            return {"detail": "Unable to reach the server."}, 500
