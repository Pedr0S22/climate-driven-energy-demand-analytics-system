import logging
import os

import keyring
from dotenv import load_dotenv

load_dotenv()


class SessionManager:
    _SERVICE_NAME = os.getenv("KEYRING_SERVICE_NAME")
    _KEY_TOKEN = os.getenv("KEYRING_TOKEN_KEY")
    _KEY_ROLE = os.getenv("KEYRING_ROLE_KEY")

    @classmethod
    def set_session(cls, token: str, role: str) -> None:
        keyring.set_password(cls._SERVICE_NAME, cls._KEY_TOKEN, token)
        keyring.set_password(cls._SERVICE_NAME, cls._KEY_ROLE, role)

    @classmethod
    def get_token(cls) -> str | None:
        return keyring.get_password(cls._SERVICE_NAME, cls._KEY_TOKEN)

    @classmethod
    def get_role(cls) -> str | None:
        return keyring.get_password(cls._SERVICE_NAME, cls._KEY_ROLE)

    @classmethod
    def clear_session(cls) -> None:
        try:
            keyring.delete_password(cls._SERVICE_NAME, cls._KEY_TOKEN)
        except Exception as e:
            logging.debug(f"Could not delete token: {e}")

        try:
            keyring.delete_password(cls._SERVICE_NAME, cls._KEY_ROLE)
        except Exception as e:
            logging.debug(f"Could not delete role: {e}")
