import logging
import os
from pathlib import Path

import keyring
from dotenv import load_dotenv

# Define o caminho para o ficheiro .env (raiz do projeto
# energy_prediction_system)
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class SessionManager:
    _SERVICE_NAME = os.getenv("KEYRING_SERVICE_NAME")
    _KEY_TOKEN = os.getenv("KEYRING_TOKEN_KEY")
    _KEY_ROLE = os.getenv("KEYRING_ROLE_KEY")

    @classmethod
    def set_session(cls, token: str, role: str) -> None:
        if not cls._SERVICE_NAME:
            logger.error("KEYRING_SERVICE_NAME not set in environment!")
            return

        try:
            keyring.set_password(cls._SERVICE_NAME, cls._KEY_TOKEN, token)
            keyring.set_password(cls._SERVICE_NAME, cls._KEY_ROLE, role)
            logger.info("Session stored successfully in secure vault.")
        except Exception as e:
            logger.error(f"Failed to set session in keyring: {e}")

    @classmethod
    def get_token(cls) -> str | None:
        try:
            return keyring.get_password(cls._SERVICE_NAME, cls._KEY_TOKEN)
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None

    @classmethod
    def get_role(cls) -> str | None:
        try:
            return keyring.get_password(cls._SERVICE_NAME, cls._KEY_ROLE)
        except Exception as e:
            logger.error(f"Error retrieving role: {e}")
            return None

    @classmethod
    def clear_session(cls) -> None:
        try:
            keyring.delete_password(cls._SERVICE_NAME, cls._KEY_TOKEN)
        except Exception as e:
            logger.warning(
                f"Could clear session because token deletion fail: {e}")

        try:
            keyring.delete_password(cls._SERVICE_NAME, cls._KEY_ROLE)
        except Exception as e:
            logger.warning(
                f"Could clear session because role deletion fail: {e}")

        logger.info("Session cleared successfully.")
