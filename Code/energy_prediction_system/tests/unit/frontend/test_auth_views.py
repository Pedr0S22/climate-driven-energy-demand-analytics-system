from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt

from src.app.ui.main_window import LoginWorker, LogoutWorker, MainWindow, RegisterWorker


@pytest.fixture
def app_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    return window


def test_navigation_between_login_and_register(app_window, qtbot):
    assert app_window.stack.currentIndex() == 0

    qtbot.mouseClick(app_window.ui_login.register_link, Qt.MouseButton.LeftButton)
    assert app_window.stack.currentIndex() == 1  # Mudou para Registo

    qtbot.mouseClick(app_window.ui_register.login_link, Qt.MouseButton.LeftButton)
    assert app_window.stack.currentIndex() == 0  # Voltou ao Login


# --- LOGIN ---


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_login_validation_failure(mock_warning, app_window, qtbot):
    app_window.ui_login.email_input.setText("invalid_email")
    app_window.ui_login.pass_input.setText("123")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)

    mock_warning.assert_called_once()
    assert app_window.stack.currentIndex() == 0


def test_login_success_admin(mock_api_200, app_window, qtbot):
    app_window.ui_login.email_input.setText("admin@example.com")
    app_window.ui_login.pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)

    qtbot.waitUntil(lambda: app_window.stack.currentIndex() == 2)

    assert app_window.ui_login.email_input.text() == ""


def test_login_success_client(mock_api_response, app_window, qtbot):
    mock_api_response(status_code=200, json_data={"role": "client", "access_token": "fake_token"})

    app_window.ui_login.email_input.setText("user@example.com")
    app_window.ui_login.pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: app_window.stack.currentIndex() == 6)

    assert app_window.stack.currentIndex() == 6


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_login_invalid_credentials(mock_warning, mock_api_401, app_window, qtbot):
    app_window.ui_login.email_input.setText("wrong@example.com")
    app_window.ui_login.pass_input.setText("WrongPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)

    mock_warning.assert_called_once_with(app_window, "Login Failed", "Incorrect credentials.")
    assert app_window.stack.currentIndex() == 0


# --- REGISTER ---


@patch("src.app.ui.main_window.QMessageBox.information")
def test_register_success(mock_info, mock_api_response, app_window, qtbot):
    mock_api_response(status_code=201, json_data={"message": "User registered successfully"})
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("newuser")
    app_window.ui_register.email_input.setText("new@example.com")
    app_window.ui_register.pass_input.setText("ValidPass123!")
    app_window.ui_register.conf_pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_info.called)
    mock_info.assert_called_once()
    assert app_window.stack.currentIndex() == 0
    assert app_window.ui_register.email_input.text() == ""


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_register_duplicate_email(mock_warning, mock_api_409, app_window, qtbot):
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("dupuser")
    app_window.ui_register.email_input.setText("dup@example.com")
    app_window.ui_register.pass_input.setText("ValidPass123!")
    app_window.ui_register.conf_pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)
    mock_warning.assert_called_once()
    assert app_window.stack.currentIndex() == 1
    assert app_window.ui_register.email_input.text() == ""


# --- LOGOUT ---


@patch("src.app.ui.main_window.SessionManager.clear_session")
def test_logout_functionality(mock_clear_session, app_window, qtbot):
    app_window.stack.setCurrentIndex(6)

    qtbot.mouseClick(app_window.ui_user_homepage.logout_btn, Qt.MouseButton.LeftButton)
    mock_clear_session.assert_called_once()

    assert app_window.stack.currentIndex() == 0


@patch("src.app.ui.main_window.QMessageBox.critical")
def test_login_server_error(mock_critical, mock_api_500, app_window, qtbot):
    app_window.ui_login.email_input.setText("user@example.com")
    app_window.ui_login.pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_critical.called)
    mock_critical.assert_called_once_with(app_window, "Login Error", "Internal Server Error")
    assert app_window.stack.currentIndex() == 0


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_register_validation_failure(mock_warning, app_window, qtbot):
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("user")
    app_window.ui_register.email_input.setText("invalid_email")
    app_window.ui_register.pass_input.setText("123")
    app_window.ui_register.conf_pass_input.setText("456")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)

    mock_warning.assert_called_once()
    assert app_window.stack.currentIndex() == 1


