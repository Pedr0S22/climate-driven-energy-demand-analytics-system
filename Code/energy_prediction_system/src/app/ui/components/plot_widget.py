import matplotlib.dates as mdates
import numpy as np
from dateutil.parser import parse
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6 import QtWidgets

from .error_card import ErrorCard


class PlotWidget(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 450)

        # Page 0: Chart
        self.chart_frame = QtWidgets.QFrame()
        self.chart_frame.setStyleSheet("""
            QFrame {
                background-color: #EAEAEF;
                border: 3px solid black;
                border-radius: 10px;
            }
        """)
        self.chart_layout = QtWidgets.QVBoxLayout(self.chart_frame)
        self.chart_layout.setContentsMargins(10, 10, 10, 10)

        self.figure = Figure(facecolor="#EAEAEF")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#EAEAEF")

        # Initial empty plot
        self.ax.text(
            0.5, 0.5, "Waiting for data from API...", ha="center", va="center", fontsize=20, fontname="sans-serif"
        )
        self.ax.set_axis_off()

        self.chart_layout.addWidget(self.canvas)
        self.addWidget(self.chart_frame)

        # Page 1: Error Card
        self.error_view = ErrorCard()
        self.addWidget(self.error_view)

        self.setCurrentIndex(0)  # Start with chart/waiting state

    def show_error(self, message=None):
        """Switches the view to show the error card."""
        if message:
            self.error_view.set_message(message)
        self.setCurrentIndex(1)

    def update_chart(self, x_data, y_real, y_pred=None):
        """Updates the chart and switches view back to chart page."""
        self.ax.clear()
        self.ax.set_axis_on()
        self.ax.set_facecolor("#EAEAEF")

        # Convert ISO strings to datetime objects
        if x_data and isinstance(x_data[0], str):
            x_dt = [parse(t) for t in x_data]
        else:
            x_dt = x_data

        # Real Data (Solid Line)
        self.ax.plot(x_dt[: len(y_real)], y_real, color="#000180", linewidth=3, label="Historical")

        # Prediction Data (Dashed Line)
        if y_pred is not None:
            # We connect the last historical point with the first prediction point
            full_pred_x = x_dt[len(y_real) - 1 :]
            full_pred_y = np.concatenate(([y_real[-1]], y_pred))

            if len(full_pred_x) == len(full_pred_y):
                self.ax.plot(full_pred_x, full_pred_y, color="#000180", linewidth=3, linestyle="--", label="Forecast")
            else:
                self.ax.plot(
                    x_dt[len(y_real) : len(y_real) + len(y_pred)],
                    y_pred,
                    color="#000180",
                    linewidth=3,
                    linestyle="--",
                    label="Forecast",
                )

        # Formatting
        self.ax.set_title("Energy Demand Projection", fontsize=18, fontname="sans-serif", fontweight="bold")
        self.ax.set_xlabel("Time (UTC)", fontsize=12, fontname="sans-serif")
        self.ax.set_ylabel("Load (MWh)", fontsize=12, fontname="sans-serif")

        # X-Axis Time Formatting
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()  # Rotates labels automatically

        self.ax.legend(loc="upper left")
        self.ax.grid(True, linestyle=":", alpha=0.6)

        # Refresh
        self.figure.tight_layout()
        self.canvas.draw()
        self.setCurrentIndex(0)
