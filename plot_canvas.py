import sys
import csv
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QLabel, QSpinBox, QComboBox, QFormLayout, QGroupBox, QScrollArea,
                             QCheckBox, QDoubleSpinBox, QSizePolicy, QLineEdit)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QTime, QDate
from PyQt5.QtGui import QColor, QPalette
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import numpy as np

class PlotCanvas(FigureCanvas):
    hover_signal = pyqtSignal(str, int, int)  # Text, x, y (global pos)

    def __init__(self, parent=None, hover_callback=None):
        self.fig = Figure(figsize=(10, 6))
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.lines = {}
        self.hover_callback = hover_callback
        self.setParent(parent)
        self.mpl_connect('motion_notify_event', self.on_hover)

    def update_plot(self, x_data, y_data, channels, x_label, y_labels):
        self.axes.clear()
        for ch in channels:
            if ch in y_data:
                line, = self.axes.plot(x_data, y_data[ch], marker='x', linestyle='-', label=f"{ch} ({y_labels[ch]})")
                self.lines[ch] = line
        self.axes.set_xlabel(x_label)
        self.axes.legend()
        self.axes.grid(True)
        self.draw()

    def on_hover(self, event):
        if not event.inaxes or not self.hover_callback:
            self.hover_signal.emit('', 0, 0)
            return
        text = self.hover_callback(event.xdata)
        pos = event.guiEvent.globalPos()
        self.hover_signal.emit(text, pos.x(), pos.y())