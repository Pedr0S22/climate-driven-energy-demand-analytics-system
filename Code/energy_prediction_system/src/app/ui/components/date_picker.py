import os

from PyQt6 import QtCore, QtGui, QtWidgets

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")


class DatePicker(QtWidgets.QDateEdit):
    def __init__(self, parent=None, initial_date=QtCore.QDate(2026, 4, 25)):
        super().__init__(parent)
        self.setFixedSize(310, 65)
        self.setCalendarPopup(True)

        # Force English locale for full month names
        self.setLocale(QtCore.QLocale(QtCore.QLocale.Language.English, QtCore.QLocale.Country.UnitedStates))

        self.setDate(initial_date)
        self.setDisplayFormat("MMMM dd yyyy")
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

        # Disable keyboard editing
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)

        # Custom Calendar Widget
        self.calendar = QtWidgets.QCalendarWidget()
        self.calendar.setLocale(self.locale())
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setMinimumWidth(400)

        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { 
                background-color: white; 
                color: black;
                font-family: 'Tw Cen MT';
            }
            QCalendarWidget QToolButton {
                color: white;
                background-color: #000180;
                font-size: 18px;
                font-weight: bold;
                border-radius: 5px;
                margin: 5px;
                height: 40px;
            }
            QCalendarWidget QToolButton#qt_calendar_monthbutton {
                width: 150px;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                qproperty-icon: url(none);
                qproperty-text: "<";
                width: 40px;
            }
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                qproperty-icon: url(none);
                qproperty-text: ">";
                width: 40px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                selection-background-color: #000180;
                selection-color: white;
                background-color: white;
                outline: 0;
            }
        """)

        self.setCalendarWidget(self.calendar)

        # Main styling
        self.setStyleSheet("""
            QDateEdit {
                background-color: #EAEAEF;
                border: 3px solid black;
                border-radius: 30px;
                padding-left: 65px;
            }
            QDateEdit QLineEdit {
                color: black !important;
                font-family: 'Tw Cen MT Condensed';
                font-size: 26px;
                border: none;
                background: transparent;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 310px;
                border: none;
            }
        """)

        # Overlay Icon
        self.cal_icon = QtWidgets.QLabel(self)
        self.cal_icon.setGeometry(20, 15, 35, 35)
        icon_path = os.path.join(BASE_PATH, "calendar.png")
        if os.path.exists(icon_path):
            pix = QtGui.QPixmap(icon_path).scaled(
                35, 35, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation
            )
            self.cal_icon.setPixmap(pix)
        else:
            self.cal_icon.setStyleSheet("background-color: #888; border-radius: 5px;")

        self.cal_icon.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
