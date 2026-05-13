# Code\energy_prediction_system\src\app\client\api_client.py
import requests

class APIClient:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api/auth"

    def post(self, endpoint, data=None):
        url = f"{self.base_url}{endpoint}"
        print(f"Frontend (requests) a enviar para: {url}") 
        return requests.post(url, json=data, timeout=10)