import logging

from app.client.models_service import ModelsService
from app.manager.session_manager import SessionManager
from app.ui.components import Sidebar, ToggleSwitch, TopBar
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QMessageBox

logger = logging.getLogger(__name__)


class LoadModelsWorker(QtCore.QThread):
    """Carregar modelos da API em background"""

    finished = QtCore.pyqtSignal(list, str)  # (models_list, error_message)

    def run(self):
        service = ModelsService()
        try:
            data, status = service.get_all_models()
            if status == 200:
                self.finished.emit(data, "")
            else:
                error = data.get("detail", f"Error {status}")
                self.finished.emit([], str(error))
        except Exception as e:
            self.finished.emit([], str(e))


class ActivateModelWorker(QtCore.QThread):
    """Ativar um modelo em background"""

    finished = QtCore.pyqtSignal(object, str)  # (response_data, error_message)

    def __init__(self, model_id):
        super().__init__()
        self.model_id = model_id

    def run(self):
        service = ModelsService()
        try:
            data, status = service.activate_model(self.model_id)
            if status == 200:
                self.finished.emit(data, "")
            else:
                error = data.get("detail", f"Error {status}")
                self.finished.emit(None, str(error))
        except Exception as e:
            self.finished.emit(None, str(e))


class ModelRow(QtWidgets.QWidget):
    def __init__(self, model_type, date, dataset, rmse, mae, r2, is_active=False, model_id=None, parent=None):
        super().__init__(parent)
        self.model_id = model_id  # Guarda o ID do modelo para operações de ativação
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
        self.rows = []  # List to track rows for exclusive selection
        self.setFixedWidth(850)  # Fixed width for the table
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

        for h_text, w in zip(headers, widths, strict=False):
            lbl = QtWidgets.QLabel(h_text)
            lbl.setFont(header_font)
            lbl.setFixedWidth(w)
            lbl.setAlignment(
                QtCore.Qt.AlignmentFlag.AlignCenter if h_text == "Active" else QtCore.Qt.AlignmentFlag.AlignLeft
            )
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

    def add_row(self, model_type, date, dataset, rmse, mae, r2, is_active=False, model_id=None):
        row = ModelRow(model_type, date, dataset, rmse, mae, r2, is_active, model_id)
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

    def clear_all_rows(self):
        """Remove todas as linhas do frame"""
        for row in self.rows:
            self.rows_layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()

    def get_active_model_id(self) -> int | None:
        """Retorna o ID do modelo atualmente selecionado (toggle ativo)"""
        for row in self.rows:
            if row.toggle.active:
                return row.model_id
        return None


