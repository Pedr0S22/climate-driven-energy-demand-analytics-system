from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget
from .views.login_view import Ui_LoginWindow
from .views.register_view import Ui_RegisterWindow
from .views.admin_homepage import Ui_MainWindow as Ui_AdminHome

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
        self.stack.addWidget(self.login_page)    # Índice 0
        self.stack.addWidget(self.register_page) # Índice 1
        self.stack.addWidget(self.admin_page)    # Índice 2

        # --- LIGAÇÕES ---
        
        # No Login: Ir para Registo
        self.ui_login.register_link.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        
        # No Registo: Voltar para Login
        self.ui_register.login_link.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # No Login: Botão de Login (falta logica de validação, por isso só muda para a Home)
        self.ui_login.login_button.clicked.connect(self.ir_para_home)

        # Na Home: Botão Logout
        self.ui_admin.pushButton.clicked.connect(lambda: self.stack.setCurrentIndex(0))

    def ir_para_home(self):
        #aqui chamar validators
        self.stack.setCurrentIndex(2)
        