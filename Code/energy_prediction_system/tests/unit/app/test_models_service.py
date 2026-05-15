# tests/unit/app/test_models_service.py
"""
Testes unitários para ModelsService e seus Workers.
"""
from unittest.mock import patch

import pytest

from app.client.models_service import ModelsService
from app.ui.views.model_management_view import (
    ActivateModelWorker,
    LoadModelsWorker,
)


@pytest.fixture
def models_service():
    """Fixture que retorna uma instância limpa do ModelsService"""
    return ModelsService()


@pytest.fixture
def sample_models_list():
    """Fixture com dados de exemplo de modelos retornados pela API"""
    return [
        {
            "model_name_id": 1,
            "model_type": "RandomForest",
            "model_creation_date": "2026-01-24T14:30:00",
            "model_pred_type": "daily",
            "model_server_relative_path": "/models/daily_rf.joblib",
            "dataset_selected": "full",
            "top2_drivers": "t2m, L1_Load",
            "rmse": 150.22,
            "mae": 100.51,
            "r2": 0.99,
            "is_active": True,
        },
        {
            "model_name_id": 2,
            "model_type": "LinearReg",
            "model_creation_date": "2025-10-10T10:30:00",
            "model_pred_type": "daily",
            "model_server_relative_path": "/models/daily_lr.joblib",
            "dataset_selected": "pca",
            "top2_drivers": "PCA_1, PCA_2",
            "rmse": 180.54,
            "mae": 120.32,
            "r2": 0.97,
            "is_active": False,
        },
        {
            "model_name_id": 3,
            "model_type": "RandomForest",
            "model_creation_date": "2026-01-24T14:30:00",
            "model_pred_type": "hourly",
            "model_server_relative_path": "/models/hourly_rf.joblib",
            "dataset_selected": "full",
            "top2_drivers": "t2m, hour",
            "rmse": 3.52,
            "mae": 2.10,
            "r2": 0.98,
            "is_active": True,
        },
        {
            "model_name_id": 4,
            "model_type": "LinearReg",
            "model_creation_date": "2025-10-10T09:15:00",
            "model_pred_type": "hourly",
            "model_server_relative_path": "/models/hourly_lr.joblib",
            "dataset_selected": "pca",
            "top2_drivers": "PCA_1, PCA_2",
            "rmse": 4.05,
            "mae": 2.54,
            "r2": 0.95,
            "is_active": False,
        },
    ]


