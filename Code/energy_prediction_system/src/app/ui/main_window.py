import logging

from app.client.auth_service import AuthService
from app.client.prediction_service import PredictionService
from app.manager.session_manager import SessionManager
from app.utils.validators import validate_login_input, validate_prediction_params, validate_registration_input
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from .views.admin_homepage import Ui_MainWindow as Ui_AdminHome
from .views.daily_prediction_view import Ui_DailyPredictionAdminWindow
from .views.hourly_prediction_view import Ui_HourlyPredictionAdminWindow
from .views.login_view import Ui_LoginWindow
from .views.model_management_view import Ui_ModelManagementWindow
from .views.register_view import Ui_RegisterWindow
from .views.user_homepage import Ui_UserMainWindow

logger = logging.getLogger(__name__)


class LoginWorker(QThread):
    finished = pyqtSignal(object, int)

    def __init__(self, email, password):
        super().__init__()
        self.email = email
        self.password = password

    def run(self):
        auth_service = AuthService()
        try:
            data, status = auth_service.login_user(self.email, self.password)
            self.finished.emit(data, status)
        except Exception as e:
            logger.error(f"LoginWorker error: {e}")
            self.finished.emit({"detail": "An internal error occurred. Please try again later."}, 500)


class ProfileWorker(QThread):
    finished = pyqtSignal(object, int)

    def run(self):
        auth_service = AuthService()
        try:
            data, status = auth_service.get_user_profile()
            self.finished.emit(data, status)
        except Exception as e:
            logger.error(f"ProfileWorker error: {e}")
            self.finished.emit({"detail": str(e)}, 500)


class RegisterWorker(QThread):
    finished = pyqtSignal(object, int)

    def __init__(self, user, email, password):
        super().__init__()
        self.user = user
        self.email = email
        self.password = password

    def run(self):
        auth_service = AuthService()
        try:
            data, status = auth_service.register_user(self.user, self.email, self.password)
            self.finished.emit(data, status)
        except Exception as e:
            logger.error(f"RegisterWorker error: {e}")
            self.finished.emit({"detail": "An internal error occurred during registration."}, 500)


class LogoutWorker(QThread):
    finished = pyqtSignal()

    def run(self):
        try:
            auth_service = AuthService()
            auth_service.logout_user()
        except Exception as e:
            logger.error(f"LogoutWorker error: {e}")
        self.finished.emit()


