import os
from unittest.mock import patch

import pytest

from src.app.client.models_service import ModelsService
from src.app.client.simulation_service import SimulationService
from src.app.manager.session_manager import SessionManager
from src.app.ui.main_window import DailySimulationWorker, HourlySimulationWorker, TemplateWorker
from src.app.ui.views.model_management_view import ActivateModelWorker, LoadModelsWorker

os.environ.setdefault("KEYRING_SERVICE_NAME", "energy_pred_test_service")
os.environ.setdefault("KEYRING_TOKEN_KEY", "test_token")
os.environ.setdefault("KEYRING_ROLE_KEY", "test_role")
# keyring
fake_keyring: dict = {}


def _set_password(service, username, password):
    fake_keyring[(service, username)] = password


def _get_password(service, username):
    return fake_keyring.get((service, username))


def _delete_password(service, username):
    if (service, username) in fake_keyring:
        del fake_keyring[(service, username)]
    else:
        import keyring

        raise keyring.errors.PasswordDeleteError("Not found")


@pytest.fixture(autouse=True)
def mock_keyring():
    fake_keyring.clear()
    with (
        patch("src.app.manager.session_manager.keyring.set_password", side_effect=_set_password),
        patch("src.app.manager.session_manager.keyring.get_password", side_effect=_get_password),
        patch("src.app.manager.session_manager.keyring.delete_password", side_effect=_delete_password),
    ):
        yield


@pytest.fixture(autouse=True)
def clean_session():
    SessionManager.clear_session()
    yield
    SessionManager.clear_session()


def _make_response(status_code: int, json_body):
    """Cria um mock de resposta requests com status_code e json() configurados."""
    from unittest.mock import MagicMock

    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    return resp


class TestModelsServiceContract:
    # --- get_all_models ---
    @patch("src.app.client.api_client.requests.get")
    def test_get_all_models_hits_correct_endpoint(self, mock_get):
        """GET /models/ — verifica URL completo enviado ao requests."""

        mock_get.return_value = _make_response(200, [])

        ModelsService().get_all_models()

        called_url: str = mock_get.call_args[0][0]
        assert called_url.endswith("/models/"), f"URL incorrecto: {called_url!r} — deve terminar em '/models/'"

    @patch("src.app.client.api_client.requests.get")
    def test_get_all_models_sends_no_body(self, mock_get):
        """GET /models/ — pedido GET não deve enviar json body."""

        mock_get.return_value = _make_response(200, [])

        ModelsService().get_all_models()

        call_kwargs = mock_get.call_args[1] if mock_get.call_args[1] else {}
        assert "json" not in call_kwargs or call_kwargs.get("json") is None, "GET /models/ não deve enviar body JSON"

    # --- activate_model ---

    @patch("src.app.client.api_client.requests.patch")
    def test_activate_model_hits_correct_endpoint(self, mock_patch):
        """PATCH /models/{id}/activate — verifica URL com ID correcto."""

        mock_patch.return_value = _make_response(200, {"model_name_id": 7, "is_active": True})

        ModelsService().activate_model(7)

        called_url: str = mock_patch.call_args[0][0]
        assert "/models/7/activate" in called_url, f"URL incorrecto: {called_url!r} — deve conter '/models/7/activate'"

    @patch("src.app.client.api_client.requests.patch")
    def test_activate_model_sends_correct_payload(self, mock_patch):
        """PATCH /models/{id}/activate — body deve conter {is_active: true}."""

        mock_patch.return_value = _make_response(200, {"model_name_id": 3, "is_active": True})

        ModelsService().activate_model(3)

        sent_json = mock_patch.call_args[1].get("json", {})
        assert sent_json == {"is_active": True}, f"Payload incorrecto: {sent_json!r} — deve ser {{'is_active': True}}"

    @patch("src.app.client.api_client.requests.patch")
    def test_activate_different_model_ids_use_different_urls(self, mock_patch):
        """IDs diferentes devem gerar URLs diferentes — sem hardcoding."""

        mock_patch.return_value = _make_response(200, {"is_active": True})

        service = ModelsService()
        service.activate_model(1)
        service.activate_model(99)

        urls = [c[0][0] for c in mock_patch.call_args_list]
        assert "/models/1/activate" in urls[0]
        assert "/models/99/activate" in urls[1]
        assert urls[0] != urls[1], "URLs para IDs diferentes não devem ser iguais"


