from PyQt6 import QtCore, QtGui, QtWidgets

class TimePicker(QtWidgets.QTimeEdit):
    def __init__(self, parent=None, initial_hour=12):
        super().__init__(parent)
        
        self.setFixedSize(392, 58) 
        self.setTime(QtCore.QTime(initial_hour, 0))
        
        # Format to show only hours like "12h"
        self.setDisplayFormat("HH'h'")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        
        # Style the internal line edit
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)
        
        # Main styling to match QComboBox Template selector logic
        self.setStyleSheet("""
            QTimeEdit {
                background-color: #EAEAEF;
                border: 4px solid black;
                border-radius: 8px;
                color: black;
                font-family: 'Tw Cen MT Condensed';
                font-size: 28px;
            }
            QTimeEdit QLineEdit {
                color: black;
                background: transparent;
                border: none;
            }
        """)

    def stepBy(self, steps):
        """Force stepping only by hour."""
        super().stepBy(steps)