class TestModelsServiceGetAllModels:
    """Testes para o método get_all_models()"""

    def test_get_all_models_success(self, models_service, sample_models_list):
        """Testa obtenção bem-sucedida da lista completa de modelos"""
        with patch.object(models_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = sample_models_list

            data, status = models_service.get_all_models()

            assert status == 200
            assert len(data) == 4
            assert data[0]["model_type"] == "RandomForest"
            assert data[0]["model_name_id"] == 1
            assert data[0]["is_active"] is True

    def test_get_all_models_empty_list(self, models_service):
        """Testa obtenção de lista vazia"""
        with patch.object(models_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = []

            data, status = models_service.get_all_models()

            assert status == 200
            assert data == []

    def test_get_all_models_server_error(self, models_service):
        """Testa erro 500 do servidor"""
        with patch.object(models_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.json.return_value = {
                "detail": "Internal Server Error"}

            data, status = models_service.get_all_models()

            assert status == 500
            assert data["detail"] == "Internal Server Error"

    def test_get_all_models_unauthorized(self, models_service):
        """Testa erro 401 - não autenticado"""
        with patch.object(models_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 401
            mock_get.return_value.json.return_value = {
                "detail": "Not authenticated"}

            data, status = models_service.get_all_models()

            assert status == 401
            assert data["detail"] == "Not authenticated"

    def test_get_all_models_forbidden(self, models_service):
        """Testa erro 403 - sem permissões"""
        with patch.object(models_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 403
            mock_get.return_value.json.return_value = {
                "detail": "Admin privileges required"}

            data, status = models_service.get_all_models()

            assert status == 403
            assert data["detail"] == "Admin privileges required"

    def test_get_all_models_connection_error(self, models_service):
        """Testa erro de conexão"""
        with patch.object(models_service.client, "get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            data, status = models_service.get_all_models()

            assert status == 500
            assert data["detail"] == "Unable to reach the server. Please check your connection."


class TestModelsServiceActivateModel:
    """Testes para o método activate_model()"""

    def test_activate_model_success(self, models_service):
        """Testa ativação bem-sucedida"""
        response = {
            "model_name_id": 2,
            "model_type": "LinearReg",
            "model_pred_type": "daily",
            "is_active": True,
        }
        with patch.object(models_service.client, "patch") as mock_patch:
            mock_patch.return_value.status_code = 200
            mock_patch.return_value.json.return_value = response

            data, status = models_service.activate_model(2)

            assert status == 200
            assert data["is_active"] is True
            assert data["model_name_id"] == 2

    def test_activate_model_not_found(self, models_service):
        """Testa modelo não encontrado (404)"""
        with patch.object(models_service.client, "patch") as mock_patch:
            mock_patch.return_value.status_code = 404
            mock_patch.return_value.json.return_value = {
                "detail": "Model with id 999 not found"}

            data, status = models_service.activate_model(999)

            assert status == 404
            assert "not found" in data["detail"]

    def test_activate_model_already_active(self, models_service):
        """Testa modelo já ativo (400)"""
        with patch.object(models_service.client, "patch") as mock_patch:
            mock_patch.return_value.status_code = 400
            mock_patch.return_value.json.return_value = {
                "detail": "Model 1 is already active"}

            data, status = models_service.activate_model(1)

            assert status == 400
            assert "already active" in data["detail"]

    def test_activate_model_forbidden(self, models_service):
        """Testa sem permissões (403)"""
        with patch.object(models_service.client, "patch") as mock_patch:
            mock_patch.return_value.status_code = 403
            mock_patch.return_value.json.return_value = {
                "detail": "Admin privileges required"}

            data, status = models_service.activate_model(1)
            assert status == 403
            assert data["detail"] == "Admin privileges required"

    def test_activate_model_server_error(self, models_service):
        """Testa erro do servidor (500)"""
        with patch.object(models_service.client, "patch") as mock_patch:
            mock_patch.return_value.status_code = 500
            mock_patch.return_value.json.return_value = {
                "detail": "Error activating model"}

            data, status = models_service.activate_model(1)

            assert status == 500
            assert data["detail"] == "Error activating model"

    def test_activate_model_connection_error(self, models_service):
        """Testa erro de conexão"""
        with patch.object(models_service.client, "patch") as mock_patch:
            mock_patch.side_effect = Exception("Timeout")

            data, status = models_service.activate_model(1)

            assert status == 500
            assert "Unable to reach the server" in data["detail"]


class TestLoadModelsWorker:
    """Testes para o LoadModelsWorker (QThread)"""

    def test_load_models_worker_success(self, qtbot, sample_models_list):
        """Testa worker que carrega modelos com sucesso"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_all_models.return_value = (
                sample_models_list, 200)

            worker = LoadModelsWorker()

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            models, error = blocker.args
            assert error == ""
            assert len(models) == 4
            assert models[0]["model_type"] == "RandomForest"

    def test_load_models_worker_empty_list(self, qtbot):
        """Testa worker que retorna lista vazia"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_all_models.return_value = ([], 200)

            worker = LoadModelsWorker()

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            models, error = blocker.args
            assert error == ""
            assert models == []

    def test_load_models_worker_server_error(self, qtbot):
        """Testa worker com erro do servidor"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_all_models.return_value = (
                {"detail": "Internal Server Error"},
                500,
            )

            worker = LoadModelsWorker()

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            models, error = blocker.args
            assert models == []
            assert error == "Internal Server Error"

    def test_load_models_worker_exception(self, qtbot):
        """Testa worker com exceção inesperada"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_all_models.side_effect = Exception(
                "Network failure")

            worker = LoadModelsWorker()

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            models, error = blocker.args
            assert models == []
            assert error == "Network failure"


class TestActivateModelWorker:
    """Testes para o ActivateModelWorker (QThread)"""

    def test_activate_model_worker_success(self, qtbot):
        """Testa worker que ativa modelo com sucesso"""
        response = {
            "model_name_id": 2,
            "model_type": "LinearReg",
            "model_pred_type": "daily",
            "is_active": True,
        }
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.activate_model.return_value = (response, 200)

            worker = ActivateModelWorker(2)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            data, error = blocker.args
            assert error == ""
            assert data["is_active"] is True
            assert data["model_name_id"] == 2

    def test_activate_model_worker_not_found(self, qtbot):
        """Testa worker com modelo não encontrado"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.activate_model.return_value = (
                {"detail": "Model with id 999 not found"},
                404,
            )

            worker = ActivateModelWorker(999)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            data, error = blocker.args
            assert data is None
            assert "not found" in error

    def test_activate_model_worker_server_error(self, qtbot):
        """Testa worker com erro do servidor"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.activate_model.return_value = (
                {"detail": "Internal Server Error"},
                500,
            )

            worker = ActivateModelWorker(1)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            data, error = blocker.args
            assert data is None
            assert error == "Internal Server Error"

    def test_activate_model_worker_exception(self, qtbot):
        """Testa worker com exceção inesperada"""
        with patch(
            "app.ui.views.model_management_view.ModelsService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.activate_model.side_effect = Exception(
                "Timeout Error")

            worker = ActivateModelWorker(1)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            data, error = blocker.args
            assert data is None
            assert error == "Timeout Error"
