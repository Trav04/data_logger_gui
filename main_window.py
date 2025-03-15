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

from replay_manager import *
from widgets import *
from plot_canvas import *

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Acquisition System")
        self.setGeometry(100, 100, 1200, 800)
        self.replay_manager = ReplayManager()
        self.max_points = 1000

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Plot Area
        self.plot_canvas = PlotCanvas(hover_callback=self.get_hover_text)
        main_layout.addWidget(self.plot_canvas, 75)

        # Tooltip Label
        self.tooltip_label = QLabel()
        self.tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.tooltip_label.setStyleSheet("background-color: #ffffe0; border: 1px solid black; padding: 2px;")
        self.tooltip_label.hide()

        # Control Panel
        control_panel = QScrollArea()
        control_widget = QWidget()
        self.control_layout = QVBoxLayout(control_widget)
        control_panel.setWidget(control_widget)
        control_panel.setWidgetResizable(True)
        main_layout.addWidget(control_panel, 25)

        # Replay Controls
        replay_group = QGroupBox("Replay")
        self.replay_btn = QPushButton("Load Replay File")
        self.replay_btn.clicked.connect(self.load_replay_file)
        replay_group.setLayout(QVBoxLayout())
        replay_group.layout().addWidget(self.replay_btn)
        self.control_layout.addWidget(replay_group)

        # Max Points Control
        max_points_group = QGroupBox("Display Settings")
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(10, 10000)
        self.max_points_spin.setValue(1000)
        self.max_points_spin.valueChanged.connect(self.update_max_points)
        max_points_group.setLayout(QFormLayout())
        max_points_group.layout().addRow("Max Points:", self.max_points_spin)
        self.control_layout.addWidget(max_points_group)

        self.status_bar = self.statusBar()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(100)

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

        # Connect checkboxes to plot updates
        self.voltage_check.stateChanged.connect(self.update_plots)
        self.accel_check.stateChanged.connect(self.update_plots)
        self.temp_check.stateChanged.connect(self.update_plots)

        # Connect hover signal
        self.plot_canvas.hover_signal.connect(self.handle_hover)

        self.create_device_config_ui()
        self.create_axis_config_ui()
        self.create_recording_ui()
        self.create_alarm_config_ui()
        self.create_optical_link_ui()
        self.create_clear_button()

    def handle_hover(self, text, x, y):
        if text:
            self.tooltip_label.setText(text)
            self.tooltip_label.adjustSize()
            self.tooltip_label.move(x + 15, y + 15)
            self.tooltip_label.show()
        else:
            self.tooltip_label.hide()

    def load_replay_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if filename:
            success = self.replay_manager.load_csv(filename, self.max_points)
            message = f"Loaded: {filename}" if success else "Invalid file format"
            self.status_bar.showMessage(message, 5000)
            self.update_plots()

    def update_max_points(self, value):
        self.max_points = value

    def update_plots(self):
        if self.replay_manager.data:
            x_data = self.replay_manager.relative_times
            y_data = self.replay_manager.data
            y_labels = {ch: info['unit'] for ch, info in self.replay_manager.channel_info.items()}

            active_types = []
            if self.voltage_check.isChecked():
                active_types.append('voltage')
            if self.accel_check.isChecked():
                active_types.append('acceleration')
            if self.temp_check.isChecked():
                active_types.append('temperature')

            channels_to_plot = [
                ch for ch in y_data.keys()
                if self.replay_manager.channel_info.get(ch, {}).get('type') in active_types
            ]

            self.plot_canvas.update_plot(x_data, y_data, channels_to_plot, "Time (s)", y_labels)

    def get_hover_text(self, x):
        if not self.replay_manager.data or not x:
            return ''
        closest_idx = np.argmin(np.abs(np.array(self.replay_manager.relative_times) - x))
        text = f"Time: {self.replay_manager.relative_times[closest_idx]:.3f}s\n"
        for ch, values in self.replay_manager.data.items():
            text += f"{ch}: {values[closest_idx]:.2f} {self.replay_manager.channel_info[ch]['unit']}\n"
        return text

    def create_device_config_ui(self):
        device_group = QGroupBox("Device Configuration")
        layout = QFormLayout()

        # RTC Time
        self.rtc_label = QLabel()
        self.sync_rtc_btn = QPushButton("Sync RTC to System")
        self.sync_rtc_btn.clicked.connect(self.sync_rtc_time)
        layout.addRow(QLabel("RTC Time:"), self.rtc_label)
        layout.addRow(self.sync_rtc_btn)

        # Recording State
        self.recording_btn = QPushButton("Start Device Recording")
        self.recording_btn.setCheckable(True)
        self.recording_btn.clicked.connect(self.toggle_recording)
        layout.addRow(QLabel("Recording:"), self.recording_btn)

        device_group.setLayout(layout)
        self.control_layout.insertWidget(0, device_group)

    def create_axis_config_ui(self):
        axis_group = QGroupBox("Y-Axis Range")
        layout = QHBoxLayout()

        self.ymin_spin = QDoubleSpinBox()
        self.ymax_spin = QDoubleSpinBox()
        self.ymin_spin.setRange(-1000, 1000)
        self.ymax_spin.setRange(-1000, 1000)
        self.ymin_spin.valueChanged.connect(self.update_axis_range)
        self.ymax_spin.valueChanged.connect(self.update_axis_range)

        layout.addWidget(QLabel("Min:"))
        layout.addWidget(self.ymin_spin)
        layout.addWidget(QLabel("Max:"))
        layout.addWidget(self.ymax_spin)
        axis_group.setLayout(layout)
        self.control_layout.addWidget(axis_group)

    def create_recording_ui(self):
        self.record_btn = QPushButton("Start PC Recording")
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self.toggle_pc_recording)
        self.control_layout.addWidget(self.record_btn)

    def create_alarm_config_ui(self):
        self.alarm_group = QGroupBox("Alarm Settings")
        self.alarm_scroll = QScrollArea()
        self.alarm_widget = QWidget()
        self.alarm_layout = QFormLayout(self.alarm_widget)
        self.alarm_scroll.setWidget(self.alarm_widget)
        self.alarm_scroll.setWidgetResizable(True)
        self.alarm_group.setLayout(QVBoxLayout())
        self.alarm_group.layout().addWidget(self.alarm_scroll)
        self.control_layout.addWidget(self.alarm_group)

    def create_optical_link_ui(self):
        link_group = QGroupBox("Optical Link")
        layout = QHBoxLayout()
        self.link_status = StatusLED()
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.link_status)
        link_group.setLayout(layout)
        self.control_layout.addWidget(link_group)

    def create_clear_button(self):
        clear_btn = QPushButton("Clear All Data")
        clear_btn.clicked.connect(self.clear_data)
        self.control_layout.addWidget(clear_btn)

    def update_channel_config_ui(self):
        # Clear existing alarm config UI
        while self.alarm_layout.count():
            item = self.alarm_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Create new config elements for each channel
        for channel in self.replay_manager.channel_info:
            info = self.replay_manager.channel_info[channel]

            # Alarm thresholds
            high_spin = QDoubleSpinBox()
            low_spin = QDoubleSpinBox()
            type_combo = QComboBox()
            state_label = QLabel("Normal")

            # Input range for voltage channels
            if info['type'] == 'voltage':
                range_combo = QComboBox()
                range_combo.addItems(["+/-10V", "+/-1V"])
                self.replay_manager.input_ranges[channel] = "+/-10V"
                range_combo.currentTextChanged.connect(
                    lambda val, c=channel: self.update_input_range(c, val)
                )

            # Temperature config
            if info['type'] == 'temperature':
                temp_combo = QComboBox()
                temp_combo.addItems(["PT100", "PT500", "PT1000"])
                self.replay_manager.temp_configs[channel] = "PT100"
                temp_combo.currentTextChanged.connect(
                    lambda val, c=channel: self.update_temp_config(c, val)
                )

            # Add to layout
            self.alarm_layout.addRow(QLabel(f"{channel} Thresholds:"))
            self.alarm_layout.addRow(QLabel("High:"), high_spin)
            self.alarm_layout.addRow(QLabel("Low:"), low_spin)
            self.alarm_layout.addRow(QLabel("Type:"), type_combo)
            self.alarm_layout.addRow(QLabel("State:"), state_label)

            if info['type'] == 'voltage':
                self.alarm_layout.addRow(QLabel("Input Range:"), range_combo)
            elif info['type'] == 'temperature':
                self.alarm_layout.addRow(QLabel("RTD Type:"), temp_combo)

    def sync_rtc_time(self):
        self.replay_manager.rtc_time = datetime.now()
        self.rtc_label.setText(self.replay_manager.rtc_time.strftime("%Y-%m-%d %H:%M:%S"))

    def toggle_recording(self, checked):
        self.replay_manager.recording = checked
        self.recording_btn.setText("Stop Recording" if checked else "Start Recording")

    def update_axis_range(self):
        self.plot_canvas.axes.set_ylim(self.ymin_spin.value(), self.ymax_spin.value())
        self.plot_canvas.draw()

    def clear_data(self):
        self.replay_manager.data.clear()
        self.replay_manager.relative_times = []
        self.plot_canvas.axes.clear()
        self.plot_canvas.draw()

    def toggle_pc_recording(self, checked):
        if checked:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Recording", "", "CSV Files (*.csv)")
            if filename:
                # Implement actual recording logic
                pass
        self.record_btn.setText("Stop Recording" if checked else "Start PC Recording")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())