from .api_client import APIClient
import requests
from app.manager.session_manager import SessionManager

class AuthService:
    def __init__(self):
        self.client = APIClient()
        self.base_url = self.client.base_url

    def register_user(self, username, email, password):
        endpoint = "/register"
        payload = {
            "email": email,
            "username": username,
            "password": password
        }
        
        try:
            response = self.client.post(endpoint, data=payload)
            
            return response.json(), response.status_code
            
        except Exception as e:
            print(f"ERRO NO REQUESTS: {repr(e)}")
            return {"detail": f"Connection error: {str(e)}"}, 500
        
    def login_user(self, email, password):
        url = f"{self.base_url}/login"
        
        payload = {
            "username": email, 
            "password": password
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            response_data = response.json()
            
            if response.status_code == 200:
                token = response_data.get("access_token")
                role = response_data.get("role")
                
                if token and role:
                    SessionManager.set_session(token, role)
                
                return response_data, 200
            
            return response_data, response.status_code

        except Exception as e:
            print(f"Não ligou ao backend :( {e}")
            return {"detail": f"Connection error: {str(e)}"}, 500