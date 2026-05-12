from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

from app.ui.components import Sidebar, ToggleSwitch, TopBar


class ModelRow(QtWidgets.QWidget):
    def __init__(self, model_type, date, dataset, rmse, mae, r2, is_active=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(10)

        font = QtGui.QFont("Tw Cen MT", 16)
        
        # Consistent widths matching the header
        self.add_label(model_type, 140, font, layout)
        self.add_label(date, 180, font, layout)
        self.add_label(dataset, 120, font, layout)
        self.add_label(rmse, 80, font, layout)
        self.add_label(mae, 80, font, layout)
        self.add_label(r2, 80, font, layout)

        # Toggle Switch Container (Fixed width 100 to match header)
        toggle_container = QtWidgets.QWidget()
        toggle_container.setFixedWidth(100)
        toggle_layout = QtWidgets.QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        self.toggle = ToggleSwitch(active=is_active)
        toggle_layout.addWidget(self.toggle, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(toggle_container)

    def add_label(self, text, width, font, layout):
        lbl = QtWidgets.QLabel(text)
        lbl.setFont(font)
        lbl.setFixedWidth(width)
        lbl.setStyleSheet("color: black;")
        layout.addWidget(lbl)

class ModelFrame(QtWidgets.QFrame):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.rows = [] # List to track rows for exclusive selection
        self.setFixedWidth(850) # Fixed width for the table
        self.setStyleSheet("""
            QFrame {
                background-color: #EAEAEF;
                border: 3px solid black;
                border-radius: 10px;
            }
        """)
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 10, 0, 10)
        self.main_layout.setSpacing(0)

        # Header
        header_widget = QtWidgets.QWidget()
        header_widget.setFixedHeight(50)
        header_widget.setStyleSheet("border: none; background: transparent;")
        header_layout = QtWidgets.QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(10)

        header_font = QtGui.QFont("Tw Cen MT Condensed", 18, QtGui.QFont.Weight.Bold)
        
        headers = ["Model Type", "Creation Date", "Dataset", "RMSE", "MAE", "R2", "Active"]
        widths = [140, 180, 120, 80, 80, 80, 100]
        
        for h_text, w in zip(headers, widths):
            lbl = QtWidgets.QLabel(h_text)
            lbl.setFont(header_font)
            lbl.setFixedWidth(w)
            lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter if h_text == "Active" else QtCore.Qt.AlignmentFlag.AlignLeft)
            lbl.setStyleSheet("color: black; border: none;")
            header_layout.addWidget(lbl)
        
        self.main_layout.addWidget(header_widget)

        # Rows Container
        self.rows_container = QtWidgets.QWidget()
        self.rows_container.setStyleSheet("border: none; background: transparent;")
        self.rows_layout = QtWidgets.QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(5)
        self.main_layout.addWidget(self.rows_container)
        self.main_layout.addStretch()

    def add_row(self, model_type, date, dataset, rmse, mae, r2, is_active=False):
        row = ModelRow(model_type, date, dataset, rmse, mae, r2, is_active)
        row.setStyleSheet("border: none; border-bottom: 1px solid #CCCCCC;")
        self.rows_layout.addWidget(row)
        self.rows.append(row)
        
        # Connect toggle signal to ensure only one is active
        row.toggle.clicked.connect(lambda state, r=row: self._handle_toggle(r, state))

    def _handle_toggle(self, clicked_row, state):
        if state:
            # If one is turned ON, turn all others OFF
            for row in self.rows:
                if row != clicked_row:
                    row.toggle.set_active(False)
        else:
            # Force at least one to be active
            clicked_row.toggle.set_active(True)

