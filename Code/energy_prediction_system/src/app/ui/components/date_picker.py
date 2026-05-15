import os

from PyQt6 import QtCore, QtGui, QtWidgets

BASE_PATH = os.path.join(os.path.dirname(__file__), "..", "resources")


class DatePicker(QtWidgets.QDateEdit):
    def __init__(self, parent=None, initial_date=None, show_icon=True):
        super().__init__(parent)

        if initial_date is None:
            initial_date = QtCore.QDate.currentDate().addDays(1)

        self.setFixedSize(392, 58)
        self.setCalendarPopup(True)

        # Set format to match mockup (dd/MM/yyyy)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setDate(initial_date)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

        # Style the internal line edit
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.lineEdit().setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft |
                                     QtCore.Qt.AlignmentFlag.AlignVCenter)

        # Custom Calendar Widget
        self.calendar = QtWidgets.QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(
            QtWidgets.QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
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

        # Restored side-box styling
        padding_left = 65 if show_icon else 20
        self.setStyleSheet(f"""
            QDateEdit {{
                background-color: #EAEAEF;
                border: 4px solid black;
                border-radius: 8px;
                color: black;
                font-family: 'Tw Cen MT Condensed';
                font-size: 28px;
                padding-left: {padding_left}px;
            }}
            QDateEdit QLineEdit {{
                color: black;
                background: transparent;
                border: none;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 50px;
                background-color: #CCCCCC;
                border-left: 1px solid #626060;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
            }}
            QDateEdit::down-arrow {{
                image: none;
                border-left: 10px solid transparent;
                border-right: 10px solid transparent;
                border-top: 12px solid black;
                margin-top: 2px;
            }}
        """)

        # Overlay Icon
        self.cal_icon = QtWidgets.QLabel(self)
        self.cal_icon.setGeometry(20, 15, 35, 35)
        if show_icon:
            icon_path = os.path.join(BASE_PATH, "calendar.png")
            if os.path.exists(icon_path):
                pix = QtGui.QPixmap(icon_path).scaled(
                    35,
                    35,
                    QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                    QtCore.Qt.TransformationMode.SmoothTransformation)
                self.cal_icon.setPixmap(pix)
            else:
                self.cal_icon.setStyleSheet(
                    "background-color: #888; border-radius: 5px;")
        else:
            self.cal_icon.hide()

        self.cal_icon.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
