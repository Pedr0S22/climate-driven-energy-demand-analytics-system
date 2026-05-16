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
        self.title.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.title.setStyleSheet("border: none; color: #000180;")
        self.layout.addWidget(self.title)

        spinbox_style = """
            QSpinBox {
                background-color: white;
                border: 2px solid #000180;
                border-radius: 5px;
                padding-left: 15px;
                padding-right: 40px; 
                font-size: 20px;
                color: black;
                min-height: 40px; /* Locks the box model to prevent bleeding */
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 35px;
                background-color: #EAEAEF;
                border-left: 2px solid #000180;
                border-bottom: 1px solid #000180;
                border-top-right-radius: 3px;
                margin-top: 2px; /* Pulls button safely inside the rounded border */
                margin-right: 2px;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 35px;
                background-color: #EAEAEF;
                border-left: 2px solid #000180;
                border-top: 1px solid #000180;
                border-bottom-right-radius: 3px;
                margin-bottom: 2px; /* Pulls button safely inside the rounded border */
                margin-right: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #CCCCCC;
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #AAAAAA;
            }
            
            /* SVGs for the Plus and Minus signs */
            QSpinBox::up-arrow {
                image: url("data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMTAg
                MTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+
                PHBhdGggZD0iTTIgNSBMOCA1IE01IDIgTDUgOCIgc3Ryb2tlPSIjMDAwMTgwIiBzdHJ
                va2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==");
                width: 14px;
                height: 14px;
            }
            QSpinBox::down-arrow {
                image: url("data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMTAgMT
                AiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+
                PHBhdGggZD0iTTIgNSBMOCA1IiBzdHJva2U9IiMwMDAxODAiIHN0cm9rZS13aWR0aD
                0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PC9zdmc+");
                width: 14px;
                height: 14px;
            }
            
            /* Disabled states */
            QSpinBox::up-arrow:disabled, QSpinBox::up-arrow:off {
                image: url("data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PS
                IwIDAgMTAgMTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+
                PHBhdGggZD0iTTIgNSBMOCA1IE01IDIgTDUgOCIgc3Ryb2tlPSIjQTBBMEEwIiBzdHJva2Ut
                d2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPjwvc3ZnPg==");
            }
            QSpinBox::down-arrow:disabled, QSpinBox::down-arrow:off {
                image: url("data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMTAg
                MTAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTIgNS
                BMOCA1IiBzdHJva2U9IiNBMEEwQTAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbm
                VjYXA9InJvdW5kIi8+PC9zdmc+");
            }
        """

        # Before Parameter
        self.before_label = QtWidgets.QLabel("Days Before:" if mode == "daily" else "Hours Before:")
        self.before_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 18))
        self.before_label.setStyleSheet("border: none; color: black;")
        self.layout.addWidget(self.before_label)

        self.before_input = QtWidgets.QSpinBox()
        # Use PlusMinus symbols for UC requirement
        self.before_input.setFixedHeight(45)
        if mode == "hourly":
            self.before_input.setRange(3, 5)
            self.before_input.setValue(3)
        else:
            self.before_input.setRange(1, 5)
            self.before_input.setValue(3)

        self.before_input.setStyleSheet(spinbox_style)
        self.layout.addWidget(self.before_input)

        # After Parameter
        self.after_label = QtWidgets.QLabel("Days After:" if mode == "daily" else "Hours After:")
        self.after_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 18))
        self.after_label.setStyleSheet("border: none; color: black;")
        self.layout.addWidget(self.after_label)

        self.after_input = QtWidgets.QSpinBox()
        self.after_input.setFixedHeight(45)
        if mode == "hourly":
            self.after_input.setRange(1, 24)
            self.after_input.setValue(12)
        else:
            self.after_input.setRange(1, 14)
            self.after_input.setValue(7)

        self.after_input.setStyleSheet(spinbox_style)
        self.layout.addWidget(self.after_input)

        self.layout.addStretch()

        # Submit Button
        self.submit_btn = QtWidgets.QPushButton("Apply Changes")
        self.submit_btn.setFixedHeight(55)
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
