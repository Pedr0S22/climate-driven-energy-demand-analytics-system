from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_LoginWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(500, 400)
        MainWindow.setStyleSheet("background-color: rgb(204, 204, 204);")
        
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(10, 0, 10, 10)
        self.verticalLayout.setObjectName("verticalLayout")

        # barra login
        self.up_bar = QtWidgets.QWidget(parent=self.centralwidget)
        self.up_bar.setMinimumSize(QtCore.QSize(0, 30))
        self.up_bar.setStyleSheet("background-color: rgb(0, 1, 128);")
        self.up_bar.setObjectName("up_bar")
        
        self.Login_label = QtWidgets.QLabel(parent=self.up_bar)
        self.Login_label.setGeometry(QtCore.QRect(110, 0, 51, 31))
        font = QtGui.QFont()
        font.setFamily("Tw Cen MT")
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(75)
        self.Login_label.setFont(font)
        self.Login_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.Login_label.setScaledContents(True)
        self.Login_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.Login_label.setObjectName("Login_label")
        self.Login_label.setText("Login")
        
        self.verticalLayout.addWidget(self.up_bar)

        self.verticalLayout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))

        # --- LOGO ---
        self.logo_layout = QtWidgets.QHBoxLayout()
        self.logo_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.logo_label.setMinimumSize(QtCore.QSize(120, 120))
        self.logo_label.setMaximumSize(QtCore.QSize(120, 120))
        self.logo_label.setPixmap(QtGui.QPixmap("Logo.png"))
        self.logo_label.setScaledContents(True)
        self.logo_layout.addWidget(self.logo_label)
        self.verticalLayout.addLayout(self.logo_layout)

        self.verticalLayout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))

        # --- FORMS ---
        self.forms_container = QtWidgets.QVBoxLayout()
        self.forms_container.setContentsMargins(60, 0, 60, 0) # Margens laterais para não esticar muito
        self.forms_container.setSpacing(10)

        # Estilo comum aos componentes
        input_style = "background-color: rgb(234, 234, 239); border: 1px solid black; border-radius: 4px; color: black; padding: 2px;"
        label_font = QtGui.QFont("Tw Cen MT Condensed", 18)
        label_style = "color: black;"

        # Email
        self.email_label = QtWidgets.QLabel("Email")
        self.email_label.setFont(label_font)
        self.email_label.setStyleSheet(label_style)
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setMinimumHeight(35)
        self.email_input.setStyleSheet(input_style)
        self.forms_container.addWidget(self.email_label)
        self.forms_container.addWidget(self.email_input)

        # Password
        self.pass_label = QtWidgets.QLabel("Password")
        self.pass_label.setFont(label_font)
        self.pass_label.setStyleSheet(label_style)
        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setMinimumHeight(35)
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet(input_style)
        self.forms_container.addWidget(self.pass_label)
        self.forms_container.addWidget(self.pass_input)

        # Esqueci a password
        self.forgot_btn = QtWidgets.QPushButton("I forgot my password")
        self.forgot_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgb(0, 1, 128);
                text-decoration: underline;
                text-align: left;
            }
            QPushButton:hover { color: #3498db; }
        """)
        self.forms_container.addWidget(self.forgot_btn)

        self.verticalLayout.addLayout(self.forms_container)

        self.verticalLayout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        # --- BOTÃO LOGIN ---
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.setFixedSize(140, 50)
        font_btn = QtGui.QFont("Tw Cen MT", 22, QtGui.QFont.Weight.Bold)
        self.login_button.setFont(font_btn)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(0, 1, 128);
                border: 1px solid black;
                border-radius: 20px;
                color: white;
            }
            QPushButton:pressed {
                background-color: rgb(4, 6, 89);
            }
        """)
        self.btn_layout.addWidget(self.login_button)
        self.verticalLayout.addLayout(self.btn_layout)

        # --- LINK PARA REGISTO ---
        self.register_link = QtWidgets.QPushButton("Don't have an account? Register here.")
        self.register_link.setFont(QtGui.QFont("Tw Cen MT", 12))
        self.register_link.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.register_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgb(0, 1, 128);
                text-decoration: underline;
            }
            QPushButton:hover { color: #3498db; }
        """)
        self.verticalLayout.addWidget(self.register_link)

        self.verticalLayout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))

        MainWindow.setCentralWidget(self.centralwidget)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_LoginWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())