class Ui_ModelManagementWindow:
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("ModelManagementWindow")
        MainWindow.resize(1446, 1029)
        MainWindow.setStyleSheet("background-color: #F3F3F3;")

        # Guarda referência ao MainWindow para usar em callbacks
        self.MainWindow = MainWindow

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

        self.home_btn = self.sidebar.add_menu_header("Home", is_toggle=False, active=False)
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

        self.model_btn = self.sidebar.add_menu_header("Model Management", is_toggle=False, active=True)

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

        # HOURLY MODEL SECTION (inicialmente vazia - dados carregados da API)
        self.hourly_section = self.create_centered_section("Hourly Model", "hourly_frame")
        self.tables_centering_layout.addLayout(self.hourly_section)

        # DAILY MODEL SECTION (inicialmente vazia - dados carregados da API)
        self.daily_section = self.create_centered_section("Daily Model", "daily_frame")
        self.tables_centering_layout.addLayout(self.daily_section)

        # Mensagem de placeholder enquanto os dados não são carregados
        self.placeholder_label = QtWidgets.QLabel("Click 'Load Models' to fetch data from the server...")
        self.placeholder_label.setFont(QtGui.QFont("Tw Cen MT", 18))
        self.placeholder_label.setStyleSheet("color: #666666;")
        self.placeholder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tables_centering_layout.addWidget(self.placeholder_label)

        self.content_layout.addLayout(self.tables_centering_layout)

        # BUTTONS AT BOTTOM
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.addStretch()

        self.load_btn = QtWidgets.QPushButton("Load Models")
        self.load_btn.setFixedSize(220, 60)
        self.load_btn.setFont(QtGui.QFont("Tw Cen MT", 24, QtGui.QFont.Weight.Bold))
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #800002;
                border: 3px solid black;
                border-radius: 20px;
                color: white;
            }
            QPushButton:hover {
                background-color: #A00002;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.buttons_layout.addWidget(self.load_btn)

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
            QPushButton:disabled {
                background-color: #666666;
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

        # --- CONEXÕES DOS BOTÕES ---
        self.load_btn.clicked.connect(self.load_models)
        self.save_btn.clicked.connect(self.save_changes)

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

    def load_models(self):
        """Carrega a lista de modelos a partir da API e popula as tabelas"""
        self.load_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.load_btn.setText("Loading...")

        # Esconde o placeholder se existir
        if hasattr(self, "placeholder_label"):
            self.placeholder_label.setVisible(False)

        self.load_worker = LoadModelsWorker()
        self.load_worker.finished.connect(self._on_models_loaded)
        self.load_worker.finished.connect(self.load_worker.deleteLater)
        self.load_worker.start()

    def _on_models_loaded(self, models, error):
        """Callback executado quando os modelos são carregados da API"""
        self.load_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.load_btn.setText("Load Models")

        if error:
            QMessageBox.warning(self.MainWindow, "Error", f"Failed to load models:\n{error}")
            return

        if not models:
            QMessageBox.information(self.MainWindow, "Info", "No models found on the server.")
            return

        # Limpa as tabelas existentes
        self.hourly_frame.clear_all_rows()
        self.daily_frame.clear_all_rows()

        # Separa modelos por tipo
        daily_models = [m for m in models if m.get("model_pred_type") == "daily"]
        hourly_models = [m for m in models if m.get("model_pred_type") == "hourly"]

        # Popula a tabela de modelos Daily
        for model in daily_models:
            creation_date = model.get("model_creation_date", "")
            # Formata a data para mostrar só YYYY-MM-DD HH:MM
            if creation_date:
                try:
                    # Tenta parse e formatar a data
                    from datetime import datetime

                    dt = datetime.fromisoformat(creation_date.replace("Z", "+00:00"))
                    creation_date = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, AttributeError):
                    creation_date = creation_date[:16] if len(creation_date) >= 16 else creation_date

            self.daily_frame.add_row(
                model_type=model.get("model_type", "Unknown"),
                date=creation_date,
                dataset=model.get("dataset_selected", "N/A"),
                rmse=f"{model.get('rmse', 0):.2f}" if model.get("rmse") is not None else "N/A",
                mae=f"{model.get('mae', 0):.2f}" if model.get("mae") is not None else "N/A",
                r2=f"{model.get('r2', 0):.4f}" if model.get("r2") is not None else "N/A",
                is_active=model.get("is_active", False),
                model_id=model.get("model_name_id"),
            )

        # Popula a tabela de modelos Hourly
        for model in hourly_models:
            creation_date = model.get("model_creation_date", "")
            if creation_date:
                try:
                    from datetime import datetime

                    dt = datetime.fromisoformat(creation_date.replace("Z", "+00:00"))
                    creation_date = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, AttributeError):
                    creation_date = creation_date[:16] if len(creation_date) >= 16 else creation_date

            self.hourly_frame.add_row(
                model_type=model.get("model_type", "Unknown"),
                date=creation_date,
                dataset=model.get("dataset_selected", "N/A"),
                rmse=f"{model.get('rmse', 0):.2f}" if model.get("rmse") is not None else "N/A",
                mae=f"{model.get('mae', 0):.2f}" if model.get("mae") is not None else "N/A",
                r2=f"{model.get('r2', 0):.4f}" if model.get("r2") is not None else "N/A",
                is_active=model.get("is_active", False),
                model_id=model.get("model_name_id"),
            )
        self._originally_active = {"daily": None, "hourly": None}
        for model in models:
            if model.get("is_active"):
                self._originally_active[model["model_pred_type"]] = model["model_name_id"]

        logger.info(f"Loaded {len(daily_models)} daily and {len(hourly_models)} hourly models from API")

    def save_changes(self):
        if SessionManager.get_role() != "admin":
            QMessageBox.warning(self.MainWindow, "Access Denied", "Only administrators can activate models.")
            return
        """Ativa o modelo selecionado em cada secção (daily e/ou hourly)"""
        # Verifica quais modelos estão com toggle ativo em cada frame
        daily_active_id = self.daily_frame.get_active_model_id()
        hourly_active_id = self.hourly_frame.get_active_model_id()

        models_to_activate = []
        if daily_active_id is not None and daily_active_id != self._originally_active.get("daily"):
            models_to_activate.append(("daily", daily_active_id))
        if hourly_active_id is not None and hourly_active_id != self._originally_active.get("hourly"):
            models_to_activate.append(("hourly", hourly_active_id))

        if not models_to_activate:
            QMessageBox.information(
                self.MainWindow,
                "Info",
                "Please select at least one model to activate.\n"
                "Use the toggle switches to select an active model for Daily and/or Hourly predictions.",
            )
            return

        # Confirmação do utilizador
        msg = "This will activate the following models:\n\n"
        for freq, mid in models_to_activate:
            msg += f"  • {freq.capitalize()} Model (ID: {mid})\n"
        msg += "\nDo you want to continue?"

        reply = QMessageBox.question(
            self.MainWindow,
            "Confirm Activation",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Desativa botões durante a operação
        self.load_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.save_btn.setText("Saving...")

        # Ativa cada modelo sequencialmente
        self._pending_activations = models_to_activate
        self._activation_errors = []
        self._activate_next_model()

    def _activate_next_model(self):
        if not self._pending_activations:
            self._on_all_activations_complete()
            return

        freq, model_id = self._pending_activations.pop(0)
        self.activate_worker = ActivateModelWorker(model_id)  # ← self.activate_worker
        self.activate_worker.finished.connect(
            lambda data, error, f=freq, mid=model_id: self._on_activation_complete(f, mid, data, error)
        )
        self.activate_worker.finished.connect(self.activate_worker.deleteLater)
        self.activate_worker.start()

    def _on_activation_complete(self, frequency, model_id, data, error):
        """Callback quando um modelo é ativado"""
        if error:
            self._activation_errors.append(f"{frequency.capitalize()} Model (ID {model_id}): {error}")
        else:
            logger.info(f"{frequency.capitalize()} model {model_id} activated successfully")

        # Continua para o próximo modelo
        self._activate_next_model()

    def _on_all_activations_complete(self):
        """Callback final após todas as ativações"""
        self.load_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.save_btn.setText("Save changes")

        if self._activation_errors:
            error_msg = "Some activations failed:\n\n" + "\n".join(self._activation_errors)
            QMessageBox.warning(self.MainWindow, "Activation Errors", error_msg)
        else:
            QMessageBox.information(self.MainWindow, "Success", "All selected models have been activated successfully!")

        # Recarrega os modelos para mostrar o estado atualizado
        self.load_models()
