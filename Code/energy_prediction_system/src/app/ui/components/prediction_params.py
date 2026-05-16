from PyQt6 import QtCore, QtGui, QtWidgets


class PredictionParams(QtWidgets.QFrame):
    def __init__(self, parent=None, mode="daily"):
        super().__init__(parent)
        self.mode = mode
        self.setFixedWidth(320)
        self.setStyleSheet("""
            QFrame {
                background-color: #EAEAEF;
                border: 2px solid black;
                border-radius: 10px;
            }
        """)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Title
        self.title = QtWidgets.QLabel("Parameters")
        self.title.setFont(QtGui.QFont("Tw Cen MT Condensed", 24, QtGui.QFont.Weight.Bold))
        self.title.setStyleSheet("border: none; color: #000180;")
        self.layout.addWidget(self.title)

        # --- REUSABLE FIXED STYLESHEET ---
        # Adding padding-right prevents the text frame from smothering the native Up Arrow
        fixed_spinbox_style = """
            QSpinBox {
                background-color: white;
                border: 1px solid #000180;
                border-radius: 5px;
                padding-left: 10px;
                padding-right: 24px;  /* CRITICAL: Protects the native up/down arrow space */
                font-size: 16px;
                color: black;
            }
        """

        # Before Parameter
        self.before_label = QtWidgets.QLabel("Days Before:" if mode == "daily" else "Hours Before:")
        self.before_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 18))
        self.before_label.setStyleSheet("border: none; color: black;")
        self.layout.addWidget(self.before_label)

        self.before_input = QtWidgets.QSpinBox()
        self.before_input.setFixedHeight(40)
        self.before_input.setStyleSheet(fixed_spinbox_style)

        # Exact values applied cleanly here
        if mode == "hourly":
            self.before_input.setRange(3, 5)  # Hours before: 3-5
            self.before_input.setValue(3)  # Default: 3
        else:
            self.before_input.setRange(1, 5)  # Days before: 1-5
            self.before_input.setValue(3)  # Default: 3

        self.layout.addWidget(self.before_input)

        # After Parameter
        self.after_label = QtWidgets.QLabel("Days After:" if mode == "daily" else "Hours After:")
        self.after_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 18))
        self.after_label.setStyleSheet("border: none; color: black;")
        self.layout.addWidget(self.after_label)

        self.after_input = QtWidgets.QSpinBox()
        self.after_input.setFixedHeight(40)
        self.after_input.setStyleSheet(fixed_spinbox_style)

        # Exact values applied cleanly here
        if mode == "hourly":
            self.after_input.setRange(1, 24)  # Hours after: 1-24
            self.after_input.setValue(12)  # Default: 12
        else:
            self.after_input.setRange(1, 14)  # Days after: 1-14
            self.after_input.setValue(7)  # Default: 7

        self.layout.addWidget(self.after_input)

        self.layout.addStretch()

        # Submit Button
        self.submit_btn = QtWidgets.QPushButton("Apply Changes")
        self.submit_btn.setFixedHeight(50)
        self.submit_btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #000180;
                color: white;
                border-radius: 25px;
                font-family: 'Tw Cen MT';
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0000AA; }
        """)
        self.layout.addWidget(self.submit_btn)