@patch("src.app.ui.main_window.QMessageBox.critical")
def test_register_server_error(mock_critical, mock_api_500, app_window, qtbot):
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("newuser")
    app_window.ui_register.email_input.setText("new@example.com")
    app_window.ui_register.pass_input.setText("ValidPass123!")
    app_window.ui_register.conf_pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_critical.called)
    mock_critical.assert_called_once_with(app_window, "Registration Error", "Internal Server Error")
    assert app_window.stack.currentIndex() == 1


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_login_account_locked(mock_warning, mock_api_403, app_window, qtbot):
    app_window.ui_login.email_input.setText("locked@example.com")
    app_window.ui_login.pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)
    mock_warning.assert_called_once_with(app_window, "Login Failed", "Account locked or access denied.")
    assert app_window.stack.currentIndex() == 0


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_login_invalid_request_format(mock_warning, mock_api_400, app_window, qtbot):
    app_window.ui_login.email_input.setText("badformat@example.com")
    app_window.ui_login.pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)
    mock_warning.assert_called_once_with(app_window, "Login Failed", "Invalid Request format.")
    assert app_window.stack.currentIndex() == 0


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_register_invalid_input_format(mock_warning, mock_api_response, app_window, qtbot):
    mock_api_response(status_code=400, json_data={"detail": "Password too weak"})
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("newuser")
    app_window.ui_register.email_input.setText("new@example.com")
    app_window.ui_register.pass_input.setText("ValidPass123!")
    app_window.ui_register.conf_pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)
    mock_warning.assert_called_once_with(app_window, "Registration Failed", "Password too weak")
    assert app_window.stack.currentIndex() == 1


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_login_invalid_request_format_list(mock_warning, mock_api_response, app_window, qtbot):
    mock_api_response(status_code=400, json_data={"detail": [{"msg": "Field required"}]})

    app_window.ui_login.email_input.setText("badformat@example.com")
    app_window.ui_login.pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_login.login_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)
    mock_warning.assert_called_once_with(app_window, "Login Failed", "Field required")


@patch("src.app.ui.main_window.QMessageBox.warning")
def test_register_invalid_input_format_list(mock_warning, mock_api_response, app_window, qtbot):
    mock_api_response(status_code=400, json_data={"detail": [{"msg": "Password too weak array"}]})
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("newuser")
    app_window.ui_register.email_input.setText("new@example.com")
    app_window.ui_register.pass_input.setText("ValidPass123!")
    app_window.ui_register.conf_pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_warning.called)
    mock_warning.assert_called_once_with(app_window, "Registration Failed", "Password too weak array")


@patch("src.app.ui.main_window.QMessageBox.critical")
def test_register_server_error_list(mock_critical, mock_api_response, app_window, qtbot):
    mock_api_response(status_code=500, json_data={"detail": [{"msg": "Unknown array error"}]})
    app_window.stack.setCurrentIndex(1)

    app_window.ui_register.user_input.setText("newuser")
    app_window.ui_register.email_input.setText("new@example.com")
    app_window.ui_register.pass_input.setText("ValidPass123!")
    app_window.ui_register.conf_pass_input.setText("ValidPass123!")

    qtbot.mouseClick(app_window.ui_register.signup_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: mock_critical.called)
    mock_critical.assert_called_once_with(app_window, "Registration Error", "Unknown array error")


# --- TESTES DE COBERTURA DOS WORKERS (QTHREADS) ---


def test_login_worker_run_success(qtbot, mock_api_200):
    worker = LoginWorker("admin@example.com", "ValidPass123!")
    # Usar qtbot para escutar o sinal emitido
    with qtbot.waitSignal(worker.finished) as blocker:
        worker.run()  # Executar de forma síncrona (run em vez de start) para o coverage

    assert blocker.args[1] == 200


def test_register_worker_run_success(qtbot, mock_api_response):
    mock_api_response(status_code=201, json_data={"message": "ok"})
    worker = RegisterWorker("newuser", "new@example.com", "ValidPass123!")

    with qtbot.waitSignal(worker.finished) as blocker:
        worker.run()

    assert blocker.args[1] == 201


def test_logout_worker_run_success(qtbot):
    worker = LogoutWorker()
    with qtbot.waitSignal(worker.finished):
        worker.run()


@patch("src.app.ui.main_window.AuthService")
def test_login_worker_run_exception(mock_auth_service_class, qtbot):
    # Forçamos a instância do AuthService a lançar o erro
    mock_instance = mock_auth_service_class.return_value
    mock_instance.login_user.side_effect = Exception("Network failure")

    worker = LoginWorker("admin@example.com", "ValidPass123!")

    with qtbot.waitSignal(worker.finished) as blocker:
        worker.run()

    assert blocker.args[1] == 500
    assert blocker.args[0]["detail"] == "Network failure"


@patch("src.app.ui.main_window.AuthService")
def test_register_worker_run_exception(mock_auth_service_class, qtbot):
    mock_instance = mock_auth_service_class.return_value
    mock_instance.register_user.side_effect = Exception("Timeout Error")

    worker = RegisterWorker("newuser", "new@example.com", "ValidPass123!")

    with qtbot.waitSignal(worker.finished) as blocker:
        worker.run()

    assert blocker.args[1] == 500
    assert blocker.args[0]["detail"] == "Timeout Error"


@patch("src.app.ui.main_window.AuthService")
def test_logout_worker_run_exception(mock_auth_service_class, qtbot):
    mock_instance = mock_auth_service_class.return_value
    mock_instance.logout_user.side_effect = Exception("Logout Error")

    worker = LogoutWorker()

    with qtbot.waitSignal(worker.finished):
        worker.run()
