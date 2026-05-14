import os

from PyQt6 import QtCore, QtGui, QtWidgets

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")


class LogoLabel(QtWidgets.QLabel):
    def __init__(self, parent=None, size=(120, 120)):
        super().__init__(parent)
        self.setMinimumSize(QtCore.QSize(*size))
        self.setMaximumSize(QtCore.QSize(*size))
        logo_path = os.path.join(BASE_PATH, "Logo.png")
        if os.path.exists(logo_path):
            self.setPixmap(QtGui.QPixmap(logo_path))
        self.setScaledContents(True)
