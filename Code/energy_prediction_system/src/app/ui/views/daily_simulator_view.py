from app.ui.components import DatePicker, Sidebar, StyledInput, TopBar
from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_DailySimulatorWindow:
    def setupUi(self, DailySimulatorWindow):
        DailySimulatorWindow.setObjectName("DailySimulatorWindow")
        DailySimulatorWindow.resize(1446, 1029)
        DailySimulatorWindow.setStyleSheet("background-color: rgb(243, 243, 243);")

        self.centralwidget = QtWidgets.QWidget(parent=DailySimulatorWindow)
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
        self.top_bar = TopBar(parent=self.container, title="Daily Scenario Simulator")
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
            "daily", active=True, indent=True, header_parent="Scenario Simulation:"
        )
        self.sim_hourly_btn = self.sidebar.add_menu_item(
            "hourly", active=False, indent=True, header_parent="Scenario Simulation:"
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

        # --- 3. UNIFIED MASTER GRID ---
        self.main_grid = QtWidgets.QGridLayout()
        self.main_grid.setHorizontalSpacing(120)  # Gap between the Left and Right columns
        self.main_grid.setVerticalSpacing(40)  # Gap between the Selectors (Row 0) and Inputs (Row 1)

        # ---------------------------------------------------------
        # ROW 0, COLUMN 0: Template Selector
        # ---------------------------------------------------------
        self.template_vbox = QtWidgets.QVBoxLayout()
        self.template_vbox.setSpacing(10)
        self.template_label = QtWidgets.QLabel("Template")
        self.template_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.template_label.setStyleSheet("color: black;")
        self.template_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.template_vbox.addWidget(self.template_label)

        self.template_combo = self.create_custom_combo(["Average", "Heatwave", "Storm", "Rainy"])
        self.template_vbox.addWidget(self.template_combo)

        self.main_grid.addLayout(
            self.template_vbox, 0, 0, QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom
        )

        # ---------------------------------------------------------
        # ROW 0, COLUMN 1: Date Selector
        # ---------------------------------------------------------
        self.date_vbox = QtWidgets.QVBoxLayout()
        self.date_vbox.setSpacing(10)
        self.date_label = QtWidgets.QLabel("Date")
        self.date_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.date_label.setStyleSheet("color: black;")
        self.date_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.date_vbox.addWidget(self.date_label)

        self.date_picker = DatePicker(parent=self.scroll_content, show_icon=False)
        self.date_vbox.addWidget(self.date_picker)

        self.main_grid.addLayout(
            self.date_vbox, 0, 1, QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignBottom
        )

        # ---------------------------------------------------------
        # ROW 1, COLUMN 0: Parameters Column
        # ---------------------------------------------------------
        self.params_vbox = QtWidgets.QVBoxLayout()
        self.params_vbox.setSpacing(15)

        self.params_header = QtWidgets.QLabel("Overwrite parameters")
        self.params_header.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.params_header.setStyleSheet("color: black;")
        self.params_header.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.params_vbox.addWidget(self.params_header)

        # Real Defaults from BASE_TEMPLATES (Daily)
        self.template_defaults = {
            "Average": {"t2m": "13.78", "sp": "938.67", "tp": "0.00", "u10": "0.46", "v10": "0.37"},
            "Heatwave": {"t2m": "33.29", "sp": "939.47", "tp": "0.00", "u10": "-1.77", "v10": "-1.51"},
            "Storm": {"t2m": "19.56", "sp": "934.71", "tp": "1.99", "u10": "-1.89", "v10": "-0.81"},
            "Rainy": {"t2m": "4.34", "sp": "931.85", "tp": "0.16", "u10": "1.66", "v10": "1.68"},
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
            ("2m Air Temperature (ºC)", "13.78"),
            ("Surface Pressure (hPa)", "938.67"),
            ("Total Precipitation (mm)", "0.00"),
            ("10 m Wind Zonal Velocity (m/s)", "0.46"),
            ("10 m Meridional Velocity (m/s)", "0.37"),
        ]

        for label_text, default_val in parameters:
            row_layout = QtWidgets.QHBoxLayout()
            row_layout.setSpacing(60)  # Distance between label and input

            lbl = QtWidgets.QLabel(label_text)
            lbl.setFont(QtGui.QFont("Tw Cen MT Condensed", 28))
            lbl.setStyleSheet("color: black;")
            lbl.setFixedWidth(350)  # Reduced fixed width to tighten spacing

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
            validator.setLocale(QtCore.QLocale.c())  # Force dot as decimal separator
            inp.setValidator(validator)

            row_layout.addWidget(lbl)
            row_layout.addWidget(inp)
            row_layout.addStretch()  # Push inputs to the left side to keep them tightly together

            self.params_vbox.addLayout(row_layout)
            self.param_inputs[label_text] = inp

        self.main_grid.addLayout(
            self.params_vbox, 1, 0, QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )

        # ---------------------------------------------------------
        # ROW 1, COLUMN 1: Projection Column
        # ---------------------------------------------------------
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
                border-radius: 12px; /* Highly rounded corners */
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
        self.main_grid.addLayout(
            self.projection_vbox, 1, 1, QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )

        # --- 4. FINISH THE SPACER SANDWICH ---
        self.center_h_layout.addLayout(self.main_grid)
        self.center_h_layout.addStretch()  # RIGHT STRETCH

        self.content_layout.addLayout(self.center_h_layout)

        # --- 5. BOTTOM STRETCH FOR VERTICAL CENTERING ---
        self.content_layout.addStretch()

        # Final setup
        self.scroll_area.setWidget(self.scroll_content)
        self.horizontal_container.addWidget(self.scroll_area, stretch=1)
        self.container_layout.addLayout(self.horizontal_container)
        self.main_layout.addWidget(self.container)

        DailySimulatorWindow.setCentralWidget(self.centralwidget)

        self.menu_btn.clicked.connect(self.toggle_sidebar)
        self.template_combo.currentTextChanged.connect(self.update_params_from_template)
        self.reset_btn.clicked.connect(self.reset_defaults)

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

    def create_custom_combo(self, items):
        combo = QtWidgets.QComboBox()
        combo.addItems(items)
        combo.setFixedSize(392, 58)
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
