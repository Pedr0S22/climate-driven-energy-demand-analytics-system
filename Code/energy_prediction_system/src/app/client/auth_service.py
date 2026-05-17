import logging

from src.app.client.api_client import APIClient
from src.app.manager.session_manager import SessionManager

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.client = APIClient()

    def register_user(self, username, email, password):
        endpoint = "/auth/register"
        payload = {"email": email, "username": username, "password": password}

        try:
            # Registration expects JSON
            response = self.client.post(endpoint, json=payload)
            logger.info(f"Register attempt for {email}: Status {response.status_code}")
            return response.json(), response.status_code

        except Exception as e:
            logger.error(f"Error during registration for {email}: {repr(e)}")
            return {"detail": "Unable to reach the server. Please check your connection."}, 500

    def login_user(self, email, password):
        endpoint = "/auth/login"
        # OAuth2 (FastAPI) expects Form Data for login
        payload = {"username": email, "password": password}

        try:
            logger.info(f"Attempting login for {email}")
            response = self.client.post(endpoint, data=payload)
            response_data = response.json()

            if response.status_code == 200:
                token = response_data.get("access_token")
                role = response_data.get("role")

                if token and role:
                    logger.info(f"Login successful for {email}. Role: {role}")
                    SessionManager.set_session(token, role)

                return response_data, 200

            logger.info(f"Login failed for {email}: Status {response.status_code}")
            return response_data, response.status_code

        except Exception as e:
            logger.error(f"Connection error during login for {email}: {e}")
            return {"detail": "Unable to connect to the server. Please check your connection and try again later."}, 500

    def logout_user(self):
        """Notifies the backend about the logout event."""
        endpoint = "/auth/logout"
        try:
            # APIClient automatically injects the Bearer token from
            # SessionManager
            response = self.client.post(endpoint)
            if response.status_code == 200:
                logger.info("Backend logout successful.")
            else:
                logger.warning(f"Backend logout failed with status: {response.status_code}")
        except Exception as e:
            # We don't return anything as logout is mostly for auditing
            logger.error(f"Error during backend logout: {e}")

    def get_user_profile(self):
        """Fetches the authenticated user's profile."""
        endpoint = "/auth/me"
        try:
            response = self.client.get(endpoint)
            logger.info(f"Profile fetch attempt: Status {response.status_code}")
            return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error fetching user profile: {repr(e)}")
            return {"detail": "Unable to reach the server."}, 500
