# Code\energy_prediction_system\src\app\client\auth_service.py
from .api_client import APIClient

class AuthService:
    def __init__(self):
        self.client = APIClient()

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
            return {"detail": f"Erro de conexão com requests: {str(e)}"}, 500