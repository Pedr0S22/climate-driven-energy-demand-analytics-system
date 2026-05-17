from PyQt6 import QtCore, QtGui, QtWidgets

from src.app.ui.components.date_picker import DatePicker
from src.app.ui.components.sidebar import Sidebar
from src.app.ui.components.styled_input import StyledInput
from src.app.ui.components.time_picker import TimePicker
from src.app.ui.components.top_bar import TopBar


class Ui_HourlySimulatorWindow:
    def setupUi(self, HourlySimulatorWindow):
        HourlySimulatorWindow.setObjectName("HourlySimulatorWindow")
        HourlySimulatorWindow.resize(1446, 1029)
        HourlySimulatorWindow.setStyleSheet("background-color: rgb(243, 243, 243);")

        self.centralwidget = QtWidgets.QWidget(parent=HourlySimulatorWindow)
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
        self.top_bar = TopBar(parent=self.container, title="Hourly Scenario Simulator")
        self.container_layout.addWidget(self.top_bar)

        # Connections
        self.logout_btn = self.top_bar.logout_btn
        self.menu_btn = self.top_bar.menu_btn

        # --- HORIZONTAL LAYOUT FOR SIDEBAR + CONTENT ---
        self.horizontal_container = QtWidgets.QHBoxLayout()
        self.horizontal_container.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = Sidebar(parent=self.container)
        self.sidebar.setFixedWidth(280)

        self.home_btn = self.sidebar.add_menu_header("Home", is_toggle=False, active=False)

        self.sidebar.add_menu_header("Predictions:")
        self.daily_btn = self.sidebar.add_menu_item("daily", active=False, indent=True, header_parent="Predictions:")
        self.hourly_btn = self.sidebar.add_menu_item("hourly", active=False, indent=True, header_parent="Predictions:")

        self.sidebar.add_menu_header("Scenario Simulation:")
        self.sim_daily_btn = self.sidebar.add_menu_item(
            "daily", active=False, indent=True, header_parent="Scenario Simulation:"
        )
        self.sim_hourly_btn = self.sidebar.add_menu_item(
            "hourly", active=True, indent=True, header_parent="Scenario Simulation:"
        )

        self.model_btn = self.sidebar.add_menu_header("Model Management", is_toggle=False, active=False)

        self.sidebar.layout.addStretch()
        self.sidebar.setVisible(False)
        self.horizontal_container.addWidget(self.sidebar)

        # --- CONTENT AREA ---
        self.scroll_area = QtWidgets.QScrollArea(parent=self.container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")

        # Main Layout for Scroll Area
        self.content_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.content_layout.setContentsMargins(40, 20, 40, 20)

        # --- 1. TOP STRETCH FOR VERTICAL CENTERING ---
        self.content_layout.addStretch()

        # --- 2. HORIZONTAL LAYOUT FOR HORIZONTAL CENTERING ---
        self.center_h_layout = QtWidgets.QHBoxLayout()
        self.center_h_layout.addStretch()  # LEFT STRETCH

        # --- 3. INNER CONTENT LAYOUT ---
        self.inner_content_layout = QtWidgets.QVBoxLayout()
        self.inner_content_layout.setSpacing(60)  # Large gap between Selectors and Simulator sections

        # ---------------------------------------------------------
        # ROW 1: SELECTORS SECTION (Template, Date, Hour)
        # ---------------------------------------------------------
        self.selectors_layout = QtWidgets.QHBoxLayout()
        self.selectors_layout.setSpacing(40)  # Space between the 3 boxes

        # Add a left stretch to perfectly center the 3 items over the columns below
        self.selectors_layout.addStretch()

        # Template Selector
        self.template_vbox = QtWidgets.QVBoxLayout()
        self.template_vbox.setSpacing(10)
        self.template_label = QtWidgets.QLabel("Template")
        self.template_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.template_label.setStyleSheet("color: black;")
        self.template_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.template_vbox.addWidget(self.template_label)

        self.template_combo = self.create_custom_combo(["Average", "Heatwave", "Storm", "Rainy"])
        self.template_vbox.addWidget(self.template_combo)
        self.selectors_layout.addLayout(self.template_vbox)

        # Date Selector
        self.date_vbox = QtWidgets.QVBoxLayout()
        self.date_vbox.setSpacing(10)
        self.date_label = QtWidgets.QLabel("Date")
        self.date_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.date_label.setStyleSheet("color: black;")
        self.date_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.date_vbox.addWidget(self.date_label)

        self.date_picker = DatePicker(parent=self.scroll_content, show_icon=False)
        self.date_picker.setFixedSize(260, 58)  # Made shorter horizontally
        self.date_vbox.addWidget(self.date_picker)
        self.selectors_layout.addLayout(self.date_vbox)

        # Hour Selector
        self.hour_vbox = QtWidgets.QVBoxLayout()
        self.hour_vbox.setSpacing(10)
        self.hour_label = QtWidgets.QLabel("Hour")
        self.hour_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.hour_label.setStyleSheet("color: black;")
        self.hour_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.hour_vbox.addWidget(self.hour_label)

        self.time_picker = TimePicker(parent=self.scroll_content, initial_hour=12)
        self.time_picker.setFixedSize(260, 58)  # Made shorter horizontally
        self.hour_vbox.addWidget(self.time_picker)
        self.selectors_layout.addLayout(self.hour_vbox)

        # Add a right stretch to finish centering the 3 items
        self.selectors_layout.addStretch()

        # Add the selectors to the inner vertical layout
        self.inner_content_layout.addLayout(self.selectors_layout)

        # ---------------------------------------------------------
        # ROW 2: MAIN SIMULATOR SECTION (2 Columns)
        # ---------------------------------------------------------
        self.main_grid = QtWidgets.QGridLayout()
        self.main_grid.setColumnStretch(1, 1)
        self.main_grid.setHorizontalSpacing(120)  # Distance between columns

        # Parameters Column (Column 0)
        self.params_vbox = QtWidgets.QVBoxLayout()
        self.params_vbox.setSpacing(10)

        self.params_header = QtWidgets.QLabel("Overwrite parameters")
        self.params_header.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.params_header.setStyleSheet("color: black;")
        self.params_header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.params_vbox.addWidget(self.params_header)

        # Real Defaults from BASE_TEMPLATES (Hourly)
        self.template_defaults = {
            "Average": {"t2m": "14.78", "sp": "941.93", "tp": "0.00", "u10": "-0.50", "v10": "-0.80"},
            "Heatwave": {"t2m": "41.00", "sp": "939.61", "tp": "0.00", "u10": "3.74", "v10": "2.82"},
            "Storm": {"t2m": "20.49", "sp": "933.40", "tp": "9.64", "u10": "-1.25", "v10": "-0.78"},
            "Rainy": {"t2m": "5.56", "sp": "936.74", "tp": "0.07", "u10": "2.73", "v10": "2.22"},
        }

        # Real Limits from PHYSICAL_LIMITS
        self.param_ranges = {
            "2m Air Temperature (ºC)": (-40.0, 55.0),
            "Surface Pressure (hPa)": (800.0, 1100.0),
            "Total Precipitation (mm)": (0.0, 55.0),
            "10 m Wind Zonal Velocity (m/s)": (-69.4, 69.4),
            "10 m Meridional Velocity (m/s)": (-69.4, 69.4),
        }

        # Parameter Inputs
        self.param_inputs = {}
        parameters = [
            ("2m Air Temperature (ºC)", "14.78"),
            ("Surface Pressure (hPa)", "941.93"),
            ("Total Precipitation (mm)", "0.00"),
            ("10 m Wind Zonal Velocity (m/s)", "-0.50"),
            ("10 m Meridional Velocity (m/s)", "-0.80"),
        ]

        for label_text, default_val in parameters:
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.setSpacing(10)  # Tight distance between label and input

            lbl = QtWidgets.QLabel(label_text)
            lbl.setFont(QtGui.QFont("Tw Cen MT Condensed", 28))
            lbl.setStyleSheet("color: black;")
            lbl.setFixedWidth(350)  # Prevents invisible spacing issues

            inp = StyledInput(placeholder=default_val)
            inp.setText(default_val)
            inp.setFixedWidth(191)
            inp.setFixedHeight(58)
            inp.setStyleSheet(
                inp.styleSheet() + "QLineEdit { font-size: 32px; border: 2px solid black; border-radius: 6px; }"
            )

            # Add validator based on real ranges
            min_val, max_val = self.param_ranges[label_text]
            validator = QtGui.QDoubleValidator(min_val, max_val, 2)
            validator.setNotation(QtGui.QDoubleValidator.Notation.StandardNotation)
            validator.setLocale(QtCore.QLocale.c())
            inp.setValidator(validator)

            row_layout.addWidget(lbl)
            row_layout.addWidget(inp)
            row_layout.addStretch()  # Push inputs to the left to keep them tidy

            self.params_vbox.addLayout(row_layout)
            self.param_inputs[label_text] = inp

        self.main_grid.addLayout(self.params_vbox, 0, 0, QtCore.Qt.AlignmentFlag.AlignTop)

        # Projection Column (Column 1)
        self.projection_vbox = QtWidgets.QVBoxLayout()
        self.projection_vbox.setSpacing(20)

        self.proj_title = QtWidgets.QLabel("Projected Demand (MWh)")
        self.proj_title.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.proj_title.setStyleSheet("color: black;")
        self.proj_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.projection_vbox.addWidget(self.proj_title)

        self.proj_display = QtWidgets.QFrame()
        self.proj_display.setFixedSize(350, 150)
        self.proj_display.setStyleSheet("""
            QFrame {
                background-color: #CAF6FF;
                border: 4px solid black;
                border-radius: 12px; /* Smooth rounded corners */
            }
        """)
        self.proj_display_layout = QtWidgets.QVBoxLayout(self.proj_display)
        self.proj_value = QtWidgets.QLabel("---,--")
        self.proj_value.setFont(QtGui.QFont("Tw Cen MT Condensed", 50, QtGui.QFont.Weight.Bold))
        self.proj_value.setStyleSheet("color: black; border: none;")
        self.proj_value.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.proj_display_layout.addWidget(self.proj_value)

        self.projection_vbox.addWidget(self.proj_display, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Buttons
        self.buttons_vbox = QtWidgets.QVBoxLayout()
        self.buttons_vbox.setSpacing(15)
        self.buttons_vbox.setContentsMargins(0, 10, 0, 0)

        self.save_btn = QtWidgets.QPushButton("Run Simulation")
        self.save_btn.setFixedSize(280, 65)
        self.save_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #000180;
                color: white;
                border: 3px solid black;
                border-radius: 12px;
                font-family: 'Tw Cen MT';
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0000AA; }
        """)
        self.buttons_vbox.addWidget(self.save_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.setFixedSize(140, 65)
        self.reset_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #800002;
                color: white;
                border: 3px solid black;
                border-radius: 12px;
                font-family: 'Tw Cen MT';
                font-size: 28px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A00002; }
        """)
        self.buttons_vbox.addWidget(self.reset_btn, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        self.buttons_vbox.addStretch()

        self.projection_vbox.addLayout(self.buttons_vbox)
        self.main_grid.addLayout(self.projection_vbox, 0, 1, QtCore.Qt.AlignmentFlag.AlignTop)

        self.inner_content_layout.addLayout(self.main_grid)

        # --- 4. FINISH THE SPACER SANDWICH ---
        self.center_h_layout.addLayout(self.inner_content_layout)
        self.center_h_layout.addStretch()  # RIGHT STRETCH

        self.content_layout.addLayout(self.center_h_layout)

        # --- 5. BOTTOM STRETCH FOR VERTICAL CENTERING ---
        self.content_layout.addStretch()

        # Final setup
        self.scroll_area.setWidget(self.scroll_content)
        self.horizontal_container.addWidget(self.scroll_area, stretch=1)
        self.container_layout.addLayout(self.horizontal_container)
        self.main_layout.addWidget(self.container)

        HourlySimulatorWindow.setCentralWidget(self.centralwidget)

        # Connections
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        self.template_combo.currentTextChanged.connect(self.update_params_from_template)
        self.reset_btn.clicked.connect(self.reset_defaults)
        self.save_btn.clicked.connect(self.run_simulation)  # Connected!

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def update_params_from_template(self, template_name):
        if template_name in self.template_defaults:
            defs = self.template_defaults[template_name]

            self.param_inputs["2m Air Temperature (ºC)"].setText(defs["t2m"])
            self.param_inputs["2m Air Temperature (ºC)"].setPlaceholderText(defs["t2m"])

            self.param_inputs["Surface Pressure (hPa)"].setText(defs["sp"])
            self.param_inputs["Surface Pressure (hPa)"].setPlaceholderText(defs["sp"])

            self.param_inputs["Total Precipitation (mm)"].setText(defs["tp"])
            self.param_inputs["Total Precipitation (mm)"].setPlaceholderText(defs["tp"])

            self.param_inputs["10 m Wind Zonal Velocity (m/s)"].setText(defs["u10"])
            self.param_inputs["10 m Wind Zonal Velocity (m/s)"].setPlaceholderText(defs["u10"])

            self.param_inputs["10 m Meridional Velocity (m/s)"].setText(defs["v10"])
            self.param_inputs["10 m Meridional Velocity (m/s)"].setPlaceholderText(defs["v10"])

    def reset_defaults(self):
        """Resets inputs to current template defaults."""
        self.update_params_from_template(self.template_combo.currentText())
        tomorrow = QtCore.QDate.currentDate().addDays(1)
        self.date_picker.setDate(tomorrow)
        self.time_picker.setTime(QtCore.QTime(12, 0))

    def run_simulation(self):
        """Gathers all inputs and runs the simulation."""

        selected_template = self.template_combo.currentText()

        try:
            selected_date = self.date_picker.date().toString("dd/MM/yyyy")
        except AttributeError:
            selected_date = "Unknown Date"

        try:
            selected_hour = self.time_picker.time().toString("HH:mm")
        except AttributeError:
            selected_hour = "Unknown Hour"

        # Get variables, falling back to placeholders if empty
        temp_input = self.param_inputs["2m Air Temperature (ºC)"]
        temp_val = temp_input.text() if temp_input.text() else temp_input.placeholderText()

        sp_input = self.param_inputs["Surface Pressure (hPa)"]
        sp_val = sp_input.text() if sp_input.text() else sp_input.placeholderText()

        tp_input = self.param_inputs["Total Precipitation (mm)"]
        tp_val = tp_input.text() if tp_input.text() else tp_input.placeholderText()

        u10_input = self.param_inputs["10 m Wind Zonal Velocity (m/s)"]
        u10_val = u10_input.text() if u10_input.text() else u10_input.placeholderText()

        v10_input = self.param_inputs["10 m Meridional Velocity (m/s)"]
        v10_val = v10_input.text() if v10_input.text() else v10_input.placeholderText()

        print("--- HOURLY SIMULATION TRIGGERED ---")
        print(f"Date: {selected_date} | Hour: {selected_hour} | Template: {selected_template}")
        print(f"Temp: {temp_val}, Pressure: {sp_val}, Precip: {tp_val}")
        print(f"Wind Zonal: {u10_val}, Wind Meridional: {v10_val}")

        # Update Display
        mock_prediction = "---,--"
        self.proj_value.setText(mock_prediction)

    def create_custom_combo(self, items):
        combo = QtWidgets.QComboBox()
        combo.addItems(items)
        combo.setFixedSize(260, 58)  # Changed width to perfectly match Date & Hour boxes
        combo.setStyleSheet("""
            QComboBox {
                background-color: #EAEAEF;
                border: 4px solid black;
                border-radius: 8px;
                color: black;
                font-family: 'Tw Cen MT Condensed';
                font-size: 28px;
                padding-left: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 50px;
                background-color: #CCCCCC;
                border-left: 1px solid #626060;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 10px solid transparent;
                border-right: 10px solid transparent;
                border-top: 12px solid black;
                margin-top: 2px;
            }
            QComboBox QAbstractItemView {
                background-color: #828282;
                border: 1px solid black;
                selection-background-color: #000180;
                selection-color: white;
            }
        """)
        return combo
