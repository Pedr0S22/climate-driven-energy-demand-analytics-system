# Code\energy_prediction_system\src\app\client\api_client.py
import logging

import requests

from src.app.manager.session_manager import SessionManager

logger = logging.getLogger(__name__)


class APIClient:
    """
    Generic API Client for communicating with the FastAPI backend.
    Handles base URL, HTTP methods, and automatic JWT authentication.
    """

    def __init__(self):
        # Base API URL (via Traefik)
        self.base_url = "http://localhost/api"

    def _get_headers(self):
        """Builds headers, automatically adding the Bearer token if available."""
        headers = {}
        token = SessionManager.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def get(self, endpoint, params=None):
        """Standard GET request."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET Request to: {url}")
        try:
            return requests.get(url, params=params, headers=self._get_headers(), timeout=10)
        except Exception as e:
            logger.error(f"GET Request failed: {e}")
            raise

    def post(self, endpoint, data=None, json=None):
        """
        Standard POST request.
        Use 'data=' for Form Data (login) and 'json=' for JSON bodies.
        """
        url = f"{self.base_url}{endpoint}"
        logger.info(f"POST Request to: {url}")
        try:
            return requests.post(url, data=data, json=json, headers=self._get_headers(), timeout=10)
        except Exception as e:
            logger.error(f"POST Request failed: {e}")
            raise

    def put(self, endpoint, json=None):
        """Standard PUT request."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"PUT Request to: {url}")
        try:
            return requests.put(url, json=json, headers=self._get_headers(), timeout=10)
        except Exception as e:
            logger.error(f"PUT Request failed: {e}")
            raise

    def patch(self, endpoint, json=None):
        """Standard PATCH request."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"PATCH Request to: {url}")
        try:
            return requests.patch(url, json=json, headers=self._get_headers(), timeout=10)
        except Exception as e:
            logger.error(f"PATCH Request failed: {e}")
            raise

    def delete(self, endpoint):
        """Standard DELETE request."""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"DELETE Request to: {url}")
        try:
            return requests.delete(url, headers=self._get_headers(), timeout=10)
        except Exception as e:
            logger.error(f"DELETE Request failed: {e}")
            raise
