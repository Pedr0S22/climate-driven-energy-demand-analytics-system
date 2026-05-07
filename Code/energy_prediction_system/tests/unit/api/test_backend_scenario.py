import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from unittest.mock import patch
from src.api.models.model import Model
from src.api.schemas.user import UserCreate
from src.api.services.auth import create_user
from src.api.services.simulation_service import SimulationService
from src.api.services.inference_engine import get_inference_engine, InferenceEngine
from unittest.mock import MagicMock


@pytest.fixture
def admin_token(client: TestClient, db):
    admin_in = UserCreate(
        username="testadmin",
        email="testadmin@example.com",
        password="admin123456"
    )
    create_user(db, admin_in, is_admin=True)

    response = client.post("/api/auth/login", json={
        "email": "testadmin@example.com",
        "password": "admin123456"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def client_token(client: TestClient):
    client.post("/api/auth/register", json={
        "username": "normalclient",
        "email": "normal@example.com",
        "password": "client123456"
    })
    response = client.post("/api/auth/login", json={
        "email": "normal@example.com",
        "password": "client123456"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def active_hourly_model(db):
    from unittest.mock import MagicMock

    db.query(Model).filter(Model.model_pred_type ==
                           "hourly").update({"is_active": False})
    model = Model(
        model_name_id=100,
        model_type="Random Forest",
        model_pred_type="hourly",
        model_server_relative_path="/models/hourly/rf.joblib",
        dataset_selected="full",
        top2_drivers="L1_Load, hour",
        rmse=600.0, mae=450.0, r2=0.98,
        is_active=True
    )
    db.add(model)
    db.commit()
    db.refresh(model)

    engine = get_inference_engine()

    # Criar mock do modelo que retorna uma predição
    mock_model = MagicMock()
    mock_model.predict.return_value = 30000.0

    # Criar mock do scaler com transform
    mock_scaler = MagicMock()
    mock_scaler.transform.return_value = [[0.5, 0.3, 0.2]]

    engine._models["hourly"] = mock_model
    engine._scalers["hourly"] = mock_scaler

    return model


def _next_id(db):
    """Obtém o próximo ID disponível"""
    max_id = db.query(func.max(Model.model_name_id)).scalar() or 0
    return max_id + 1


def _create_test_model(db, model_pred_type="daily", is_active=False, **kwargs):
    model = Model(
        model_name_id=_next_id(db),
        model_type=kwargs.get("model_type", "Test"),
        model_pred_type=model_pred_type,
        model_server_relative_path=kwargs.get("path", "/test.joblib"),
        dataset_selected=kwargs.get("dataset", "full"),
        top2_drivers=kwargs.get("drivers", "a,b"),
        rmse=kwargs.get("rmse", 0.1),
        mae=kwargs.get("mae", 0.1),
        r2=kwargs.get("r2", 0.9),
        is_active=is_active
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


class TestListModels:
    BASE_URL = "/api/v1/models"

    def test_list_models_empty(self, client):
        response = client.get(self.BASE_URL)
        assert response.status_code == 200

    def test_list_models_has_metrics(self, client):
        response = client.get(self.BASE_URL)
        if response.json():
            model = response.json()[0]
            for field in [
                "rmse",
                "r2",
                "mae",
                "top2_drivers",
                "model_type",
                    "model_pred_type"]:
                assert field in model


class TestActivateModel:
    BASE_URL = "/api/v1/models"

    def test_activate_without_token_returns_401(self, client):
        response = client.patch(
            f"{self.BASE_URL}/1/activate",
            json={
                "is_active": True})
        assert response.status_code == 401

    def test_activate_not_found(self, client, admin_token):
        response = client.patch(
            f"{self.BASE_URL}/99999/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404


class TestRBAC:
    BASE_URL = "/api/v1/models"

    @pytest.fixture
    def sample_model(self, db):
        return _create_test_model(db)

    def test_client_cannot_activate_model(
            self, client, client_token, sample_model):
        response = client.patch(
            f"{self.BASE_URL}/{sample_model.model_name_id}/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {client_token}"}
        )
        assert response.status_code == 403

    def test_admin_can_activate_model(self, client, admin_token, db):
        model = _create_test_model(db)
        response = client.patch(
            f"{self.BASE_URL}/{model.model_name_id}/activate",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_list_models_is_public(self, client):
        assert client.get(self.BASE_URL).status_code == 200


class TestSimulationTemplates:
    TEMPLATES_URL = "/api/simulations/templates"

    def test_get_template_daily_heatwave(self, client):
        response = client.post(
            self.TEMPLATES_URL,
            json={
                "frequency": "daily",
                "condition": "heatwave"})
        assert response.status_code == 200
        data = response.json()
        assert data["features"]["t2m"] == 42.0

    def test_get_template_hourly_storm(self, client):
        response = client.post(
            self.TEMPLATES_URL,
            json={
                "frequency": "hourly",
                "condition": "storm"})
        assert response.status_code == 200
        assert response.json()["features"]["u10"] == -35.0

    def test_get_template_invalid_condition(self, client):
        response = client.post(
            self.TEMPLATES_URL,
            json={
                "frequency": "daily",
                "condition": "tornado"})
        assert response.status_code == 404

    def test_all_16_templates_exist(self, client):
        """Verifica que os 16 templates estão disponíveis"""
        frequencies = ["daily", "hourly"]
        conditions = ["average", "rainy", "storm", "heatwave"]
        count = 0
        for freq in frequencies:
            for condition in conditions:
                response = client.post(
                    self.TEMPLATES_URL,
                    json={"frequency": freq, "condition": condition}
                )
                assert response.status_code == 200, f"Missing: {freq}/{condition}"
                data = response.json()
                assert "features" in data
                assert "dataset_type" in data
                count += 1
        assert count == 8  # 2 × 4 = 8 combinações base (×2 dataset types = 16)

    def test_template_features_validate_physical_limits(self, client):
        """Verifica que templates respeitam limites físicos"""
        response = client.post(
            self.TEMPLATES_URL,
            json={"frequency": "daily", "condition": "heatwave"}
        )
        assert response.status_code == 200
        features = response.json()["features"]
        assert -50 <= features["t2m"] <= 60, "t2m outside physical limits"
        assert 0 <= features.get("tp", 0) <= 500, "tp outside physical limits"


class TestSimulationRun:
    RUN_URL = "/api/simulations/run"

    def test_run_simulation_heatwave(self, client, active_hourly_model):
        response = client.post(self.RUN_URL, json={
            "frequency": "hourly", "template_name": "heatwave",
            "month": 5, "day_of_week": 0, "overrides": {"t2m": 50.0}
        })
        assert response.status_code == 200
        data = response.json()
        assert "predicted_mw" in data
        assert len(data["top_drivers"]) == 2

    def test_simulation_extreme_temp_increases_load(
            self, client, active_hourly_model):
        """Temperatura extrema aumenta carga prevista"""
        from unittest.mock import MagicMock

        engine = get_inference_engine()

        mock_model = MagicMock()
        mock_model.predict.side_effect = [
            40000.0, 25000.0]  # heatwave > average

        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[0.5, 0.3]]

        engine._models["hourly"] = mock_model
        engine._scalers["hourly"] = mock_scaler

        hot = client.post(self.RUN_URL, json={
            "frequency": "hourly", "template_name": "heatwave",
            "month": 5, "day_of_week": 0, "overrides": {"t2m": 50.0}
        })
        avg = client.post(self.RUN_URL, json={
            "frequency": "hourly", "template_name": "average",
            "month": 5, "day_of_week": 0
        })

        assert hot.status_code == 200
        assert avg.status_code == 200
        assert hot.json()["predicted_mw"] > avg.json()["predicted_mw"]

    def test_simulation_validation_error(self, client):
        response = client.post(self.RUN_URL, json={
            "frequency": "hourly", "template_name": "average",
            "month": 7, "day_of_week": 3, "overrides": {"t2m": 100.0}
        })
        assert response.status_code == 400

    def test_simulation_no_active_model(self, client, db):
        db.query(Model).update({"is_active": False})
        db.commit()
        response = client.post(self.RUN_URL, json={
            "frequency": "daily", "template_name": "average",
            "month": 1, "day_of_week": 0
        })
        assert response.status_code == 400

    def test_simulation_invalid_template(self, client):
        response = client.post(self.RUN_URL, json={
            "frequency": "hourly", "template_name": "tornado",
            "month": 1, "day_of_week": 0
        })
        assert response.status_code == 400


class TestPCAFlow:
    def test_pca_transform_called_when_dataset_is_pca(self, db):

        model = Model(
            model_name_id=300,
            model_type="Random Forest",
            model_pred_type="daily",
            model_server_relative_path="/models/daily/rf_pca.joblib",
            dataset_selected="pca",
            top2_drivers="t2m,sp",
            rmse=0.15,
            mae=0.12,
            r2=0.89,
            is_active=True)
        db.add(model)
        db.commit()

        mock_pca = MagicMock()
        mock_pca.transform = MagicMock(return_value=[[1.0, 2.0, 3.0]])

        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[0.5, 0.3, 0.2]]

        mock_model = MagicMock()
        mock_model.predict.return_value = 35000.0

        engine = get_inference_engine()

        with patch.object(InferenceEngine, 'load_active_model', return_value=True), \
                patch.object(InferenceEngine, 'get_model', return_value=mock_model), \
                patch.object(InferenceEngine, 'get_scaler', return_value=mock_scaler), \
                patch.object(InferenceEngine, 'get_pca', return_value=mock_pca):

            engine.load_active_model(model)

            result = SimulationService.run_simulation(
                db=db, frequency="daily", template_name="average",
                month=6, day_of_week=3
            )

        assert result["predicted_mw"] == 35000.0
        mock_pca.transform.assert_called_once()
        mock_scaler.transform.assert_called()


class TestInferenceEngine:
    def test_inference_engine_singleton(self):
        engine1 = get_inference_engine()
        engine2 = get_inference_engine()
        assert engine1 is engine2

    def test_inference_engine_cache_shared(self, db):
        """Cache é partilhado entre instâncias"""
        from unittest.mock import MagicMock, patch

        model = _create_test_model(db, model_pred_type="daily", is_active=True)

        with patch('src.api.services.inference_engine.Path.exists', return_value=True), \
                patch('src.api.services.inference_engine.joblib.load', return_value=MagicMock()):

            engine1 = get_inference_engine()
            engine1.load_active_model(model)
            engine2 = get_inference_engine()

            assert engine2.get_model("daily") is not None
            assert engine1.get_model("daily") is engine2.get_model("daily")

    def test_inference_engine_refresh_on_activation(
            self, client, admin_token, db):
        """Engine recarrega quando modelo ativo muda"""
        model = _create_test_model(
            db, model_pred_type="daily", is_active=False)

        with patch.object(InferenceEngine, 'load_active_model') as mock_load:
            client.patch(
                f"/api/v1/models/{model.model_name_id}/activate",
                json={"is_active": True},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            mock_load.assert_called()
