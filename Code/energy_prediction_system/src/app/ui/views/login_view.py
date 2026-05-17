from PyQt6 import QtCore, QtGui, QtWidgets

from src.app.ui.components.logo_label import LogoLabel
from src.app.ui.components.styled_input import StyledInput


class Ui_LoginWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1446, 1029)
        MainWindow.setStyleSheet("background-color: rgb(243, 243, 243);")

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(16, 18, 16, 18)
        self.main_layout.setSpacing(0)

        # Central Container
        self.container = QtWidgets.QFrame(parent=self.centralwidget)
        self.container.setStyleSheet("background-color: #CCCCCC; border-radius: 5px;")
        self.container_layout = QtWidgets.QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        # Top Blue Bar
        self.up_bar = QtWidgets.QWidget(parent=self.container)
        self.up_bar.setFixedHeight(60)
        self.up_bar.setStyleSheet(
            "background-color: rgb(0, 1, 128); border-top-left-radius: 5px; border-top-right-radius: 5px;"
        )
        self.up_bar_layout = QtWidgets.QHBoxLayout(self.up_bar)

        self.Login_label = QtWidgets.QLabel("Login")
        font = QtGui.QFont("Tw Cen MT", 24, QtGui.QFont.Weight.Bold)
        self.Login_label.setFont(font)
        self.Login_label.setStyleSheet("color: rgb(255, 255, 255);")
        self.Login_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.up_bar_layout.addWidget(self.Login_label)

        self.container_layout.addWidget(self.up_bar)

        # Content Area
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 40, 0, 40)
        self.content_layout.setSpacing(20)

        self.content_layout.addStretch()

        # Logo
        self.logo_row = QtWidgets.QHBoxLayout()
        self.logo_label = LogoLabel()
        self.logo_row.addStretch()
        self.logo_row.addWidget(self.logo_label)
        self.logo_row.addStretch()
        self.content_layout.addLayout(self.logo_row)

        self.content_layout.addSpacing(30)

        # Forms Wrapper (to limit width and center)
        self.forms_wrapper = QtWidgets.QHBoxLayout()
        self.forms_wrapper.addStretch()

        self.forms_container = QtWidgets.QVBoxLayout()
        self.forms_container.setSpacing(15)

        label_font = QtGui.QFont("Tw Cen MT Condensed", 20)
        label_style = "color: black;"

        # Email
        self.email_label = QtWidgets.QLabel("Email")
        self.email_label.setFont(label_font)
        self.email_label.setStyleSheet(label_style)
        self.email_input = StyledInput(placeholder="your@email.com")
        self.email_input.setFixedWidth(500)
        self.forms_container.addWidget(self.email_label)
        self.forms_container.addWidget(self.email_input)

        # Password
        self.pass_label = QtWidgets.QLabel("Password")
        self.pass_label.setFont(label_font)
        self.pass_label.setStyleSheet(label_style)
        self.pass_input = StyledInput(placeholder="password", is_password=True)
        self.pass_input.setFixedWidth(500)
        self.forms_container.addWidget(self.pass_label)
        self.forms_container.addWidget(self.pass_input)


        self.forms_wrapper.addLayout(self.forms_container)
        self.forms_wrapper.addStretch()
        self.content_layout.addLayout(self.forms_wrapper)

        self.content_layout.addSpacing(40)

        # Login Button
        self.btn_row = QtWidgets.QHBoxLayout()
        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.setFixedSize(200, 60)
        font_btn = QtGui.QFont("Tw Cen MT", 22, QtGui.QFont.Weight.Bold)
        self.login_button.setFont(font_btn)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(0, 1, 128);
                border: 2px solid black;
                border-radius: 30px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgb(0, 0, 110);
            }
            QPushButton:pressed {
                background-color: rgb(0, 0, 80);
            }
        """)
        self.btn_row.addStretch()
        self.btn_row.addWidget(self.login_button)
        self.btn_row.addStretch()
        self.content_layout.addLayout(self.btn_row)

        # Register Link
        self.register_link = QtWidgets.QPushButton("Don't have an account? Register here.")
        self.register_link.setFont(QtGui.QFont("Tw Cen MT", 14))
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
        self.content_layout.addWidget(self.register_link)

        self.content_layout.addStretch()

        self.container_layout.addWidget(self.content_widget)
        self.main_layout.addWidget(self.container)

        MainWindow.setCentralWidget(self.centralwidget)
