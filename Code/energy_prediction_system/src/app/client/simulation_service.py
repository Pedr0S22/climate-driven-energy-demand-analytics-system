import logging
from typing import Any

from .api_client import APIClient

logger = logging.getLogger(__name__)


class SimulationService:
    def __init__(self):
        self.client = APIClient()

    def get_template(self, frequency: str,
                     template_name: str) -> tuple[dict[str, Any], int]:
        endpoint = "/simulations/templates"
        payload = {
            "frequency": frequency,
            "template_name": template_name
        }

        try:
            response = self.client.post(endpoint, json=payload)
            logger.info(
                f"Fetching template {frequency}/{template_name}: Status {response.status_code}")

            if response.status_code == 200:
                return response.json(), 200
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Failed to fetch template: {error_detail}")
                return {"detail": error_detail}, response.status_code

        except Exception as e:
            logger.error(f"Error fetching template: {repr(e)}")
            return {"detail": "Unable to connect to server."}, 500

    def run_daily_simulation(
        self,
        template_name: str,
        year: int,
        month: int,
        day_of_week: int,
        overrides: dict[str, float] | None = None
    ) -> tuple[dict[str, Any], int]:
        endpoint = "/simulations/daily"
        payload = {
            "template_name": template_name,
            "year": year,
            "month": month,
            "day_of_week": day_of_week,
        }
        # Só adiciona "overrides" se NÃO for None e NÃO for vazio
        if overrides:
            payload["overrides"] = overrides

        try:
            response = self.client.post(endpoint, json=payload)
            logger.info(
                f"Daily simulation {template_name}: Status {response.status_code}")

            if response.status_code == 200:
                return response.json(), 200
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Simulation failed: {error_detail}")
                return {"detail": error_detail}, response.status_code

        except Exception as e:
            logger.error(f"Error running daily simulation: {repr(e)}")
            return {"detail": "Unable to connect to server."}, 500

    def run_hourly_simulation(
        self,
        template_name: str,
        year: int,
        month: int,
        day_of_week: int,
        hour: int,
        overrides: dict[str, float] | None = None
    ) -> tuple[dict[str, Any], int]:
        endpoint = "/simulations/hourly"
        payload = {
            "template_name": template_name,
            "year": year,
            "month": month,
            "day_of_week": day_of_week,
            "hour": hour,
        }
        # Só adiciona "overrides" se NÃO for None e NÃO for vazio
        if overrides:
            payload["overrides"] = overrides

        try:
            response = self.client.post(endpoint, json=payload)
            logger.info(
                f"Hourly simulation {template_name}: Status {response.status_code}")

            if response.status_code == 200:
                return response.json(), 200
            else:
                error_detail = response.json().get("detail", "Unknown error")
                logger.error(f"Simulation failed: {error_detail}")
                return {"detail": error_detail}, response.status_code

        except Exception as e:
            logger.error(f"Error running hourly simulation: {repr(e)}")
            return {"detail": "Unable to connect to server."}, 500

    def get_available_templates(self, frequency: str) -> list[str]:
        """Obtém templates disponíveis do backend"""
        endpoint = "/simulations/available-templates"
        try:
            response = self.client.get(
                endpoint, params={
                    "frequency": frequency})
            if response.status_code == 200:
                return response.json().get("templates", [])
            return ["average", "rainy", "storm", "heatwave"]  # fallback
        except Exception:
            return ["average", "rainy", "storm", "heatwave"]  # fallback
