from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_RegisterWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 450)
        MainWindow.setStyleSheet("background-color: rgb(204, 204, 204);")
        
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(10, 0, 10, 10)
        self.verticalLayout.setObjectName("verticalLayout")

        self.up_bar = QtWidgets.QWidget(parent=self.centralwidget)
        self.up_bar.setMinimumSize(QtCore.QSize(0, 30))
        self.up_bar.setStyleSheet("background-color: rgb(0, 1, 128);")
        self.up_bar.setObjectName("up_bar")
        
        self.Register_label = QtWidgets.QLabel(parent=self.up_bar)
        self.Register_label.setGeometry(QtCore.QRect(110, 0, 81, 31)) 
        font = QtGui.QFont()
        font.setFamily("Tw Cen MT")
        font.setPointSize(18)
        font.setBold(True)
        font.setWeight(QtGui.QFont.Weight.Bold)
        font.setWeight(100)
        self.Register_label.setFont(font)
        self.Register_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.Register_label.setScaledContents(True)
        self.Register_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.Register_label.setObjectName("Register_label")
        self.Register_label.setText("Register")
        
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
        self.forms_grid = QtWidgets.QGridLayout()
        self.forms_grid.setContentsMargins(40, 0, 40, 0)
        self.forms_grid.setHorizontalSpacing(30)
        self.forms_grid.setVerticalSpacing(15)

        input_style = "background-color: rgb(234, 234, 239); border: 1px solid black; border-radius: 4px; color: black; padding: 2px;"
        label_font = QtGui.QFont("Tw Cen MT Condensed", 16)
        label_style = "color: black;"

        # Username
        self.user_layout = QtWidgets.QVBoxLayout()
        self.user_label = QtWidgets.QLabel("Username")
        self.user_label.setStyleSheet(label_style)
        self.user_label.setFont(label_font)
        self.user_input = QtWidgets.QLineEdit()
        self.user_input.setMinimumHeight(30)
        self.user_input.setStyleSheet(input_style)
        self.user_layout.addWidget(self.user_label)
        self.user_layout.addWidget(self.user_input)
        self.forms_grid.addLayout(self.user_layout, 0, 0)

        # Email
        self.email_layout = QtWidgets.QVBoxLayout()
        self.email_label = QtWidgets.QLabel("Email")
        self.email_label.setStyleSheet(label_style)
        self.email_label.setFont(label_font)
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setMinimumHeight(30)
        self.email_input.setStyleSheet(input_style)
        self.email_layout.addWidget(self.email_label)
        self.email_layout.addWidget(self.email_input)
        self.forms_grid.addLayout(self.email_layout, 0, 1)

        # Password
        self.pass_layout = QtWidgets.QVBoxLayout()
        self.pass_label = QtWidgets.QLabel("Password")
        self.pass_label.setStyleSheet(label_style)
        self.pass_label.setFont(label_font)
        self.pass_input = QtWidgets.QLineEdit()
        self.pass_input.setMinimumHeight(30)
        self.pass_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.pass_input.setStyleSheet(input_style)
        self.pass_layout.addWidget(self.pass_label)
        self.pass_layout.addWidget(self.pass_input)
        self.forms_grid.addLayout(self.pass_layout, 1, 0)

        # Confirm Password
        self.conf_pass_layout = QtWidgets.QVBoxLayout()
        self.conf_pass_label = QtWidgets.QLabel("Confirm Password")
        self.conf_pass_label.setStyleSheet(label_style)
        self.conf_pass_label.setFont(label_font)
        self.conf_pass_input = QtWidgets.QLineEdit()
        self.conf_pass_input.setMinimumHeight(30)
        self.conf_pass_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.conf_pass_input.setStyleSheet(input_style)
        self.conf_pass_layout.addWidget(self.conf_pass_label)
        self.conf_pass_layout.addWidget(self.conf_pass_input)
        self.forms_grid.addLayout(self.conf_pass_layout, 1, 1)

        self.verticalLayout.addLayout(self.forms_grid)

        # Requisitos
        self.requirements_label = QtWidgets.QLabel("8–20 characters, with at least one uppercase letter, one number, and one special character.")
        self.requirements_label.setFont(QtGui.QFont("Tw Cen MT", 10))
        self.requirements_label.setStyleSheet("color: rgb(0, 1, 128);")
        self.requirements_label.setContentsMargins(40, 0, 0, 0)
        self.verticalLayout.addWidget(self.requirements_label)

        self.verticalLayout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Fixed))

        # Botão Sign up
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.signup_button = QtWidgets.QPushButton("Sign up")
        self.signup_button.setFixedSize(140, 50)
        font_btn = QtGui.QFont("Tw Cen MT", 22, QtGui.QFont.Weight.Bold)
        self.signup_button.setFont(font_btn)
        self.signup_button.setStyleSheet("""
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
        self.btn_layout.addWidget(self.signup_button)
        self.verticalLayout.addLayout(self.btn_layout)

        # Link para Login
        self.login_link = QtWidgets.QPushButton("Already have an account? Log in here.")
        self.login_link.setFont(QtGui.QFont("Tw Cen MT", 11))
        self.login_link.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.login_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgb(0, 1, 128);
                text-decoration: underline;
            }
            QPushButton:hover { color: #3498db; }
        """)
        self.verticalLayout.addWidget(self.login_link)
        self.verticalLayout.addItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))

        MainWindow.setCentralWidget(self.centralwidget)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_RegisterWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())