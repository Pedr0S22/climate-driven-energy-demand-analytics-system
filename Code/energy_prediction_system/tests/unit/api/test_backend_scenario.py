import pytest
from fastapi.testclient import TestClient
from src.api.models.model import Model
from src.api.schemas.user import UserCreate
from src.api.services.auth import create_user


@pytest.fixture
def admin_token(client: TestClient, db):
    """Cria usuário admin e retorna token JWT"""
    admin_in = UserCreate(
        username="testadmin",
        email="testadmin@example.com",
        password="admin123456"
    )
    create_user(db, admin_in, is_admin=True)

    response = client.post(
        "/api/auth/login",
        json={
            "email": "testadmin@example.com",
            "password": "admin123456"
        }
    )
    assert response.status_code == 200, f"Admin login failed: {response.json()}"
    return response.json()["access_token"]


@pytest.fixture
def client_token(client: TestClient):
    """Cria cliente normal e retorna token JWT"""
    client.post(
        "/api/auth/register",
        json={
            "username": "normalclient",
            "email": "normal@example.com",
            "password": "client123456"
        }
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "normal@example.com",
            "password": "client123456"
        }
    )
    assert response.status_code == 200, f"Client login failed: {response.json()}"
    return response.json()["access_token"]


class TestListModels:
    """Testes para listagem de modelos"""

    BASE_URL = "/api/models/api/v1/models/"

    def test_list_models_empty(self, client):
        """GET /models/ - lista vazia retorna 200"""
        response = client.get(self.BASE_URL)
        assert response.status_code == 200

    def test_list_models_has_metrics(self, client):
        """GET /models/ - verifica campos obrigatórios nos modelos"""
        response = client.get(self.BASE_URL)

        if response.json():
            model = response.json()[0]
            required_fields = [
                "rmse", "r2", "mae",
                "top2_drivers", "model_type", "model_pred_type"
            ]

            for field in required_fields:
                assert field in model, (
                    f"Missing required field '{field}' in model response"
                )


class TestActivateModel:
    """Testes para ativação de modelos"""

    BASE_URL = "/api/models/api/v1/models"

    def test_activate_without_token_returns_401(self, client):
        """PATCH /models/{id}/activate sem token → 401"""
        response = client.patch(
            f"{self.BASE_URL}/1/activate",
            json={"is_active": True}
        )
        assert response.status_code == 401

    def test_activate_not_found(self, client, admin_token):
        """PATCH /models/{id}/activate com ID inválido → 404"""
        response = client.patch(
            f"{self.BASE_URL}/99999/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404


class TestSEG:

    BASE_URL = "/api/models/api/v1/models"

    @pytest.fixture
    def sample_model(self, db):
        model = Model(
            model_name_id=1,
            model_type="Test",
            model_pred_type="daily",
            model_server_relative_path="/test_model.joblib",
            dataset_selected="full",
            top2_drivers="feature1,feature2",
            rmse=0.1,
            mae=0.1,
            r2=0.9,
            is_active=False
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def test_client_cannot_activate_model(
            self, client, client_token, sample_model):
        """nao-admin dá erro 403 ao tentar ativar"""
        response = client.patch(
            f"{self.BASE_URL}/{sample_model.model_name_id}/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403, (
            f"Expected 403 Forbidden, got {response.status_code}: {response.json()}"
        )

    def test_admin_can_activate_model(self, client, admin_token, db):
        """Admin ativa modelo com sucesso"""
        model = Model(
            model_name_id=2,
            model_type="Test",
            model_pred_type="daily",
            model_server_relative_path="/admin_model.joblib",
            dataset_selected="full",
            top2_drivers="a,b",
            rmse=0.1,
            mae=0.1,
            r2=0.9,
            is_active=False
        )
        db.add(model)
        db.commit()

        response = client.patch(
            f"{self.BASE_URL}/{model.model_name_id}/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    def test_list_models_is_public(self, client):
        response = client.get(self.BASE_URL)
        assert response.status_code == 200
