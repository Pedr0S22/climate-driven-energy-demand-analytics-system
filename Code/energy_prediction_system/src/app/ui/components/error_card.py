from PyQt6 import QtCore, QtGui, QtWidgets

class ErrorCard(QtWidgets.QFrame):
    def __init__(self, parent=None, message="Error fetching data from API"):
        super().__init__(parent)
        self.setMinimumSize(800, 450)
        self.setStyleSheet("""
            QFrame {
                background-color: #EAEAEF;
                border: 3px solid black;
                border-radius: 10px;
            }
        """)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.setSpacing(20)

        # Warning Icon (Yellow Triangle) - Using a QLabel with stylized text/drawing
        self.icon_label = QtWidgets.QLabel("⚠") # Standard warning sign emoji/char
        font_icon = QtGui.QFont("Arial", 80)
        self.icon_label.setFont(font_icon)
        self.icon_label.setStyleSheet("color: #FFD700; border: none;") # Gold/Yellow
        self.icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.icon_label)

        # Error Message
        self.msg_label = QtWidgets.QLabel(message)
        self.msg_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 28, QtGui.QFont.Weight.Bold))
        self.msg_label.setStyleSheet("color: black; border: none;")
        self.msg_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setWordWrap(True)
        self.layout.addWidget(self.msg_label)

        # Retry Hint
        self.hint_label = QtWidgets.QLabel("Please verify your connection and try again.")
        self.hint_label.setFont(QtGui.QFont("Tw Cen MT Condensed", 18))
        self.hint_label.setStyleSheet("color: #555555; border: none;")
        self.hint_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.hint_label)

    def set_message(self, message):
        self.msg_label.setText(message)
