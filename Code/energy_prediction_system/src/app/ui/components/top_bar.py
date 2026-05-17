import os

from PyQt6 import QtCore, QtGui, QtWidgets

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")


class TopBar(QtWidgets.QFrame):
    def __init__(self, parent=None, title=""):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setMaximumHeight(80)
        self.setStyleSheet("""
            background-color: #000180;
            border: 3px solid #040659;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        """)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(40, 0, 40, 0)

        # Menu Button
        self.menu_btn = QtWidgets.QToolButton()
        icon_menu = QtGui.QIcon()
        icon_menu.addPixmap(
            QtGui.QPixmap(
                os.path.join(
                    BASE_PATH,
                    "menu_button.png")),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.Off)
        self.menu_btn.setIcon(icon_menu)
        self.menu_btn.setIconSize(QtCore.QSize(46, 38))
        self.menu_btn.setCursor(
            QtGui.QCursor(
                QtCore.Qt.CursorShape.PointingHandCursor))
        self.menu_btn.setStyleSheet("background: transparent; border: none;")
        self.layout.addWidget(self.menu_btn)

        self.layout.addStretch()

        # Title
        self.title_label = QtWidgets.QLabel(title)
        font_title = QtGui.QFont(
            "Tw Cen MT Condensed",
            36,
            QtGui.QFont.Weight.Bold)
        self.title_label.setFont(font_title)
        self.title_label.setStyleSheet(
            "color: white; border: none; background: transparent;")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.layout.addStretch()

        # Logout Button
        self.logout_btn = QtWidgets.QPushButton("Log out")
        self.logout_btn.setFixedSize(228, 52)
        font_logout = QtGui.QFont("Tw Cen MT", 24, QtGui.QFont.Weight.Bold)
        self.logout_btn.setFont(font_logout)
        self.logout_btn.setCursor(QtGui.QCursor(
            QtCore.Qt.CursorShape.PointingHandCursor))
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #83E7FF;
                border: 3px solid #000000;
                border-radius: 26px;
                color: black;
            }
            QPushButton:hover {
                background-color: #A0EEFF;
            }
        """)
        self.layout.addWidget(self.logout_btn)
