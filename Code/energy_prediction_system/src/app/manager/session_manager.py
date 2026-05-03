import keyring

class SessionManager:
    """
    Handles secure storage of user session data using the OS keyring
    """
    _SERVICE_NAME = "energy_prediction_system"
    _TOKEN_KEY = "access_token"
    _ROLE_KEY = "user_role"

    @staticmethod
    def set_session(token: str, role: str):
        """
        Securely stores the access token and the user role in the OS vault
        """
        try:
            keyring.set_password(SessionManager._SERVICE_NAME, SessionManager._TOKEN_KEY, token)
            keyring.set_password(SessionManager._SERVICE_NAME, SessionManager._ROLE_KEY, role)
        except Exception as e:
            print(f"Error saving session to keyring: {e}")

    @staticmethod
    def get_token() -> str:
        """
        Retrieves the access token from the secure vault
        Returns None if not found
        """
        return keyring.get_password(SessionManager._SERVICE_NAME, SessionManager._TOKEN_KEY)

    @staticmethod
    def get_role() -> str:
        """
        Retrieves the user role
        """
        return keyring.get_password(SessionManager._SERVICE_NAME, SessionManager._ROLE_KEY)

    @staticmethod
    def clear_session():
        """
        Removes session data from the keyring- used for Logout (uc14)
        """
        try:
            keyring.delete_password(SessionManager._SERVICE_NAME, SessionManager._TOKEN_KEY)
            keyring.delete_password(SessionManager._SERVICE_NAME, SessionManager._ROLE_KEY)
        except keyring.errors.PasswordDeleteError:
            #silent fail if the keys already don't exist
            pass

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if there is a valid token stored
        """
        return SessionManager.get_token() is not None

    @staticmethod
    def get_auth_header() -> dict:
        """
        Builds Authorization header for API requests.
        
        Returns:
            {"Authorization": "Bearer <token>"} or empty dict if no token
        """
        token = SessionManager.get_token()
        if not token:
            return {}
        
        return {"Authorization": f"Bearer {token}"}
