import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # src/app
src_dir = os.path.dirname(current_dir) # src

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from app.ui.views.user_homepage import Ui_UserMainWindow
from app.ui.views.daily_prediction_view import Ui_DailyPredictionAdminWindow
from app.ui.views.hourly_prediction_view import Ui_HourlyPredictionAdminWindow
from app.ui.views.login_view import Ui_LoginWindow
from app.ui.views.register_view import Ui_RegisterWindow

class TestUserMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("User Test - Energy Demand Prediction System")
        self.showMaximized()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pages
        self.login_page = QMainWindow()
        self.register_page = QMainWindow()
        self.home_page = QMainWindow()
        self.daily_page = QMainWindow()
        self.hourly_page = QMainWindow()

        # UIs
        self.ui_login = Ui_LoginWindow()
        self.ui_login.setupUi(self.login_page)

        self.ui_register = Ui_RegisterWindow()
        self.ui_register.setupUi(self.register_page)

        self.ui_home = Ui_UserMainWindow()
        self.ui_home.setupUi(self.home_page)

        self.ui_daily = Ui_DailyPredictionAdminWindow()
        self.ui_daily.setupUi(self.daily_page)

        self.ui_hourly = Ui_HourlyPredictionAdminWindow()
        self.ui_hourly.setupUi(self.hourly_page)

        # Hide Admin-only items for normal user test
        self.ui_daily.model_btn.parent().setVisible(False)
        self.ui_hourly.model_btn.parent().setVisible(False)

        # Add to stack
        self.stack.addWidget(self.login_page)    # 0
        self.stack.addWidget(self.register_page) # 1
        self.stack.addWidget(self.home_page)     # 2
        self.stack.addWidget(self.daily_page)    # 3
        self.stack.addWidget(self.hourly_page)   # 4

        # Iniciar na Home para facilitar o seu teste (Índice 2)
        self.stack.setCurrentIndex(2)

        # --- LIGAÇÕES DE NAVEGAÇÃO ---

        # No Login (0)
        self.ui_login.login_button.clicked.connect(lambda: self.stack.setCurrentIndex(2)) # Para Home
        self.ui_login.register_link.clicked.connect(lambda: self.stack.setCurrentIndex(1)) # Para Registo

        # No Registo (1)
        self.ui_register.login_link.clicked.connect(lambda: self.stack.setCurrentIndex(0)) # Volta para Login
        self.ui_register.signup_button.clicked.connect(lambda: self.stack.setCurrentIndex(0)) # Simula sucesso -> Login

        # Logout em todas as páginas -> Volta para Login (0)
        self.ui_home.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_daily.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.ui_hourly.logout_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        # Home Sidebar (Página 2)
        self.ui_home.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_home.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_home.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        
        # Home Dashboard
        self.ui_home.daily_button.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_home.hourly_button.clicked.connect(lambda: self.stack.setCurrentIndex(4))

        # Daily Page Sidebar (Página 3)
        self.ui_daily.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_daily.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_daily.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))

        # Hourly Page Sidebar (Página 4)
        self.ui_hourly.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.ui_hourly.daily_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.ui_hourly.hourly_btn.clicked.connect(lambda: self.stack.setCurrentIndex(4))

def main():
    app = QApplication(sys.argv)
    window = TestUserMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