class PredictionWorker(QThread):
    finished = pyqtSignal(object, int, str)

    def __init__(self, frequency, historical_points, predicted_points):
        super().__init__()
        self.frequency = frequency
        self.historical_points = historical_points
        self.predicted_points = predicted_points

    def run(self):
        service = PredictionService()
        try:
            data, status = service.get_prediction(self.frequency, self.historical_points, self.predicted_points)
            self.finished.emit(data, status, self.frequency)
        except Exception as e:
            logger.error(f"PredictionWorker error: {e}")
            self.finished.emit({"detail": str(e)}, 500, self.frequency)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing MainWindow...")
        self.setWindowTitle("Energy Demand Prediction System")
        self.showMaximized()

        # O StackedWidget permite trocar de página sem abrir janelas novas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Criar os widgets para cada página
        self.login_page = QMainWindow()
        self.register_page = QMainWindow()
        self.admin_page = QMainWindow()
        self.daily_pred_admin_page = QMainWindow()
        self.hourly_pred_admin_page = QMainWindow()
        self.model_mgmt_page = QMainWindow()
        self.user_homepage = QMainWindow()

        # Configurar as UIs nos seus respetivos widgets
        self.ui_login = Ui_LoginWindow()
        self.ui_login.setupUi(self.login_page)

        self.ui_register = Ui_RegisterWindow()
        self.ui_register.setupUi(self.register_page)

        self.ui_admin = Ui_AdminHome()
        self.ui_admin.setupUi(self.admin_page)

        self.ui_daily_pred = Ui_DailyPredictionAdminWindow()
        self.ui_daily_pred.setupUi(self.daily_pred_admin_page)

        self.ui_hourly_pred = Ui_HourlyPredictionAdminWindow()
        self.ui_hourly_pred.setupUi(self.hourly_pred_admin_page)

        self.ui_model_mgmt = Ui_ModelManagementWindow()
        self.ui_model_mgmt.setupUi(self.model_mgmt_page)

        self.ui_user_homepage = Ui_UserMainWindow()
        self.ui_user_homepage.setupUi(self.user_homepage)  # Criar um QMainWindow

        # Adicionar à pilha (Stack)
        self.stack.addWidget(self.login_page)  # Índice 0
        self.stack.addWidget(self.register_page)  # Índice 1
        self.stack.addWidget(self.admin_page)  # Índice 2
        self.stack.addWidget(self.daily_pred_admin_page)  # Índice 3
        self.stack.addWidget(self.hourly_pred_admin_page)  # Índice 4
        self.stack.addWidget(self.model_mgmt_page)  # Índice 5
        self.stack.addWidget(self.user_homepage)  # Índice 6

        self.stack.setCurrentIndex(0)  # Iniciar na Home por agora para testes

        # --- LIGAÇÕES ---

        # No Login: Ir para Registo
        self.ui_login.register_link.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        # No Registo: Voltar para Login
        self.ui_register.login_link.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Na Home: Botão Logout
        self.ui_admin.pushButton.clicked.connect(self.handle_logout)

        # Na Home: Navegação Sidebar
        self.ui_admin.home_btn.clicked.connect(self.handle_nav_to_home)
        self.ui_admin.daily_btn.clicked.connect(self.handle_nav_to_daily)
        self.ui_admin.hourly_btn.clicked.connect(self.handle_nav_to_hourly)
        self.ui_admin.model_mgmt_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))

        # Na Home: Navegação Dashboard
        self.ui_admin.daily_button.clicked.connect(self.handle_nav_to_daily)
        self.ui_admin.hourly_button.clicked.connect(self.handle_nav_to_hourly)
        self.ui_admin.model_mgmt_button.clicked.connect(lambda: self.stack.setCurrentIndex(5))

        self.ui_admin.sim_daily_button.clicked.connect(lambda: print("Go to Daily Simulation"))
        self.ui_admin.sim_hourly_button.clicked.connect(lambda: print("Go to Hourly Simulation"))

        # Na Daily Pred Admin
        self.ui_daily_pred.logout_btn.clicked.connect(self.handle_logout)
        self.ui_daily_pred.home_btn.clicked.connect(self.handle_nav_to_home)
        self.ui_daily_pred.daily_btn.clicked.connect(self.handle_nav_to_daily)
        self.ui_daily_pred.hourly_btn.clicked.connect(self.handle_nav_to_hourly)
        self.ui_daily_pred.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_daily_pred.params_widget.submit_btn.clicked.connect(self.handle_daily_prediction)

        # Na Hourly Pred Admin
        self.ui_hourly_pred.logout_btn.clicked.connect(self.handle_logout)
        self.ui_hourly_pred.home_btn.clicked.connect(self.handle_nav_to_home)
        self.ui_hourly_pred.daily_btn.clicked.connect(self.handle_nav_to_daily)
        self.ui_hourly_pred.hourly_btn.clicked.connect(self.handle_nav_to_hourly)
        self.ui_hourly_pred.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_hourly_pred.params_widget.submit_btn.clicked.connect(self.handle_hourly_prediction)

        # Na Model Management
        self.ui_model_mgmt.logout_btn.clicked.connect(self.handle_logout)
        self.ui_model_mgmt.home_btn.clicked.connect(self.handle_nav_to_home)
        self.ui_model_mgmt.daily_btn.clicked.connect(self.handle_nav_to_daily)
        self.ui_model_mgmt.hourly_btn.clicked.connect(self.handle_nav_to_hourly)
        self.ui_model_mgmt.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))

        # User Homepage
        self.ui_user_homepage.logout_btn.clicked.connect(self.handle_logout)
        self.ui_user_homepage.home_btn.clicked.connect(self.handle_nav_to_home)
        self.ui_user_homepage.daily_btn.clicked.connect(self.handle_nav_to_daily)
        self.ui_user_homepage.hourly_btn.clicked.connect(self.handle_nav_to_hourly)

        # Botões com Validação
        self.ui_login.login_button.clicked.connect(self.handle_login)
        self.ui_register.signup_button.clicked.connect(self.handle_register)

    def handle_login(self):
        email = self.ui_login.email_input.text().strip()
        password = self.ui_login.pass_input.text().strip()

        is_valid, message = validate_login_input(email, password)
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", message)
            return

        self.ui_login.login_button.setEnabled(False)
        self.ui_login.login_button.setText("Logging in...")

        self.login_worker = LoginWorker(email, password)
        self.login_worker.finished.connect(self._on_login_finished)
        self.login_worker.start()

    def _on_login_finished(self, response_data, status_code):
        self.ui_login.login_button.setEnabled(True)
        self.ui_login.login_button.setText("Login")

        if status_code == 200:
            role = response_data.get("role")

            # Apply role-based visibility
            is_admin = role == "admin"
            self.ui_daily_pred.model_btn.parent().setVisible(is_admin)
            self.ui_hourly_pred.model_btn.parent().setVisible(is_admin)

            # Fetch Profile for username
            self.profile_worker = ProfileWorker()
            self.profile_worker.finished.connect(self._on_profile_finished)
            self.profile_worker.start()

            self.ui_login.email_input.clear()
            self.ui_login.pass_input.clear()

            if is_admin:
                self.stack.setCurrentIndex(2)
            else:
                self.stack.setCurrentIndex(6)
        elif status_code == 401:
            QMessageBox.warning(self, "Login Failed", "Incorrect credentials.")
        elif status_code == 403:
            QMessageBox.warning(self, "Login Failed", "Account locked or access denied.")
        elif status_code == 400:
            error_msg = response_data.get("detail", "Invalid request format.")
            if isinstance(error_msg, list):
                error_msg = error_msg[0].get("msg", str(error_msg))
            QMessageBox.warning(self, "Login Failed", str(error_msg))
        else:
            error_msg = response_data.get("detail", "Error occurred while starting session.")
            QMessageBox.critical(self, "Login Error", str(error_msg))

    def _on_profile_finished(self, data, status):
        if status == 200:
            username = data.get("username", "User")
            welcome_text = f"Welcome back, {username}"
            self.ui_admin.top_bar.title_label.setText(welcome_text)
            self.ui_user_homepage.top_bar.title_label.setText(welcome_text)

    def handle_register(self):
        user = self.ui_register.user_input.text().strip()
        email = self.ui_register.email_input.text().strip()
        password = self.ui_register.pass_input.text().strip()
        confirm = self.ui_register.conf_pass_input.text().strip()

        is_valid, message = validate_registration_input(user, email, password, confirm)

        if not is_valid:
            QMessageBox.warning(self, "Registration Error", message)
            return

        self.ui_register.signup_button.setEnabled(False)
        self.ui_register.signup_button.setText("Registering...")

        self.register_worker = RegisterWorker(user, email, password)
        self.register_worker.finished.connect(self._on_register_finished)
        self.register_worker.start()

    def _on_register_finished(self, response_data, status_code):
        # QA16:feedback visual
        self.ui_register.signup_button.setEnabled(True)
        self.ui_register.signup_button.setText("Sign Up")

        if status_code == 201:
            QMessageBox.information(self, "Success", "Account created successfully!")

            self.ui_register.user_input.clear()
            self.ui_register.email_input.clear()
            self.ui_register.pass_input.clear()
            self.ui_register.conf_pass_input.clear()

            self.stack.setCurrentIndex(0)

        elif status_code == 409:
            self.ui_register.email_input.clear()
            error_message = response_data.get("detail", "Error: Email already registered.")
            QMessageBox.warning(self, "Invalid Registration", str(error_message))
        elif status_code == 400:
            error_message = response_data.get("detail", "Invalid input format.")
            if isinstance(error_message, list):
                error_message = error_message[0].get("msg", str(error_message))
            QMessageBox.warning(self, "Registration Failed", str(error_message))
        else:
            error_message = response_data.get("detail", "An unknown error occurred during registration.")
            if isinstance(error_message, list):
                error_message = error_message[0].get("msg", str(error_message))
            QMessageBox.critical(self, "Registration Error", str(error_message))

    def handle_logout(self):
        self.stack.setCurrentIndex(0)

        # QA5: Enviar notificação ao backend via QThread
        self.logout_worker = LogoutWorker()
        # O deleteLater garante que a thread é destruída da memória após terminar a execução
        self.logout_worker.finished.connect(self._on_logout_finished)
        self.logout_worker.finished.connect(self.logout_worker.deleteLater)
        self.logout_worker.start()

    def _on_logout_finished(self):
        SessionManager.clear_session()
        logger.info("Logout process complete.")

    # --- NAVIGATION HANDLERS ---

    def handle_nav_to_home(self):
        role = SessionManager.get_role()
        if role == "admin":
            self.stack.setCurrentIndex(2)
        else:
            self.stack.setCurrentIndex(6)

    def handle_nav_to_daily(self):
        self.stack.setCurrentIndex(3)
        # Ensure correct visibility in prediction view sidebar
        is_admin = SessionManager.get_role() == "admin"
        self.ui_daily_pred.model_btn.parent().setVisible(is_admin)
        self.handle_daily_prediction()

    def handle_nav_to_hourly(self):
        self.stack.setCurrentIndex(4)
        # Ensure correct visibility in prediction view sidebar
        is_admin = SessionManager.get_role() == "admin"
        self.ui_hourly_pred.model_btn.parent().setVisible(is_admin)
        self.handle_hourly_prediction()

    def handle_daily_prediction(self):
        hist = self.ui_daily_pred.params_widget.before_input.value()
        pred = self.ui_daily_pred.params_widget.after_input.value()

        is_valid, msg = validate_prediction_params("daily", hist, pred)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Parameters", msg)
            return

        self._start_prediction_worker("daily", hist, pred)

    def handle_hourly_prediction(self):
        hist = self.ui_hourly_pred.params_widget.before_input.value()
        pred = self.ui_hourly_pred.params_widget.after_input.value()

        is_valid, msg = validate_prediction_params("hourly", hist, pred)
        if not is_valid:
            QMessageBox.warning(self, "Invalid Parameters", msg)
            return

        self._start_prediction_worker("hourly", hist, pred)

    def _start_prediction_worker(self, frequency, hist, pred):
        self.prediction_worker = PredictionWorker(frequency, hist, pred)
        self.prediction_worker.finished.connect(self._on_prediction_finished)
        self.prediction_worker.finished.connect(self.prediction_worker.deleteLater)
        self.prediction_worker.start()

    def _on_prediction_finished(self, data, status, frequency):
        ui = self.ui_daily_pred if frequency == "daily" else self.ui_hourly_pred

        if status == 200:
            hist_load = data.get("historical_load")
            pred_load = data.get("load_predicted")
            timestamps = data.get("timestamps")
            drivers = data.get("top2_drivers", ["N/A", "N/A"])

            # Update Plot
            ui.plot_widget.update_chart(timestamps, hist_load, pred_load, drivers)

            # Update Driver Cards
            if len(drivers) >= 2:
                ui.rad_card.label.setText(drivers[0])
                ui.temp_card.label.setText(drivers[1])
        else:
            error_msg = data.get("detail", "Failed to fetch predictions.")
            ui.plot_widget.show_error(error_msg)
