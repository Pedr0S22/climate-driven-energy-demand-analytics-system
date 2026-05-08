from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from app.utils.validators import validate_login_input, validate_registration_input


from .views.admin_homepage import Ui_MainWindow as Ui_AdminHome
from .views.login_view import Ui_LoginWindow
from .views.register_view import Ui_RegisterWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # O StackedWidget permite trocar de página sem abrir janelas novas
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Criar os widgets para cada página
        self.login_page = QMainWindow()
        self.register_page = QMainWindow()
        self.admin_page = QMainWindow()

        # Configurar as UIs nos seus respetivos widgets
        self.ui_login = Ui_LoginWindow()
        self.ui_login.setupUi(self.login_page)

        self.ui_register = Ui_RegisterWindow()
        self.ui_register.setupUi(self.register_page)

        self.ui_admin = Ui_AdminHome()
        self.ui_admin.setupUi(self.admin_page)

        # Adicionar à pilha (Stack)
        self.stack.addWidget(self.login_page)  # Índice 0
        self.stack.addWidget(self.register_page)  # Índice 1
        self.stack.addWidget(self.admin_page)  # Índice 2

        # --- LIGAÇÕES ---

        # No Login: Ir para Registo
        self.ui_login.register_link.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        # No Registo: Voltar para Login
        self.ui_register.login_link.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Na Home: Botão Logout
        self.ui_admin.pushButton.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Botões com Validação
        self.ui_login.login_button.clicked.connect(self.handle_login)
        self.ui_register.signup_button.clicked.connect(self.handle_register)

    def handle_login(self):
        email = self.ui_login.email_input.text()
        password = self.ui_login.pass_input.text()

        is_valid, message = validate_login_input(email, password)

        if is_valid:
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
