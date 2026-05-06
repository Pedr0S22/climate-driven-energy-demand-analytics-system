import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.database.session import get_db
from src.api.main import app
from src.api.models.model import Model

DATABASE_URL = "postgresql://piacd_energy:postgres_Piacd_energy@localhost:5433/energy_db"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)


@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def get_admin_token(client):
    """Login como admin e retorna o token"""
    response = client.post("/api/auth/login", json={
        "email": "pedro.silva@piacd.pt",
        "password": "adoroSerAdmin123."
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


class TestListModels:
    """GET /api/models/api/v1/models/"""

    def test_list_models_returns_data(self, client):
        response = client.get("/api/models/api/v1/models/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_models_has_metrics(self, client):
        response = client.get("/api/models/api/v1/models/")
        if response.json():
            model = response.json()[0]
            assert "rmse" in model
            assert "r2" in model
            assert "mae" in model
            assert "top2_drivers" in model


class TestActivateModel:
    """PATCH /api/models/api/v1/models/{id}/activate"""

    def test_activate_model_success(self, client, db_session):
        token = get_admin_token(client)

        model = Model(
            model_type="Test Model",
            model_pred_type="daily",
            model_server_relative_path="/test.joblib",
            dataset_selected="full",
            top2_drivers="a,b",
            rmse=0.1, mae=0.1, r2=0.9,
            is_active=False
        )
        db_session.add(model)
        db_session.commit()
        model_id = model.model_name_id

        response = client.patch(
            f"/api/models/api/v1/models/{model_id}/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_active"]

    def test_activate_model_mutex(self, client, db_session):
        token = get_admin_token(client)

        m1 = Model(
            model_type="Test1",
            model_pred_type="daily",
            model_server_relative_path="/t1.joblib",
            dataset_selected="full",
            top2_drivers="a,b",
            rmse=0.1,
            mae=0.1,
            r2=0.9,
            is_active=False)
        m2 = Model(
            model_type="Test2",
            model_pred_type="daily",
            model_server_relative_path="/t2.joblib",
            dataset_selected="full",
            top2_drivers="a,b",
            rmse=0.1,
            mae=0.1,
            r2=0.9,
            is_active=False)
        db_session.add_all([m1, m2])
        db_session.commit()

        client.patch(
            f"/api/models/api/v1/models/{m1.model_name_id}/activate",
            json={
                "is_active": True},
            headers={
                "Authorization": f"Bearer {token}"})
        client.patch(
            f"/api/models/api/v1/models/{m2.model_name_id}/activate",
            json={
                "is_active": True},
            headers={
                "Authorization": f"Bearer {token}"})

        db_session.refresh(m1)
        db_session.refresh(m2)
        assert m1.is_active is False
        assert m2.is_active

    def test_activate_not_found(self, client):
        token = get_admin_token(client)
        response = client.patch(
            "/api/models/api/v1/models/99999/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404


class TestRBAC:
    """Testes de segurança"""

    def test_activate_without_token_returns_401(self, client):
        response = client.patch(
            "/api/models/api/v1/models/1/activate",
            json={
                "is_active": True})
        assert response.status_code == 401
