from PyQt6 import QtCore, QtGui, QtWidgets

class ToggleSwitch(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None, active=False):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._active = active
        self._circle_pos = 5 if not active else 35
        
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        
        # Background track
        bg_color = QtGui.QColor("#2ECC71") if self._active else QtGui.QColor("#BDC3C7")
        painter.setBrush(bg_color)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)
        
        # Circle (The "bola")
        painter.setBrush(QtGui.QColor("white"))
        painter.drawEllipse(self._circle_pos, 5, 20, 20)

    def mousePressEvent(self, event):
        self._active = not self._active
        
        # Simple animation state
        self._circle_pos = 35 if self._active else 5
        self.update()
        self.clicked.emit(self._active)

    def is_active(self):
        return self._active

    def set_active(self, state):
        self._active = state
        self._circle_pos = 35 if state else 5
        self.update()
