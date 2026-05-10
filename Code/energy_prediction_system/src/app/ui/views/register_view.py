import os
from PyQt6 import QtCore, QtGui, QtWidgets

from app.ui.components.logo_label import LogoLabel
from app.ui.components.styled_input import StyledInput

class Ui_RegisterWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(500, 500)
        MainWindow.setStyleSheet("background-color: rgb(204, 204, 204);")

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(10, 0, 10, 10)
        self.verticalLayout.setObjectName("verticalLayout")

        # Top Bar
        self.up_bar = QtWidgets.QWidget(parent=self.centralwidget)
        self.up_bar.setMinimumSize(QtCore.QSize(0, 30))
        self.up_bar.setStyleSheet("background-color: rgb(0, 1, 128);")
        self.up_bar.setObjectName("up_bar")

        self.Register_label = QtWidgets.QLabel(parent=self.up_bar)
        self.Register_label.setGeometry(QtCore.QRect(110, 0, 100, 31))
        font = QtGui.QFont("Tw Cen MT", 18, QtGui.QFont.Weight.Bold)
        self.Register_label.setFont(font)
        self.Register_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.Register_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.Register_label.setText("Register")

        self.verticalLayout.addWidget(self.up_bar)

        self.verticalLayout.addStretch()

        # Logo
        self.logo_layout = QtWidgets.QHBoxLayout()
        self.logo_label = LogoLabel()
        self.logo_layout.addWidget(self.logo_label)
        self.verticalLayout.addLayout(self.logo_layout)

        self.verticalLayout.addStretch()

        # Forms
        self.forms_container = QtWidgets.QVBoxLayout()
        self.forms_container.setContentsMargins(60, 0, 60, 0)
        self.forms_container.setSpacing(10)

        label_font = QtGui.QFont("Tw Cen MT Condensed", 18)
        label_style = "color: black;"

        # Username
        self.user_label = QtWidgets.QLabel("Username")
        self.user_label.setFont(label_font)
        self.user_label.setStyleSheet(label_style)
        self.user_input = StyledInput(placeholder="username")
        self.forms_container.addWidget(self.user_label)
        self.forms_container.addWidget(self.user_input)

        # Email
        self.email_label = QtWidgets.QLabel("Email")
        self.email_label.setFont(label_font)
        self.email_label.setStyleSheet(label_style)
        self.email_input = StyledInput(placeholder="your@email.com")
        self.forms_container.addWidget(self.email_label)
        self.forms_container.addWidget(self.email_input)

        # Password
        self.pass_label = QtWidgets.QLabel("Password")
        self.pass_label.setFont(label_font)
        self.pass_label.setStyleSheet(label_style)
        self.pass_input = StyledInput(placeholder="password", is_password=True)
        self.forms_container.addWidget(self.pass_label)
        self.forms_container.addWidget(self.pass_input)

        # Confirm Password
        self.conf_pass_label = QtWidgets.QLabel("Confirm Password")
        self.conf_pass_label.setFont(label_font)
        self.conf_pass_label.setStyleSheet(label_style)
        self.conf_pass_input = StyledInput(placeholder="confirm password", is_password=True)
        self.forms_container.addWidget(self.conf_pass_label)
        self.forms_container.addWidget(self.conf_pass_input)

        self.verticalLayout.addLayout(self.forms_container)
        self.verticalLayout.addSpacing(20)

        # Signup Button
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.signup_button = QtWidgets.QPushButton("Sign Up")
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

        # Login Link
        self.login_link = QtWidgets.QPushButton("Already have an account? Login here.")
        self.login_link.setFont(QtGui.QFont("Tw Cen MT", 12))
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

        self.verticalLayout.addStretch()

        MainWindow.setCentralWidget(self.centralwidget)
