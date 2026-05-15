from unittest.mock import patch

import pytest

from app.client.simulation_service import SimulationService
from app.ui.main_window import (
    DailySimulationWorker,
    HourlySimulationWorker,
    TemplateWorker,
)


@pytest.fixture
def simulation_service():
    return SimulationService()


class TestSimulationServiceGetTemplate:
    def test_get_template_success(self, simulation_service):
        expected_data = {
            "frequency": "daily",
            "template_name": "average",
            "dataset_type": "full",
            "features": {"t2m": 13.78, "sp": 938.67},
        }
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = expected_data

            data, status = simulation_service.get_template("daily", "average")

            assert status == 200
            assert data["frequency"] == "daily"
            assert data["template_name"] == "average"
            assert "features" in data

            # Verifica payload enviado
            mock_post.assert_called_once_with(
                "/simulations/templates",
                json={"frequency": "daily", "template_name": "average"},
            )

    def test_get_template_not_found(self, simulation_service):
        """Testa template não encontrado"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 404
            mock_post.return_value.json.return_value = {
                "detail": "Template not found"}

            data, status = simulation_service.get_template(
                "daily", "nonexistent")

            assert status == 404
            assert data["detail"] == "Template not found"

    def test_get_template_server_error(self, simulation_service):
        """Testa erro do servidor"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.json.return_value = {
                "detail": "Server error"}

            data, status = simulation_service.get_template("daily", "average")

            assert status == 500
            assert data["detail"] == "Server error"

    def test_get_template_connection_error(self, simulation_service):
        """Testa erro de conexão"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.side_effect = ConnectionError("Network error")

            data, status = simulation_service.get_template("daily", "average")

            assert status == 500
            assert "Unable to connect to server" in data["detail"]


class TestSimulationServiceRunDaily:
    def test_run_daily_success(self, simulation_service):
        """Testa simulação diária bem-sucedida"""
        expected = {
            "predicted_mw": 650000.5,
            "top_drivers": ["t2m", "L1_Load"],
        }
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = expected

            data, status = simulation_service.run_daily_simulation(
                template_name="average",
                year=2025,
                month=6,
                day_of_week=3,
                overrides={"t2m": 25.0},
            )

            assert status == 200
            assert data["predicted_mw"] == 650000.5
            assert data["top_drivers"] == ["t2m", "L1_Load"]
            mock_post.assert_called_once_with(
                "/simulations/daily",
                json={
                    "template_name": "average",
                    "year": 2025,
                    "month": 6,
                    "day_of_week": 3,
                    "overrides": {"t2m": 25.0},
                },
            )

    def test_run_daily_without_overrides(self, simulation_service):
        """Testa simulação diária sem overrides"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "predicted_mw": 500000.0, "top_drivers": ["sp", "day_of_week"]}

            data, status = simulation_service.run_daily_simulation(
                template_name="heatwave",
                year=2022,
                month=7,
                day_of_week=5,
            )

            assert status == 200
            # Verifica que overrides NÃO foi enviado no payload
            call_args = mock_post.call_args[1]["json"]
            assert "overrides" not in call_args

    def test_run_daily_validation_error(self, simulation_service):
        """Testa erro de validação (400)"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                "detail": "Erro de validação: 't2m' deve estar entre -40.0 e 55.0, recebeu 100.0"}

            data, status = simulation_service.run_daily_simulation(
                template_name="average",
                year=2025,
                month=6,
                day_of_week=3,
                overrides={"t2m": 100.0},
            )

            assert status == 400
            assert "validação" in data["detail"]

    def test_run_daily_no_active_model(self, simulation_service):
        """Testa quando não há modelo ativo"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                "detail": "Nenhum modelo ativo encontrado para daily"
            }

            data, status = simulation_service.run_daily_simulation(
                template_name="storm",
                year=2023,
                month=9,
                day_of_week=6,
            )

            assert status == 400
            assert "modelo ativo" in data["detail"]

    def test_run_daily_connection_error(self, simulation_service):
        """Testa erro de conexão"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.side_effect = TimeoutError("Timeout")

            data, status = simulation_service.run_daily_simulation(
                template_name="rainy",
                year=2024,
                month=2,
                day_of_week=1,
            )

            assert status == 500
            assert "Unable to connect to server" in data["detail"]


class TestSimulationServiceRunHourly:
    """Testes para o método run_hourly_simulation()"""

    def test_run_hourly_success(self, simulation_service):
        """Testa simulação horária bem-sucedida"""
        expected = {
            "predicted_mw": 28500.0,
            "top_drivers": ["hour", "t2m"],
        }
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = expected

            data, status = simulation_service.run_hourly_simulation(
                template_name="average",
                year=2025,
                month=9,
                day_of_week=3,
                hour=14,
                overrides={"sp": 950.0},
            )

            assert status == 200
            assert data["predicted_mw"] == 28500.0
            assert data["top_drivers"] == ["hour", "t2m"]
            mock_post.assert_called_once_with(
                "/simulations/hourly",
                json={
                    "template_name": "average",
                    "year": 2025,
                    "month": 9,
                    "day_of_week": 3,
                    "hour": 14,
                    "overrides": {"sp": 950.0},
                },
            )

    def test_run_hourly_without_overrides(self, simulation_service):
        """Testa simulação horária sem overrides"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "predicted_mw": 32000.0, "top_drivers": ["t2m", "L1_Load"]}

            data, status = simulation_service.run_hourly_simulation(
                template_name="heatwave",
                year=2021,
                month=8,
                day_of_week=5,
                hour=14,
            )

            assert status == 200
            call_args = mock_post.call_args[1]["json"]
            assert "overrides" not in call_args

    def test_run_hourly_validation_error(self, simulation_service):
        """Testa erro de validação (400)"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                "detail": "Erro de validação: 'u10' deve estar entre -69.4 e 69.4, recebeu 100.0"}

            data, status = simulation_service.run_hourly_simulation(
                template_name="storm",
                year=2023,
                month=9,
                day_of_week=6,
                hour=15,
                overrides={"u10": 100.0},
            )

            assert status == 400
            assert "u10" in data["detail"]

    def test_run_hourly_no_active_model(self, simulation_service):
        """Testa quando não há modelo ativo"""
        with patch.object(simulation_service.client, "post") as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                "detail": "Nenhum modelo ativo encontrado para hourly"
            }

            data, status = simulation_service.run_hourly_simulation(
                template_name="rainy",
                year=2020,
                month=3,
                day_of_week=1,
                hour=7,
            )

            assert status == 400
            assert "modelo ativo" in data["detail"]


class TestSimulationServiceGetAvailableTemplates:
    """Testes para o método get_available_templates()"""

    def test_get_available_templates_success(self, simulation_service):
        expected_templates = ["average", "heatwave", "storm", "rainy"]

        with patch.object(simulation_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "templates": expected_templates
            }

            templates = simulation_service.get_available_templates("daily")

            assert templates == expected_templates
            mock_get.assert_called_once_with(
                "/simulations/available-templates",
                params={"frequency": "daily"},
            )

    def test_get_available_templates_fallback_on_error(
            self, simulation_service):
        """Testa fallback quando backend falha"""
        with patch.object(simulation_service.client, "get") as mock_get:
            mock_get.side_effect = ConnectionError("Network error")

            templates = simulation_service.get_available_templates("daily")

            assert templates == ["average", "rainy", "storm", "heatwave"]

    def test_get_available_templates_fallback_on_500(self, simulation_service):
        """Testa fallback quando backend retorna 500"""
        with patch.object(simulation_service.client, "get") as mock_get:
            mock_get.return_value.status_code = 500
            mock_get.return_value.json.return_value = {"detail": "Error"}

            templates = simulation_service.get_available_templates("hourly")

            assert templates == ["average", "rainy", "storm", "heatwave"]


class TestTemplateWorker:
    """Testes para o TemplateWorker (QThread)"""

    def test_template_worker_run_success(self, qtbot):
        expected_data = {
            "frequency": "daily",
            "template_name": "average",
            "dataset_type": "full",
            "features": {"t2m": 13.78, "sp": 938.67},
        }
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_template.return_value = (expected_data, 200)

            worker = TemplateWorker("daily", "average")

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 200
            assert blocker.args[0]["frequency"] == "daily"
            assert blocker.args[0]["template_name"] == "average"

    def test_template_worker_run_error(self, qtbot):
        """Testa que o TemplateWorker emite erro 500 quando a API falha"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_template.return_value = (
                {"detail": "Internal Server Error"},
                500,
            )

            worker = TemplateWorker("daily", "average")

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 500

    def test_template_worker_run_404(self, qtbot):
        """Testa que o TemplateWorker trata template não encontrado"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_template.return_value = (
                {"detail": "Template not found"},
                404,
            )

            worker = TemplateWorker("daily", "nonexistent")

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 404

    def test_template_worker_run_exception(self, qtbot):
        """Testa que o TemplateWorker trata exceções inesperadas"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.get_template.side_effect = Exception(
                "Unexpected error")

            worker = TemplateWorker("daily", "average")

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 500


