from PyQt6 import QtWidgets


class StyledInput(QtWidgets.QLineEdit):
    def __init__(self, parent=None, placeholder="", is_password=False):
        super().__init__(parent)
        self.setMinimumHeight(35)
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            
        self.setStyleSheet("""
            QLineEdit {
                background-color: rgb(234, 234, 239);
                border: 1px solid black;
                border-radius: 4px;
                color: black;
                padding: 2px;
                font-family: 'Tw Cen MT Condensed';
                font-size: 18px;
            }
        """)
