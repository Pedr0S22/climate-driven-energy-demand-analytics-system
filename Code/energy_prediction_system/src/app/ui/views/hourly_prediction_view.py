from app.ui.components import DriverCard, PlotWidget, PredictionParams, Sidebar, TopBar
from PyQt6 import QtCore, QtGui, QtWidgets
from app.client.models_service import PredictionService
from PyQt6.QtWidgets import QMessageBox


class Ui_HourlyPredictionAdminWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1446, 1029)
        MainWindow.setStyleSheet("background-color: rgb(243, 243, 243);")
        self.MainWindow = MainWindow

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(16, 18, 16, 18)
        self.main_layout.setSpacing(0)

        # Central Container
        self.container = QtWidgets.QFrame(parent=self.centralwidget)
        self.container.setStyleSheet(
            "background-color: #CCCCCC; border-radius: 5px;")
        self.container_layout = QtWidgets.QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        # 1. TOP BAR
        self.top_bar = TopBar(
            parent=self.container,
            title="Hourly Demand Prediction")
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
        self.daily_btn = self.sidebar.add_menu_item(
            "daily", active=False, indent=True, header_parent="Predictions:")
        self.hourly_btn = self.sidebar.add_menu_item(
            "hourly", active=True, indent=True, header_parent="Predictions:")

        self.sidebar.add_menu_header("Scenario Simulation:")
        self.sim_daily_btn = self.sidebar.add_menu_item(
            "daily", active=False, indent=True, header_parent="Scenario Simulation:")
        self.sim_hourly_btn = self.sidebar.add_menu_item(
            "hourly", active=False, indent=True, header_parent="Scenario Simulation:")

        self.model_btn = self.sidebar.add_menu_item(
            "Model Management", active=False)
        # To hide for normal users, you can call
        # self.model_btn.parent().setVisible(False)

        self.sidebar.layout.addStretch()
        self.sidebar.setVisible(False)
        self.horizontal_container.addWidget(self.sidebar)

        # --- CONTENT AREA ---
        self.scroll_area = QtWidgets.QScrollArea(parent=self.container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(
            "border: none; background: transparent;")
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.content_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(40, 40, 40, 20)
        self.content_layout.setSpacing(50)

        # 2. KEY PREDICTION DRIVERS SECTION
        self.drivers_section = QtWidgets.QVBoxLayout()
        self.drivers_section.setSpacing(20)

        self.drivers_title = QtWidgets.QLabel("Key Prediction Drivers")
        self.drivers_title.setFont(
            QtGui.QFont(
                "Tw Cen MT Condensed",
                42,
                QtGui.QFont.Weight.Bold))
        self.drivers_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drivers_title.setStyleSheet("color: black;")
        self.drivers_section.addWidget(self.drivers_title)

        self.drivers_desc = QtWidgets.QLabel(
            "The following variables had the highest impact on the current forecast results."
        )
        self.drivers_desc.setFont(QtGui.QFont("Tw Cen MT Condensed", 22))
        self.drivers_desc.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.drivers_desc.setStyleSheet("color: #262626;")
        self.drivers_section.addWidget(self.drivers_desc)

        self.drivers_row = QtWidgets.QHBoxLayout()
        self.drivers_row.setSpacing(80)
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
        self.dashboard_grid.setSpacing(50)

        # Titles Row (Row 0)
        self.params_title_ext = QtWidgets.QLabel("Parameters")
        self.params_title_ext.setFont(
            QtGui.QFont(
                "Tw Cen MT Condensed",
                36,
                QtGui.QFont.Weight.Bold))
        self.params_title_ext.setStyleSheet("color: black;")
        self.dashboard_grid.addWidget(self.params_title_ext, 0, 0)

        self.proj_title = QtWidgets.QLabel("Energy Demand Projection")
        self.proj_title.setFont(
            QtGui.QFont(
                "Tw Cen MT Condensed",
                36,
                QtGui.QFont.Weight.Bold))
        self.proj_title.setStyleSheet("color: black;")
        self.dashboard_grid.addWidget(self.proj_title, 0, 1)

        # Widgets Row (Row 1)
        self.params_widget = PredictionParams(mode="hourly")
        self.params_widget.title.setVisible(False)
        self.params_widget.params_changed.connect(
            self.on_params_changed)  # NOVO
        self.dashboard_grid.addWidget(
            self.params_widget, 1, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        self.plot_widget = PlotWidget()
        self.dashboard_grid.addWidget(self.plot_widget, 1, 1)

        self.content_layout.addLayout(self.dashboard_grid)

        self.scroll_area.setWidget(self.scroll_content)
        self.horizontal_container.addWidget(self.scroll_area, stretch=1)
        self.container_layout.addLayout(self.horizontal_container)
        self.main_layout.addWidget(self.container)

        MainWindow.setCentralWidget(self.centralwidget)

        self.menu_btn.clicked.connect(self.toggle_sidebar)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def on_params_changed(self, before, after):
        """Atualiza o gráfico quando os parâmetros mudam."""
        self.prediction_worker = PredictionWorker("hourly", before, after)
        self.prediction_worker.finished.connect(self._on_prediction_loaded)
        self.prediction_worker.finished.connect(
            self.prediction_worker.deleteLater)
        self.prediction_worker.start()

    def _on_prediction_loaded(self, data, status):
        if status == 200:
            timestamps = data.get("timestamps", [])
            historical = data.get("historical_load", [])
            predicted = data.get("load_predicted", [])
            top_drivers = data.get("top2_drivers", [])

            all_loads = historical + predicted
            self.plot_widget.update_chart(
                timestamps, all_loads)  # ← update_chart

            if len(top_drivers) >= 1:
                self.rad_card.set_text(top_drivers[0])
            if len(top_drivers) >= 2:
                self.temp_card.set_text(top_drivers[1])
        else:
            error_msg = data.get("detail", "Unknown error")
            QMessageBox.warning(
                self.MainWindow,
                "Prediction Error",
                str(error_msg))


class PredictionWorker(QtCore.QThread):
    """Worker para obter predições em background."""
    finished = QtCore.pyqtSignal(object, int)

    def __init__(self, mode, historical, predicted):
        super().__init__()
        self.mode = mode
        self.historical = historical
        self.predicted = predicted

    def run(self):
        service = PredictionService()
        if self.mode == "daily":
            data, status = service.get_daily_prediction(
                self.historical, self.predicted)
        else:
            data, status = service.get_hourly_prediction(
                self.historical, self.predicted)
        self.finished.emit(data, status)
