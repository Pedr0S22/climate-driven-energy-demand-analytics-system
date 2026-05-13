from PyQt6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from app.utils.validators import validate_login_input, validate_registration_input

from .views.admin_homepage import Ui_MainWindow as Ui_AdminHome
from .views.daily_prediction_view import Ui_DailyPredictionAdminWindow
from .views.hourly_prediction_view import Ui_HourlyPredictionAdminWindow
from .views.login_view import Ui_LoginWindow
from .views.model_management_view import Ui_ModelManagementWindow
from .views.register_view import Ui_RegisterWindow
from .views.daily_simulator_view import Ui_DailySimulatorWindow
from .views.hourly_simulator_view import Ui_HourlySimulatorWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.daily_simulator_page = QMainWindow()
        self.hourly_simulator_page = QMainWindow()

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

        self.ui_daily_sim = Ui_DailySimulatorWindow()
        self.ui_daily_sim.setupUi(self.daily_simulator_page)

        self.ui_hourly_sim = Ui_HourlySimulatorWindow()
        self.ui_hourly_sim.setupUi(self.hourly_simulator_page)

        # Adicionar à pilha (Stack)
        self.stack.addWidget(self.login_page)             # Índice 0
        self.stack.addWidget(self.register_page)          # Índice 1
        self.stack.addWidget(self.admin_page)             # Índice 2
        self.stack.addWidget(self.daily_pred_admin_page)  # Índice 3
        self.stack.addWidget(self.hourly_pred_admin_page) # Índice 4
        self.stack.addWidget(self.model_mgmt_page)        # Índice 5
        self.stack.addWidget(self.daily_simulator_page)   # Índice 6
        self.stack.addWidget(self.hourly_simulator_page)  # Índice 7

        self.stack.setCurrentIndex(2) # Iniciar na Home por agora para testes

        # --- LIGAÇÕES ---

        # No Login: Ir para Registo
        self.ui_login.register_link.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        # No Registo: Voltar para Login
        self.ui_register.login_link.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Na Home: Botão Logout
        self.ui_admin.pushButton.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Na Home: Navegação Sidebar
        self.ui_admin.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_admin.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_admin.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_admin.model_mgmt_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_admin.sim_daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_admin.sim_hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Na Home: Navegação Dashboard
        self.ui_admin.daily_button.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_admin.hourly_button.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_admin.model_mgmt_button.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        
        self.ui_admin.sim_daily_button.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_admin.sim_hourly_button.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Na Daily Pred Admin
        self.ui_daily_pred.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_daily_pred.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_daily_pred.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_daily_pred.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_daily_pred.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_daily_pred.sim_daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_daily_pred.sim_hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Na Hourly Pred Admin
        self.ui_hourly_pred.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_hourly_pred.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_hourly_pred.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_hourly_pred.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_hourly_pred.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_hourly_pred.sim_daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_hourly_pred.sim_hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Na Model Management
        self.ui_model_mgmt.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_model_mgmt.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_model_mgmt.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_model_mgmt.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_model_mgmt.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_model_mgmt.sim_daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_model_mgmt.sim_hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Na Daily Simulator
        self.ui_daily_sim.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_daily_sim.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_daily_sim.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_daily_sim.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_daily_sim.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_daily_sim.sim_daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_daily_sim.sim_hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Na Hourly Simulator
        self.ui_hourly_sim.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_hourly_sim.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_hourly_sim.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_hourly_sim.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.ui_hourly_sim.model_btn.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.ui_hourly_sim.sim_daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.ui_hourly_sim.sim_hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(7))

        # Botões com Validação
        self.ui_login.login_button.clicked.connect(self.handle_login)
        self.ui_register.signup_button.clicked.connect(self.handle_register)

    def handle_login(self):
        email = self.ui_login.email_input.text()
        password = self.ui_login.pass_input.text()

        is_valid, message = validate_login_input(email, password)

        if is_valid:
            # Extrair nome do email para a mensagem de boas-vindas
            username = email.split('@')[0].capitalize()
            self.ui_admin.top_bar.title_label.setText(f"Welcome back, {username}!")
            
            print(f"Success: {email}")
            self.stack.setCurrentIndex(2) # Vai para Home
        else:
            QMessageBox.warning(self, "Login Error", message)

    def handle_register(self):
        user = self.ui_register.user_input.text()
        email = self.ui_register.email_input.text()
        password = self.ui_register.pass_input.text()
        confirm = self.ui_register.conf_pass_input.text()

        is_valid, message = validate_registration_input(user, email, password, confirm)

        if is_valid:
            QMessageBox.information(self, "Success", "Account created successfully!")
            self.stack.setCurrentIndex(0) # Volta para o Login
        else:
            QMessageBox.warning(self, "Registration Error", message)

    def ir_para_home(self):
        self.stack.setCurrentIndex(2)
