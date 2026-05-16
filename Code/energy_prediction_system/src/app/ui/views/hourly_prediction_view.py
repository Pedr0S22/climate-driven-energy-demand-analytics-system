from app.ui.components import DriverCard, PlotWidget, PredictionParams, Sidebar, TopBar
from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_HourlyPredictionAdminWindow:
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
        self.top_bar = TopBar(parent=self.container, title="Hourly Demand Prediction")
        self.container_layout.addWidget(self.top_bar)

        self.logout_btn = self.top_bar.logout_btn
        self.menu_btn = self.top_bar.menu_btn

        # --- HORIZONTAL LAYOUT FOR SIDEBAR + CONTENT ---
        self.horizontal_container = QtWidgets.QHBoxLayout()
        self.horizontal_container.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = Sidebar(parent=self.container)
        self.sidebar.setFixedWidth(280)

        self.home_btn = self.sidebar.add_menu_item("Home", active=False)

        self.sidebar.add_menu_header("Predictions:")
        self.daily_btn = self.sidebar.add_menu_item("daily", active=False, indent=True, header_parent="Predictions:")
        self.hourly_btn = self.sidebar.add_menu_item("hourly", active=True, indent=True, header_parent="Predictions:")

        self.sidebar.add_menu_header("Scenario Simulation:")
        self.sim_daily_btn = self.sidebar.add_menu_item(
            "daily", active=False, indent=True, header_parent="Scenario Simulation:"
        )
        self.sim_hourly_btn = self.sidebar.add_menu_item(
            "hourly", active=False, indent=True, header_parent="Scenario Simulation:"
        )

        self.model_btn = self.sidebar.add_menu_item("Model Management", active=False)
        # To hide for normal users, you can call self.model_btn.parent().setVisible(False)

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
        self.content_layout.setContentsMargins(40, 20, 40, 20)
        self.content_layout.setSpacing(0)

        # 2. KEY PREDICTION DRIVERS SECTION
        self.drivers_section = QtWidgets.QVBoxLayout()
        self.drivers_section.setSpacing(10)

        self.drivers_title = QtWidgets.QLabel("Key Prediction Drivers")
        self.drivers_title.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.drivers_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drivers_title.setStyleSheet("color: black;")
        self.drivers_section.addWidget(self.drivers_title)

        self.drivers_desc = QtWidgets.QLabel(
            "The following variables had the highest impact on the current forecast results."
        )
        self.drivers_desc.setFont(QtGui.QFont("Tw Cen MT Condensed", 16))
        self.drivers_desc.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drivers_desc.setStyleSheet("color: #262626;")
        self.drivers_section.addWidget(self.drivers_desc)

        self.drivers_row = QtWidgets.QHBoxLayout()
        self.drivers_row.setSpacing(40)
        self.drivers_row.addStretch()
        self.rad_card = DriverCard(text="Solar radiation")
        self.drivers_row.addWidget(self.rad_card)
        self.temp_card = DriverCard(text="Temperature")
        self.drivers_row.addWidget(self.temp_card)
        self.drivers_row.addStretch()
        self.drivers_section.addLayout(self.drivers_row)
        self.content_layout.addLayout(self.drivers_section)

        # 3. LOWER DASHBOARD SECTION
        self.dashboard_grid = QtWidgets.QGridLayout()
        self.dashboard_grid.setColumnStretch(1, 1)
        self.dashboard_grid.setSpacing(10)

        # Titles Row (Row 0)
        self.params_title_ext = QtWidgets.QLabel("Parameters")
        self.params_title_ext.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.params_title_ext.setStyleSheet("color: black;")
        self.dashboard_grid.addWidget(self.params_title_ext, 0, 0)

        # Widgets Row (Row 1)
        self.params_widget = PredictionParams(mode="hourly")
        self.params_widget.title.setVisible(False)
        self.dashboard_grid.addWidget(self.params_widget, 1, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        self.plot_widget = PlotWidget()
        self.dashboard_grid.addWidget(self.plot_widget, 1, 1)

        self.content_layout.addLayout(self.dashboard_grid)
        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        self.horizontal_container.addWidget(self.scroll_area, stretch=1)
        self.container_layout.addLayout(self.horizontal_container)
        self.main_layout.addWidget(self.container)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menu_btn.clicked.connect(self.toggle_sidebar)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())
