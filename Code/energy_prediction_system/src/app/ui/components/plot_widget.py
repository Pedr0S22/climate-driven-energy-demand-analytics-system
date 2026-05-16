import datetime
from datetime import timedelta

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

        # Data storage for hover logic
        self.x_dt = []
        self.x_nums = np.array([])  # Cached numeric dates for high-performance hover
        self.y_total = []
        self.main_driver = "N/A"

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

        # Interactive components (initial setup)
        self._init_interactive_elements()

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

        # Connect events
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)
        self.canvas.mpl_connect("draw_event", self.on_draw)  # Solves the Blitting Ghost bug!

        self.setCurrentIndex(0)  # Start with chart/waiting state

    def _init_interactive_elements(self):
        """Initializes or re-initializes hover elements."""
        # Transparent dashed grey line (animated=True prevents it from burning into the background)
        self.vline = self.ax.axvline(
            color="grey", linestyle="--", linewidth=1.5, visible=False, alpha=0.5, animated=True
        )

        # Transparent grey box for tooltip (animated=True prevents it from burning into the background)
        self.annot = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(15, 15),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc="grey", ec="black", alpha=0.6),  # noqa C408
            color="white",
            fontsize=10,
            fontweight="bold",
            animated=True,
            annotation_clip=False,
        )
        self.annot.set_visible(False)

    def on_draw(self, event):
        """Automatically updates the clean background snapshot whenever the canvas redraws/resizes."""
        # Because we set animated=True earlier, this snapshot is guaranteed
        # to never accidentally capture the tooltip or vertical line!
        self.bg = self.canvas.copy_from_bbox(self.figure.bbox)

        # Restore interactive elements immediately if they were visible during a window resize
        if hasattr(self, "vline") and self.vline.get_visible():
            self.ax.draw_artist(self.vline)
        if hasattr(self, "annot") and self.annot.get_visible():
            self.ax.draw_artist(self.annot)

    def show_error(self, message=None):
        """Switches the view to show the error card."""
        if message:
            self.error_view.set_message(message)
        self.setCurrentIndex(1)

    def update_chart(self, x_data, y_real, y_pred=None, drivers=None):
        """Updates the chart and switches view back to chart page."""
        self.ax.clear()
        self.ax.set_axis_on()
        self.ax.set_facecolor("#EAEAEF")

        # Save driver info for tooltip
        if drivers and len(drivers) > 0:
            self.main_driver = drivers[0]
        else:
            self.main_driver = "N/A"

        # Convert ISO strings to datetime objects
        if x_data and len(x_data) > 0 and isinstance(x_data[0], str):
            self.x_dt = [parse(t) for t in x_data]
        else:
            self.x_dt = x_data

        # CACHE THE NUMERIC DATES ONCE FOR HIGH-PERFORMANCE HOVER
        self.x_nums = np.array([mdates.date2num(t) for t in self.x_dt])

        # Real Data (Solid Line)
        self.ax.plot(
            self.x_dt[: len(y_real)], y_real, color="#000180", linewidth=3, label="Historical", marker="o", markersize=5
        )

        # Prediction Data (Dashed Line)
        if y_pred is not None:
            # API safety check: Ensure we have historical data before trying to connect the lines
            if len(y_real) > 0:
                full_pred_x = self.x_dt[len(y_real) - 1 :]
                full_pred_y = np.concatenate(([y_real[-1]], y_pred))

                if len(full_pred_x) == len(full_pred_y):
                    self.ax.plot(
                        full_pred_x,
                        full_pred_y,
                        color="#000180",
                        linewidth=3,
                        linestyle="--",
                        label="Forecast",
                        marker="o",
                        markersize=5,
                    )
                else:
                    self.ax.plot(
                        self.x_dt[len(y_real) : len(y_real) + len(y_pred)],
                        y_pred,
                        color="#000180",
                        linewidth=3,
                        linestyle="--",
                        label="Forecast",
                        marker="o",
                        markersize=5,
                    )
            else:
                # No historical data, just plot predictions
                self.ax.plot(
                    self.x_dt[: len(y_pred)],
                    y_pred,
                    color="#000180",
                    linewidth=3,
                    linestyle="--",
                    label="Forecast",
                    marker="o",
                    markersize=5,
                )

            self.y_total = np.concatenate((y_real, y_pred))
        else:
            self.y_total = y_real

        # Re-add interactive components (cleared by ax.clear())
        self._init_interactive_elements()

        # Formatting
        self.ax.set_title("Energy Demand Projection", fontsize=18, fontname="sans-serif", fontweight="bold")
        self.ax.set_xlabel("Time (UTC)", fontsize=12, fontname="sans-serif")
        self.ax.set_ylabel("Load (MWh)", fontsize=12, fontname="sans-serif")

        # X-Axis Time Formatting
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        self.figure.autofmt_xdate()  # Rotates labels automatically

        self.ax.legend(loc="upper left")
        self.ax.grid(True, linestyle=":", alpha=0.4)

        # Apply limits with 5% padding (Solves 1970 bug & makes edge points hoverable)
        if self.x_dt and len(self.x_dt) > 0:
            time_range = self.x_dt[-1] - self.x_dt[0]
            padding = time_range * 0.05

            if padding.total_seconds() == 0:
                padding = timedelta(hours=1)

            self.ax.set_xlim(self.x_dt[0] - padding, self.x_dt[-1] + padding)

        self.figure.tight_layout()

        # Hide interactive elements before drawing
        self.vline.set_visible(False)
        self.annot.set_visible(False)

        # This draw() automatically triggers on_draw(), neatly capturing our background
        self.canvas.draw()
        self.setCurrentIndex(0)

    def on_hover(self, event):
        """Event handler for mouse hover using high-performance blitting."""
        if not event.inaxes or self.x_dt is None or len(self.x_dt) == 0:
            if hasattr(self, "vline"):
                self.vline.set_visible(False)
                self.annot.set_visible(False)

                # Use blitting to clear the screen instantly when mouse leaves
                if hasattr(self, "bg"):
                    self.canvas.restore_region(self.bg)
                    self.canvas.blit(self.figure.bbox)
                    self.canvas.flush_events()
                else:
                    self.canvas.draw_idle()
            return

        x_mouse = event.xdata

        # Use cached array instead of converting dates every single frame
        idx = np.argmin(np.abs(self.x_nums - x_mouse))

        if idx >= len(self.y_total):
            return

        x = self.x_dt[idx]
        y = self.y_total[idx]

        # Update Vertical Line (Must pass x twice to form the line array)
        self.vline.set_xdata([x, x])
        self.vline.set_visible(True)

        x_num = self.x_nums[idx]
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        if x_num > xlim[0] + (xlim[1] - xlim[0]) / 2:
            x_offset = -15
            ha = "right"
        else:
            x_offset = 15
            ha = "left"

        if y > ylim[0] + (ylim[1] - ylim[0]) / 2:
            y_offset = -15
            va = "top"
        else:
            y_offset = 15
            va = "bottom"

        self.annot.set_position((x_offset, y_offset))
        self.annot.set_horizontalalignment(ha)
        self.annot.set_verticalalignment(va)
        self.annot.xy = (x, y)

        if isinstance(x, (float, np.float64)):  # noqa UP038
            time_str = mdates.num2date(x).strftime("%Y-%m-%d %H:%M")
        elif isinstance(x, datetime.datetime):
            time_str = x.strftime("%Y-%m-%d %H:%M")
        else:
            time_str = str(x)

        text = f" {time_str}\n Load: {y:,.1f} MWh "
        self.annot.set_text(text)
        self.annot.set_visible(True)

        # BLITTING RENDER PIPELINE
        if hasattr(self, "bg"):
            # 1. Restore the clean background
            self.canvas.restore_region(self.bg)

            # 2. Draw only the line and tooltip
            if self.vline.get_visible():
                self.ax.draw_artist(self.vline)
            if self.annot.get_visible():
                self.ax.draw_artist(self.annot)

            # 3. Push to screen instantly
            self.canvas.blit(self.figure.bbox)
            self.canvas.flush_events()
