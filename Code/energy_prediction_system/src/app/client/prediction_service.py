import logging

from .api_client import APIClient

logger = logging.getLogger(__name__)


class PredictionService:
    """
    Service for interacting with real-time prediction endpoints.
    """

    def __init__(self):
        self.client = APIClient()

    def get_prediction(self, frequency, historical_points, predicted_points):
        """
        Fetches predictions from the backend.
        Returns (data, status_code).
        """
        endpoint = f"/predictions/{frequency}"
        params = {"historical_points": historical_points, "predicted_points": predicted_points}

        try:
            logger.info(f"Requesting {frequency} prediction: hist={historical_points}, pred={predicted_points}")
            response = self.client.get(endpoint, params=params)
            return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error in PredictionService ({frequency}): {e}")
            return {"detail": "Connection error. Please ensure the backend is running."}, 500