class TestSimulationServiceContract:
    """
    Garante que SimulationService constrói os pedidos HTTP correctos.
    O APIClient é real; só requests é mockado.
    """

    # --- get_template ---

    @patch("src.app.client.api_client.requests.post")
    def test_get_template_hits_correct_endpoint(self, mock_post):
        """POST /simulations/templates — verifica URL."""

        mock_post.return_value = _make_response(200, {"frequency": "daily", "template_name": "average", "features": {}})

        SimulationService().get_template("daily", "average")

        called_url: str = mock_post.call_args[0][0]
        assert called_url.endswith("/simulations/templates"), f"URL incorrecto: {called_url!r}"

    @patch("src.app.client.api_client.requests.post")
    def test_get_template_sends_correct_payload(self, mock_post):
        """POST /simulations/templates — body deve ter frequency e template_name."""

        mock_post.return_value = _make_response(200, {"frequency": "hourly", "template_name": "storm", "features": {}})

        SimulationService().get_template("hourly", "storm")

        sent_json = mock_post.call_args[1].get("json", {})
        assert sent_json == {"frequency": "hourly", "template_name": "storm"}, f"Payload incorrecto: {sent_json!r}"

    # --- run_daily_simulation ---

    @patch("src.app.client.api_client.requests.post")
    def test_run_daily_hits_correct_endpoint(self, mock_post):
        """POST /simulations/daily — verifica URL."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 500000.0})

        SimulationService().run_daily_simulation("average", 2025, 6, 3)

        called_url: str = mock_post.call_args[0][0]
        assert called_url.endswith("/simulations/daily"), f"URL incorrecto: {called_url!r}"

    @patch("src.app.client.api_client.requests.post")
    def test_run_daily_payload_without_overrides(self, mock_post):
        """Sem overrides → campo 'overrides' NÃO deve existir no payload."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 500000.0})

        SimulationService().run_daily_simulation("average", 2025, 6, 3, overrides=None)

        sent_json = mock_post.call_args[1].get("json", {})
        assert "overrides" not in sent_json, "Quando overrides=None, o campo não deve ser enviado no payload"
        assert sent_json == {
            "template_name": "average",
            "year": 2025,
            "month": 6,
            "day_of_week": 3,
        }

    @patch("src.app.client.api_client.requests.post")
    def test_run_daily_payload_empty_overrides_not_sent(self, mock_post):
        """overrides={} → campo 'overrides' NÃO deve existir no payload."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 500000.0})

        SimulationService().run_daily_simulation("average", 2025, 6, 3, overrides={})

        sent_json = mock_post.call_args[1].get("json", {})
        assert "overrides" not in sent_json, "Quando overrides={}, o campo não deve ser enviado no payload"

    @patch("src.app.client.api_client.requests.post")
    def test_run_daily_payload_with_overrides(self, mock_post):
        """Com overrides → campo 'overrides' deve existir no payload com os valores correctos."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 700000.0})

        SimulationService().run_daily_simulation("heatwave", 2025, 7, 4, overrides={"t2m": 40.0, "sp": 950.0})

        sent_json = mock_post.call_args[1].get("json", {})
        assert "overrides" in sent_json, "Com overrides preenchidos, o campo deve estar no payload"
        assert sent_json["overrides"] == {"t2m": 40.0, "sp": 950.0}
        assert sent_json["template_name"] == "heatwave"
        assert sent_json["year"] == 2025
        assert sent_json["month"] == 7
        assert sent_json["day_of_week"] == 4

    # --- run_hourly_simulation ---

    @patch("src.app.client.api_client.requests.post")
    def test_run_hourly_hits_correct_endpoint(self, mock_post):
        """POST /simulations/hourly — verifica URL."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 30000.0})

        SimulationService().run_hourly_simulation("average", 2025, 6, 3, hour=14)

        called_url: str = mock_post.call_args[0][0]
        assert called_url.endswith("/simulations/hourly"), f"URL incorrecto: {called_url!r}"

    @patch("src.app.client.api_client.requests.post")
    def test_run_hourly_payload_includes_hour(self, mock_post):
        """Payload da simulação horária deve incluir o campo 'hour'."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 30000.0})

        SimulationService().run_hourly_simulation("storm", 2023, 9, 6, hour=15)

        sent_json = mock_post.call_args[1].get("json", {})
        assert "hour" in sent_json, "Payload de simulação horária deve conter 'hour'"
        assert sent_json["hour"] == 15

    @patch("src.app.client.api_client.requests.post")
    def test_run_hourly_payload_full_structure(self, mock_post):
        """Payload completo da simulação horária com overrides."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 28500.0})

        SimulationService().run_hourly_simulation("rainy", 2024, 11, 2, hour=8, overrides={"u10": 5.5})

        sent_json = mock_post.call_args[1].get("json", {})
        assert sent_json == {
            "template_name": "rainy",
            "year": 2024,
            "month": 11,
            "day_of_week": 2,
            "hour": 8,
            "overrides": {"u10": 5.5},
        }

    @patch("src.app.client.api_client.requests.post")
    def test_run_hourly_payload_without_overrides(self, mock_post):
        """Sem overrides → 'hour' presente mas 'overrides' ausente."""

        mock_post.return_value = _make_response(200, {"predicted_mw": 28500.0})

        SimulationService().run_hourly_simulation("average", 2025, 6, 3, hour=10)

        sent_json = mock_post.call_args[1].get("json", {})
        assert "hour" in sent_json
        assert "overrides" not in sent_json

    # --- get_available_templates ---

    @patch("src.app.client.api_client.requests.get")
    def test_get_available_templates_sends_frequency_as_query_param(self, mock_get):
        """GET /simulations/available-templates?frequency=daily — verifica query param."""

        mock_get.return_value = _make_response(200, {"templates": ["average", "heatwave", "storm", "rainy"]})

        SimulationService().get_available_templates("daily")

        called_url: str = mock_get.call_args[0][0]
        assert called_url.endswith("/simulations/available-templates"), f"URL incorrecto: {called_url!r}"
        call_kwargs = mock_get.call_args[1] if mock_get.call_args[1] else {}
        assert (
            call_kwargs.get("params", {}).get("frequency") == "daily"
        ), "O query param 'frequency' deve ser enviado com o valor correcto"

    @patch("src.app.client.api_client.requests.get")
    def test_get_available_templates_hourly_query_param(self, mock_get):
        """Verifica que frequency=hourly é enviado correctamente."""

        mock_get.return_value = _make_response(200, {"templates": ["average", "heatwave", "storm", "rainy"]})

        SimulationService().get_available_templates("hourly")

        call_kwargs = mock_get.call_args[1] if mock_get.call_args[1] else {}
        assert call_kwargs.get("params", {}).get("frequency") == "hourly"


class TestDailySimulationWorkerContract:
    """
    DailySimulationWorker real → SimulationService mockado.
    Verifica que o Worker passa os argumentos certos ao Service.
    """

    def test_worker_passes_all_args_to_service(self, qtbot):
        """Worker deve chamar run_daily_simulation com exactamente os argumentos recebidos."""
        with patch("src.app.ui.main_window.SimulationService") as MockService:
            instance = MockService.return_value
            instance.run_daily_simulation.return_value = ({"predicted_mw": 500000.0}, 200)

            worker = DailySimulationWorker(
                template_name="heatwave",
                year=2025,
                month=7,
                day_of_week=4,
                overrides={"t2m": 38.0},
            )

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            instance.run_daily_simulation.assert_called_once_with(
                template_name="heatwave",
                year=2025,
                month=7,
                day_of_week=4,
                overrides={"t2m": 38.0},
            )

    def test_worker_passes_none_overrides_to_service(self, qtbot):
        """Worker sem overrides deve passar overrides=None ao Service."""
        with patch("src.app.ui.main_window.SimulationService") as MockService:
            instance = MockService.return_value
            instance.run_daily_simulation.return_value = ({"predicted_mw": 500000.0}, 200)

            worker = DailySimulationWorker("average", 2025, 6, 3)

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            call_kwargs = instance.run_daily_simulation.call_args[1]
            assert call_kwargs.get("overrides") is None

    def test_worker_emits_service_data_unchanged(self, qtbot):
        """Worker deve emitir exactamente o que o Service retorna, sem modificar."""
        expected = {"predicted_mw": 123456.78, "top_drivers": ["t2m", "sp"]}

        with patch("src.app.ui.main_window.SimulationService") as MockService:
            MockService.return_value.run_daily_simulation.return_value = (expected, 200)

            worker = DailySimulationWorker("average", 2025, 6, 3)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            assert blocker.args[0] is expected, "Worker não deve modificar nem copiar os dados do Service"
            assert blocker.args[1] == 200


class TestHourlySimulationWorkerContract:
    """
    HourlySimulationWorker real → SimulationService mockado.
    """

    def test_worker_passes_all_args_including_hour(self, qtbot):
        """Worker deve passar 'hour' correctamente ao Service."""
        with patch("src.app.ui.main_window.SimulationService") as MockService:
            instance = MockService.return_value
            instance.run_hourly_simulation.return_value = ({"predicted_mw": 28500.0}, 200)

            worker = HourlySimulationWorker(
                template_name="storm",
                year=2023,
                month=9,
                day_of_week=6,
                hour=15,
                overrides={"u10": 12.0},
            )

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            instance.run_hourly_simulation.assert_called_once_with(
                template_name="storm",
                year=2023,
                month=9,
                day_of_week=6,
                hour=15,
                overrides={"u10": 12.0},
            )

    def test_worker_passes_correct_hour_zero(self, qtbot):
        """hour=0 (meia-noite) deve ser passado correctamente — não confundido com falsy."""
        with patch("src.app.ui.main_window.SimulationService") as MockService:
            instance = MockService.return_value
            instance.run_hourly_simulation.return_value = ({"predicted_mw": 20000.0}, 200)

            worker = HourlySimulationWorker("average", 2025, 1, 1, hour=0)

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            call_kwargs = instance.run_hourly_simulation.call_args[1]
            assert call_kwargs.get("hour") == 0, "hour=0 (meia-noite) deve ser preservado — não descartado como falsy"


class TestTemplateWorkerContract:
    """
    TemplateWorker real → SimulationService mockado.
    """

    def test_worker_passes_frequency_and_template_to_service(self, qtbot):
        """Worker deve chamar get_template com frequency e template_name correctos."""
        with patch("src.app.ui.main_window.SimulationService") as MockService:
            instance = MockService.return_value
            instance.get_template.return_value = (
                {"frequency": "hourly", "template_name": "rainy", "features": {}},
                200,
            )

            worker = TemplateWorker("hourly", "rainy")

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            instance.get_template.assert_called_once_with("hourly", "rainy")


class TestLoadModelsWorkerContract:
    """
    LoadModelsWorker real → ModelsService mockado.
    """

    def test_worker_calls_get_all_models_with_no_args(self, qtbot):
        """LoadModelsWorker deve chamar get_all_models() sem argumentos."""
        with patch("src.app.ui.views.model_management_view.ModelsService") as MockService:
            instance = MockService.return_value
            instance.get_all_models.return_value = ([], 200)

            worker = LoadModelsWorker()

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            instance.get_all_models.assert_called_once_with()

    def test_worker_emits_empty_list_and_error_on_non_200(self, qtbot):
        """Status != 200 → worker emite ([], mensagem_de_erro)."""
        with patch("src.app.ui.views.model_management_view.ModelsService") as MockService:
            MockService.return_value.get_all_models.return_value = ({"detail": "Forbidden"}, 403)

            worker = LoadModelsWorker()

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            models, error = blocker.args
            assert models == []
            assert "Forbidden" in error


class TestActivateModelWorkerContract:
    """
    ActivateModelWorker real → ModelsService mockado.
    """

    def test_worker_passes_model_id_to_service(self, qtbot):
        """Worker deve chamar activate_model com exactamente o ID recebido."""
        with patch("src.app.ui.views.model_management_view.ModelsService") as MockService:
            instance = MockService.return_value
            instance.activate_model.return_value = ({"model_name_id": 42, "is_active": True}, 200)

            worker = ActivateModelWorker(42)

            with qtbot.waitSignal(worker.finished, timeout=5000):
                worker.run()

            instance.activate_model.assert_called_once_with(42)

    def test_worker_emits_none_and_error_message_on_failure(self, qtbot):
        """Falha na activação → worker emite (None, mensagem_de_erro)."""
        with patch("src.app.ui.views.model_management_view.ModelsService") as MockService:
            MockService.return_value.activate_model.return_value = ({"detail": "Model with id 99 not found"}, 404)

            worker = ActivateModelWorker(99)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            data, error = blocker.args
            assert data is None
            assert "not found" in error

    def test_worker_emits_data_and_empty_error_on_success(self, qtbot):
        """Sucesso → worker emite (data, '') onde error é string vazia."""
        response = {"model_name_id": 5, "is_active": True}

        with patch("src.app.ui.views.model_management_view.ModelsService") as MockService:
            MockService.return_value.activate_model.return_value = (response, 200)

            worker = ActivateModelWorker(5)

            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.run()

            data, error = blocker.args
            assert data == response
            assert error == ""
