from PyQt6 import QtCore, QtGui, QtWidgets


class DriverCard(QtWidgets.QFrame):
    def __init__(self, parent=None, text=""):
        super().__init__(parent)
        self.setFixedSize(280, 88)
        self.setStyleSheet("background-color: #EAEAEF; border: 3px solid black; border-radius: 8px;")

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 15, 0)

        self.label = QtWidgets.QLabel(text)
        self.label.setFont(QtGui.QFont("Tw Cen MT Condensed", 24, QtGui.QFont.Weight.Bold))
        self.label.setStyleSheet("border: none; color: black;")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
