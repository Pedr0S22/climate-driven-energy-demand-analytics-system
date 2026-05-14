import os

from app.ui.components import Sidebar, TopBar
from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow:
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

        # 1. TOP BAR
        self.top_bar = TopBar(parent=self.container, title="Welcome back!")
        self.container_layout.addWidget(self.top_bar)

        # Connections
        self.pushButton = self.top_bar.logout_btn
        self.toolButton = self.top_bar.menu_btn

        # --- HORIZONTAL LAYOUT FOR SIDEBAR + CONTENT ---
        self.horizontal_container = QtWidgets.QHBoxLayout()
        self.horizontal_container.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = Sidebar(parent=self.container)
        self.sidebar.setFixedWidth(280)

        self.home_btn = self.sidebar.add_menu_item("Home", active=True)

        self.sidebar.add_menu_header("Predictions:")
        self.daily_btn = self.sidebar.add_menu_item("daily", active=False, indent=True, header_parent="Predictions:")
        self.hourly_btn = self.sidebar.add_menu_item("hourly", active=False, indent=True, header_parent="Predictions:")

        self.sidebar.add_menu_header("Scenario Simulation:")
        self.sim_daily_btn = self.sidebar.add_menu_item(
            "daily", active=False, indent=True, header_parent="Scenario Simulation:"
        )
        self.sim_hourly_btn = self.sidebar.add_menu_item(
            "hourly", active=False, indent=True, header_parent="Scenario Simulation:"
        )

        self.model_mgmt_btn = self.sidebar.add_menu_item("Model Management", active=False)

        self.sidebar.layout.addStretch()
        self.sidebar.setVisible(False)
        self.horizontal_container.addWidget(self.sidebar)

        # --- CONTENT AREA ---
        self.scroll_area = QtWidgets.QScrollArea(parent=self.container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.content_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(60, 40, 60, 40)
        self.content_layout.setSpacing(40)

        # Welcome message
        self.welcome_label = QtWidgets.QLabel("Select a module to start working")
        self.welcome_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 26))
        self.welcome_label.setStyleSheet("color: #262626;")
        self.welcome_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.welcome_label)

        # Common style for dashboard buttons
        dashboard_btn_style = """
            QPushButton {
                background-color: rgb(0, 1, 128);
                color: rgb(255, 255, 255);
                font: 22pt "Tw Cen MT Condensed";
                border: 2px solid black;
                border-radius: 15px;
                padding: 15px;
                text-align: center;
            }
            QPushButton:hover { background-color: rgb(0, 0, 110); }
            QPushButton:pressed { background-color: rgb(0, 0, 80); }
        """

        # 1. PREDICTIONS SECTION
        self.add_section_header("Predictions")
        self.pred_layout = QtWidgets.QHBoxLayout()
        self.pred_layout.setSpacing(30)

        self.daily_button = self.create_big_button("Daily Forecast", "calendar.png", dashboard_btn_style)
        self.hourly_button = self.create_big_button("Hourly Forecast", "clock.png", dashboard_btn_style)

        self.pred_layout.addWidget(self.daily_button)
        self.pred_layout.addWidget(self.hourly_button)
        self.pred_layout.addStretch()
        self.content_layout.addLayout(self.pred_layout)

        # 2. SCENARIO SIMULATION SECTION
        self.add_section_header("Scenario Simulation")
        self.sim_layout = QtWidgets.QHBoxLayout()
        self.sim_layout.setSpacing(30)

        self.sim_daily_button = self.create_big_button("Daily Simulation", "calendar.png", dashboard_btn_style)
        self.sim_hourly_button = self.create_big_button("Hourly Simulation", "clock.png", dashboard_btn_style)

        self.sim_layout.addWidget(self.sim_daily_button)
        self.sim_layout.addWidget(self.sim_hourly_button)
        self.sim_layout.addStretch()
        self.content_layout.addLayout(self.sim_layout)

        # 3. MANAGEMENT SECTION
        self.add_section_header("System Management")
        self.mgmt_layout = QtWidgets.QHBoxLayout()

        self.model_mgmt_button = self.create_big_button("Model Management", None, dashboard_btn_style)
        self.model_mgmt_button.setFixedWidth(400)

        self.mgmt_layout.addWidget(self.model_mgmt_button)
        self.mgmt_layout.addStretch()
        self.content_layout.addLayout(self.mgmt_layout)

        self.content_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_content)
        self.horizontal_container.addWidget(self.scroll_area, stretch=1)
        self.container_layout.addLayout(self.horizontal_container)
        self.main_layout.addWidget(self.container)

        MainWindow.setCentralWidget(self.centralwidget)

        # Connections
        self.toolButton.clicked.connect(self.toggle_sidebar)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def add_section_header(self, text):
        header = QtWidgets.QLabel(text)
        header.setFont(QtGui.QFont("Tw Cen MT Condensed", 24, QtGui.QFont.Weight.Bold))
        header.setStyleSheet("color: #000180; border-bottom: 2px solid #000180; padding-bottom: 5px;")
        self.content_layout.addWidget(header)

    def create_big_button(self, text, icon_name, style):
        btn = QtWidgets.QPushButton(text)
        btn.setFixedSize(300, 120)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(style)

        if icon_name:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QtGui.QIcon(icon_path))
                btn.setIconSize(QtCore.QSize(40, 40))

        return btn
