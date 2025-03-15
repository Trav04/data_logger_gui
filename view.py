# view.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QLabel, QSpinBox, QComboBox, QFormLayout, QGroupBox, QScrollArea,
                             QCheckBox, QDoubleSpinBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StatusLED(QLabel):
    def __init__(self):
        super().__init__()
        self.setFixedSize(20, 20)
        self.set_status(False)

    def set_status(self, active):
        color = QColor(0, 255, 0) if active else QColor(255, 0, 0)
        self.setStyleSheet(f"background-color: {color.name()}; border-radius: 10px;")

class GraphCanvas(FigureCanvas):
    hover_signal = pyqtSignal(float, int, int)  # xdata, global_x, global_y

    def __init__(self):
        self.fig = Figure(figsize=(10, 6))
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.lines = {}
        self.mpl_connect('motion_notify_event', self.on_hover)

    def update_plot(self, x_data, y_data, channels, x_label, y_labels):
        """
         Updates the plot with new data.

         Params:
             x_data (list or array): X-axis values.
             y_data (dict): Dictionary mapping channel names to Y-axis values.
             channels (list): List of channel names to plot.
             x_label (str): Label for the X-axis.
             y_labels (dict): Dictionary mapping channel names to Y-axis labels.
         """
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
        if event.inaxes:
            x = event.xdata
            pos = event.guiEvent.globalPos()
            self.hover_signal.emit(x, pos.x(), pos.y())
        else:
            self.hover_signal.emit(0, 0, 0)


class MainWindowView(QMainWindow):
    load_replay = pyqtSignal(str)
    max_points_changed = pyqtSignal(int)
    channel_visibility_change = pyqtSignal(list)
    axis_range_changed = pyqtSignal(float, float)
    sync_rtc = pyqtSignal()
    toggle_recording = pyqtSignal(bool)
    clear_data = pyqtSignal()
    toggle_pc_recording = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Acquisition System")
        self.setGeometry(100, 100, 1200, 800)
        self._init_ui()
        self._active_types = []

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Plot Area
        self.graph_canvas = GraphCanvas()
        main_layout.addWidget(self.graph_canvas, 75)

        # Control Panel
        control_panel = QScrollArea()
        control_widget = QWidget()
        self.control_layout = QVBoxLayout(control_widget)
        control_panel.setWidget(control_widget)
        control_panel.setWidgetResizable(True)
        main_layout.addWidget(control_panel, 25)

        self._create_replay_controls()
        # self._create_display_settings()
        self._create_visibility_controls()
        # self._create_device_config()
        # self._create_axis_config()
        # self._create_recording_controls()
        # self._create_alarm_config()
        # self._create_optical_link()
        # self._create_clear_button()

        # Tooltip Label
        self.tooltip_label = QLabel()
        self.tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.tooltip_label.setStyleSheet("background-color: #ffffe0; border: 1px solid black; padding: 2px;")
        self.tooltip_label.hide()

        self.status_bar = self.statusBar()

    def _create_replay_controls(self):
        group = QGroupBox("Replay")
        btn = QPushButton("Load Replay File")
        btn.clicked.connect(self._on_load_replay)
        group.setLayout(QVBoxLayout())
        group.layout().addWidget(btn)
        self.control_layout.addWidget(group)

    def _create_visibility_controls(self):
        visibility_group = QGroupBox("Channel Visibility")
        visibility_layout = QVBoxLayout()

        self.voltage_check = QCheckBox("Voltage")
        self.voltage_check.setChecked(True)
        visibility_layout.addWidget(self.voltage_check)

        self.accel_check = QCheckBox("Acceleration")
        self.accel_check.setChecked(True)
        visibility_layout.addWidget(self.accel_check)

        self.temp_check = QCheckBox("Temperature")
        self.temp_check.setChecked(True)
        visibility_layout.addWidget(self.temp_check)

        visibility_group.setLayout(visibility_layout)
        self.control_layout.addWidget(visibility_group)

        self.voltage_check.stateChanged.connect(self._update_active_channels)
        self.accel_check.stateChanged.connect(self._update_active_channels)
        self.temp_check.stateChanged.connect(self._update_active_channels)

    def _update_active_channels(self):
        """Emit visibility_changed signal with current active types."""
        self._active_types = []
        if self.voltage_check.isChecked():
            self._active_types.append('voltage')
        if self.accel_check.isChecked():
            self._active_types.append('acceleration')
        if self.temp_check.isChecked():
            self._active_types.append('temperature')

        # Invoke a signal to alert the controller
        self.channel_visibility_change.emit(self._active_types)

    def get_active_types(self):
        return self._active_types

    def _on_load_replay(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if filename:
            self.load_replay.emit(filename)