class TestDailySimulationWorker:
    """Testes para o DailySimulationWorker (QThread)"""

    def test_daily_simulation_worker_run_success(self, qtbot):
        """Testa que o DailySimulationWorker emite os dados corretos em caso de sucesso"""
        expected_data = {
            "predicted_mw": 650000.5,
            "top_drivers": ["t2m", "L1_Load"],
        }
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_daily_simulation.return_value = (
                expected_data, 200)

            worker = DailySimulationWorker(
                template_name="average",
                year=2025,
                month=6,
                day_of_week=3,
                overrides={"t2m": 25.0},
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 200
            assert blocker.args[0]["predicted_mw"] == 650000.5

    def test_daily_simulation_worker_run_without_overrides(self, qtbot):
        """Testa que o DailySimulationWorker funciona sem overrides"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_daily_simulation.return_value = (
                {"predicted_mw": 500000.0, "top_drivers": ["sp", "day_of_week"]},
                200,
            )

            worker = DailySimulationWorker(
                template_name="heatwave",
                year=2022,
                month=7,
                day_of_week=5,
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 200

    def test_daily_simulation_worker_run_validation_error(self, qtbot):
        """Testa que o DailySimulationWorker trata erro de validação (400)"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_daily_simulation.return_value = (
                {"detail": "Erro de validação: 't2m' deve estar entre -40.0 e 55.0, recebeu 100.0"},
                400,
            )

            worker = DailySimulationWorker(
                template_name="average",
                year=2025,
                month=6,
                day_of_week=3,
                overrides={"t2m": 100.0},
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 400
            assert "validação" in blocker.args[0]["detail"]

    def test_daily_simulation_worker_run_no_active_model(self, qtbot):
        """Testa que o DailySimulationWorker trata quando não há modelo ativo"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_daily_simulation.return_value = (
                {"detail": "Nenhum modelo ativo encontrado para daily"},
                400,
            )

            worker = DailySimulationWorker(
                template_name="storm",
                year=2023,
                month=9,
                day_of_week=6,
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 400

    def test_daily_simulation_worker_run_exception(self, qtbot):
        """Testa que o DailySimulationWorker trata exceções inesperadas"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_daily_simulation.side_effect = Exception(
                "Network error")

            worker = DailySimulationWorker(
                template_name="rainy", year=2024, month=2, day_of_week=1,
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 500
            assert "Network error" in blocker.args[0]["detail"]


class TestHourlySimulationWorker:
    """Testes para o HourlySimulationWorker (QThread)"""

    def test_hourly_simulation_worker_run_success(self, qtbot):
        """Testa que o HourlySimulationWorker emite os dados corretos em caso de sucesso"""
        expected_data = {
            "predicted_mw": 28500.0,
            "top_drivers": ["hour", "t2m"],
        }
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_hourly_simulation.return_value = (
                expected_data, 200)

            worker = HourlySimulationWorker(
                template_name="average",
                year=2025,
                month=9,
                day_of_week=3,
                hour=14,
                overrides={"sp": 950.0},
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 200
            assert blocker.args[0]["predicted_mw"] == 28500.0

    def test_hourly_simulation_worker_run_without_overrides(self, qtbot):
        """Testa que o HourlySimulationWorker funciona sem overrides"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_hourly_simulation.return_value = (
                {"predicted_mw": 32000.0, "top_drivers": ["t2m", "L1_Load"]},
                200,
            )

            worker = HourlySimulationWorker(
                template_name="heatwave",
                year=2021,
                month=8,
                day_of_week=5,
                hour=14,
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 200

    def test_hourly_simulation_worker_run_validation_error(self, qtbot):
        """Testa que o HourlySimulationWorker trata erro de validação (400)"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_hourly_simulation.return_value = (
                {"detail": "Erro de validação: 'u10' deve estar entre -69.4 e 69.4, recebeu 100.0"},
                400,
            )

            worker = HourlySimulationWorker(
                template_name="storm",
                year=2023,
                month=9,
                day_of_week=6,
                hour=15,
                overrides={"u10": 100.0},
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 400
            assert "u10" in blocker.args[0]["detail"]

    def test_hourly_simulation_worker_run_no_active_model(self, qtbot):
        """Testa que o HourlySimulationWorker trata quando não há modelo ativo"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_hourly_simulation.return_value = (
                {"detail": "Nenhum modelo ativo encontrado para hourly"},
                400,
            )

            worker = HourlySimulationWorker(
                template_name="rainy",
                year=2020,
                month=3,
                day_of_week=1,
                hour=7,
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 400

    def test_hourly_simulation_worker_run_exception(self, qtbot):
        """Testa que o HourlySimulationWorker trata exceções inesperadas"""
        with patch(
            "app.ui.main_window.SimulationService"
        ) as mock_service_class:
            mock_instance = mock_service_class.return_value
            mock_instance.run_hourly_simulation.side_effect = Exception(
                "Network error")

            worker = HourlySimulationWorker(
                template_name="average",
                year=2025,
                month=6,
                day_of_week=2,
                hour=10,
            )

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[1] == 500
            assert "Network error" in blocker.args[0]["detail"]