class Ui_ModelManagementWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("ModelManagementWindow")
        MainWindow.resize(1446, 1029)
        MainWindow.setStyleSheet("background-color: #F3F3F3;")

        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(16, 18, 16, 18)
        self.main_layout.setSpacing(0)

        # Main Outer Container
        self.container = QtWidgets.QFrame(parent=self.centralwidget)
        self.container.setStyleSheet("background-color: #CCCCCC; border-radius: 5px; border: none;")
        self.container_layout = QtWidgets.QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(5, 5)
        shadow.setColor(QtGui.QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        # 1. TOP BAR
        self.top_bar = TopBar(parent=self.container, title="Model Management")
        self.container_layout.addWidget(self.top_bar)
        
        self.logout_btn = self.top_bar.logout_btn
        self.menu_btn = self.top_bar.menu_btn

        # --- HORIZONTAL LAYOUT FOR SIDEBAR + CONTENT ---
        self.horizontal_container = QtWidgets.QHBoxLayout()
        self.horizontal_container.setSpacing(0)

        # --- SIDEBAR ---
        self.sidebar = Sidebar(parent=self.container)
        self.sidebar.setFixedWidth(300)
        
        self.home_btn = self.sidebar.add_menu_item("Home", active=False)
        self.sidebar.add_menu_header("Predictions:")
        self.daily_btn = self.sidebar.add_menu_item("daily", active=False, indent=True, header_parent="Predictions:")
        self.hourly_btn = self.sidebar.add_menu_item("hourly", active=False, indent=True, header_parent="Predictions:")
        
        self.sidebar.add_menu_header("Scenario Simulation:")
        self.sim_daily_btn = self.sidebar.add_menu_item("daily", active=False, indent=True, header_parent="Scenario Simulation:")
        self.sim_hourly_btn = self.sidebar.add_menu_item("hourly", active=False, indent=True, header_parent="Scenario Simulation:")
        
        self.model_btn = self.sidebar.add_menu_item("Model Management", active=True)
        
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
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(30)

        # Wrapper to center tables horizontally
        self.tables_centering_layout = QtWidgets.QVBoxLayout()
        self.tables_centering_layout.setSpacing(40)

        # HOURLY MODEL SECTION
        self.hourly_section = self.create_centered_section("Hourly Model", "hourly_frame")
        self.tables_centering_layout.addLayout(self.hourly_section)
        
        # Add sample data to hourly_frame (only one active)
        self.hourly_frame.add_row("RandomForest", "2026-01-24 14:30", "full", "3.52", "2.10", "0.98", is_active=True)
        self.hourly_frame.add_row("LinearReg", "2025-10-10 09:15", "pca", "4.05", "2.54", "0.95", is_active=False)
        self.hourly_frame.add_row("RandomForest", "2026-02-24 11:00", "selected", "5.21", "3.02", "0.90", is_active=False)

        # DAILY MODEL SECTION
        self.daily_section = self.create_centered_section("Daily Model", "daily_frame")
        self.tables_centering_layout.addLayout(self.daily_section)
        
        # Add sample data to daily_frame (only one active)
        self.daily_frame.add_row("RandomForest", "2026-01-24 15:45", "full", "150.22", "100.51", "0.99", is_active=True)
        self.daily_frame.add_row("LinearReg", "2025-10-10 10:30", "pca", "180.54", "120.32", "0.97", is_active=False)
        self.daily_frame.add_row("RandomForest", "2026-02-24 12:15", "selected", "210.88", "150.04", "0.92", is_active=False)

        self.content_layout.addLayout(self.tables_centering_layout)

        # BUTTONS AT BOTTOM
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addStretch()
        
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.setFixedSize(180, 60)
        self.reset_btn.setFont(QtGui.QFont("Tw Cen MT", 24, QtGui.QFont.Weight.Bold))
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #800002;
                border: 3px solid black;
                border-radius: 20px;
                color: white;
            }
            QPushButton:hover {
                background-color: #A00002;
            }
        """)
        self.buttons_layout.addWidget(self.reset_btn)

        self.save_btn = QtWidgets.QPushButton("Save changes")
        self.save_btn.setFixedSize(280, 60)
        self.save_btn.setFont(QtGui.QFont("Tw Cen MT", 24, QtGui.QFont.Weight.Bold))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #000180;
                border: 3px solid black;
                border-radius: 20px;
                color: white;
            }
            QPushButton:hover {
                background-color: #0001A0;
            }
        """)
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addStretch()
        
        self.content_layout.addLayout(self.buttons_layout)
        self.content_layout.addStretch()

        # Final setup
        self.scroll_area.setWidget(self.scroll_content)
        self.horizontal_container.addWidget(self.scroll_area, stretch=1)
        self.container_layout.addLayout(self.horizontal_container)
        self.main_layout.addWidget(self.container)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menu_btn.clicked.connect(self.toggle_sidebar)

    def create_centered_section(self, title, frame_attr_name):
        section_layout = QtWidgets.QVBoxLayout()
        
        title_lbl = QtWidgets.QLabel(title)
        title_lbl.setFont(QtGui.QFont("Tw Cen MT Condensed", 36, QtGui.QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: black;")
        
        # Center title
        title_wrapper = QtWidgets.QHBoxLayout()
        title_wrapper.addStretch()
        title_wrapper.addWidget(title_lbl)
        title_wrapper.addStretch()
        section_layout.addLayout(title_wrapper)

        # Create and center frame
        frame = ModelFrame(title)
        setattr(self, frame_attr_name, frame)
        
        frame_wrapper = QtWidgets.QHBoxLayout()
        frame_wrapper.addStretch()
        frame_wrapper.addWidget(frame)
        frame_wrapper.addStretch()
        section_layout.addLayout(frame_wrapper)
        
        return section_layout

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())
