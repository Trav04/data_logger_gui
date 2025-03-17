# view.py
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QLabel, QSpinBox, QComboBox, QFormLayout, QGroupBox, QScrollArea,
                             QCheckBox, QDoubleSpinBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from model import CHANNEL_TYPE_ACCELERATION
from model import CHANNEL_TYPE_TEMPERATURE
from model import CHANNEL_TYPE_VOLTAGE

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
        self.fig = Figure(figsize=(10, 8))
        super().__init__(self.fig)
        # Create three vertically stacked subplots
        self.ax_voltage = self.fig.add_subplot(3, 1, 1)
        self.ax_acceleration = self.fig.add_subplot(3, 1, 2, sharex=self.ax_voltage)
        self.ax_temperature = self.fig.add_subplot(3, 1, 3, sharex=self.ax_voltage)
        self.lines = {}  # Track lines for each channel
        self.mpl_connect('motion_notify_event', self.on_hover)

        self._y_min = 0
        self._y_max = 10

        self._active_channels = [CHANNEL_TYPE_VOLTAGE, CHANNEL_TYPE_TEMPERATURE, CHANNEL_TYPE_ACCELERATION]

    def update_plot(self, x_data, y_data, voltage_channels, acceleration_channels, temperature_channels, x_label, y_labels, y_min, y_max):
        """Update plots with data on respective subplots."""
        # Clear previous plots
        self.ax_voltage.clear()
        self.ax_acceleration.clear()
        self.ax_temperature.clear()

        # Plot Voltage channels
        if CHANNEL_TYPE_VOLTAGE in self._active_channels:
            for ch in voltage_channels:
                if ch in y_data:
                    line, = self.ax_voltage.plot(x_data, y_data[ch], marker='x', linestyle='-', label=f"{ch} ({y_labels[ch]})")
                    self.lines[ch] = line
            self.ax_voltage.legend()
            self.ax_voltage.grid(True)
            self.ax_voltage.set_ylabel('Voltage V')
            self.ax_voltage.set_ylim(y_min, y_max)

        # Plot Acceleration channels
        if CHANNEL_TYPE_ACCELERATION in self._active_channels:
            for ch in acceleration_channels:
                if ch in y_data:
                    line, = self.ax_acceleration.plot(x_data, y_data[ch], marker='x', linestyle='-', label=f"{ch} ({y_labels[ch]})")
                    self.lines[ch] = line
            self.ax_acceleration.legend()
            self.ax_acceleration.grid(True)
            self.ax_acceleration.set_ylabel('Acceleration m/s^2')
            self.ax_acceleration.set_ylim(y_min, y_max)

        # Plot Temperature channels
        if CHANNEL_TYPE_TEMPERATURE in self._active_channels:
            for ch in temperature_channels:
                if ch in y_data:
                    line, = self.ax_temperature.plot(x_data, y_data[ch], marker='x', linestyle='-', label=f"{ch} ({y_labels[ch]})")
                    self.lines[ch] = line
            self.ax_temperature.legend()
            self.ax_temperature.grid(True)
            self.ax_temperature.set_ylabel('Temperature C')
            self.ax_temperature.set_xlabel(x_label)
            self.ax_temperature.set_ylim(y_min, y_max)

        self.fig.tight_layout()
        self.draw()

    def set_y_lim(self, y_min, y_max):
        """
        Set synchronized Y-axis limits for all subplots
        Params:
            y_min (float): Minimum Y-axis value
            y_max (float): Maximum Y-axis value
        """
        self._y_min = y_min
        self._y_max = y_max
        self.ax_voltage.set_ylim(y_min, y_max)
        self.ax_acceleration.set_ylim(y_min, y_max)
        self.ax_temperature.set_ylim(y_min, y_max)
        self.draw()

    def get_y_axis(self):
        return self._y_min, self._y_max

    def clear_plot(self):
        """Clear all subplots."""
        self.ax_voltage.clear()
        self.ax_acceleration.clear()
        self.ax_temperature.clear()
        self.draw()

    def set_active_channels(self, active_channels):
        self._active_channels = active_channels

    def on_hover(self, event):
        """Handle hover events across all subplots."""
        if event.inaxes in [self.ax_voltage, self.ax_acceleration, self.ax_temperature]:
            x = event.xdata
            pos = event.guiEvent.globalPos()
            self.hover_signal.emit(x, pos.x(), pos.y())
        else:
            self.hover_signal.emit(0, 0, 0)


class ChannelConfigGroup(QGroupBox):
    config_changed = pyqtSignal(str)  # Emits channel name when config changes

    def __init__(self):
        super().__init__("Channel Configuration")
        self.channel_combo = QComboBox()
        self.alarm_high_spin = QSpinBox()
        self.alarm_low_spin = QSpinBox()
        self.input_range_combo = QComboBox()
        self.alarm_type_combo = QComboBox()
        self.alarm_state_led = StatusLED()
        self.temp_enable_check = QCheckBox("Enable Temperature")
        self.current_source_combo = QComboBox()
        self.sensor_type_combo = QComboBox()

        self._setup_ui()
        self._connect_internal_signals()

    def _setup_ui(self):
        layout = QFormLayout()

        # Channel Selection
        layout.addRow(QLabel("Channel:"), self.channel_combo)

        # Alarm Settings
        self.alarm_high_spin.setRange(-10000, 10000)
        self.alarm_low_spin.setRange(-10000, 10000)
        layout.addRow(QLabel("Alarm High:"), self.alarm_high_spin)
        layout.addRow(QLabel("Alarm Low:"), self.alarm_low_spin)

        # Input Range
        self.input_range_combo.addItems(['+/-10V', '+/-1V'])
        layout.addRow(QLabel("Input Range:"), self.input_range_combo)

        # Alarm State
        self.alarm_type_combo.addItems(['Disabled', 'Latched', 'Live'])
        self.alarm_type_combo.setEnabled(False)
        layout.addRow(QLabel("Alarm Type:"), self.alarm_type_combo)
        layout.addRow(QLabel("Alarm State (ON / OFF):"), self.alarm_state_led)

        # Temperature Conversion
        self.temp_enable_check.toggled.connect(self._toggle_temp_config)
        self.current_source_combo.addItems(['10μA', '200μA'])
        self.sensor_type_combo.addItems(['Thermistor', 'Platinum RTD'])
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.current_source_combo)
        temp_layout.addWidget(self.sensor_type_combo)
        layout.addRow(self.temp_enable_check, temp_layout)

        self.setLayout(layout)

    def _toggle_temp_config(self, checked):
        self.current_source_combo.setVisible(checked)
        self.sensor_type_combo.setVisible(checked)

    def _connect_internal_signals(self):
        """Connect all UI changes to emit config_changed."""
        self.alarm_high_spin.valueChanged.connect(self._emit_config_changed)
        self.alarm_low_spin.valueChanged.connect(self._emit_config_changed)
        self.input_range_combo.currentTextChanged.connect(self._emit_config_changed)
        self.temp_enable_check.toggled.connect(self._emit_config_changed)
        self.current_source_combo.currentTextChanged.connect(self._emit_config_changed)
        self.sensor_type_combo.currentTextChanged.connect(self._emit_config_changed)

    def _emit_config_changed(self):
        """Emit signal with the currently selected channel."""
        channel = self.get_selected_channel()
        if channel:
            self.config_changed.emit(channel)

    def update_ui_from_config(self, config):
        """Update UI elements from a configuration dictionary."""
        # Block signals temporarily to prevent feedback loops
        self.alarm_high_spin.blockSignals(True)
        self.alarm_low_spin.blockSignals(True)
        self.input_range_combo.blockSignals(True)
        self.temp_enable_check.blockSignals(True)
        self.current_source_combo.blockSignals(True)
        self.sensor_type_combo.blockSignals(True)

        try:
            # Update values
            self.alarm_high_spin.setValue(config['alarm_high'])
            self.alarm_low_spin.setValue(config['alarm_low'])
            self.input_range_combo.setCurrentText(config['input_range'])
            self.temp_enable_check.setChecked(config['resistive_temp_enabled'])
            self.current_source_combo.setCurrentText(config['current_source'])
            self.sensor_type_combo.setCurrentText(config['sensor_type'])
        finally:
            # Always unblock signals even if errors occur
            self.alarm_high_spin.blockSignals(False)
            self.alarm_low_spin.blockSignals(False)
            self.input_range_combo.blockSignals(False)
            self.temp_enable_check.blockSignals(False)
            self.current_source_combo.blockSignals(False)
            self.sensor_type_combo.blockSignals(False)

    def get_selected_channel(self) -> str:
        """Get the currently selected channel name."""
        return self.channel_combo.currentText()

    def get_alarm_high(self) -> int:
        """Get the current alarm high value."""
        return self.alarm_high_spin.value()

    def get_alarm_low(self) -> int:
        """Get the current alarm low value."""
        return self.alarm_low_spin.value()

    def get_input_range(self) -> str:
        """Get the selected input range."""
        return self.input_range_combo.currentText()

    def get_temp_enabled(self) -> bool:
        """Check if temperature conversion is enabled."""
        return self.temp_enable_check.isChecked()

    def get_current_source(self) -> str:
        """Get the selected current source."""
        return self.current_source_combo.currentText()

    def get_sensor_type(self) -> str:
        """Get the selected sensor type."""
        return self.sensor_type_combo.currentText()

class MainWindowView(QMainWindow):
    load_replay = pyqtSignal(str)
    max_points = pyqtSignal(int)
    channel_visibility_change = pyqtSignal(object)
    axis_range_changed = pyqtSignal(float, float)
    sync_rtc = pyqtSignal()
    toggle_recording = pyqtSignal(bool)
    clear_data = pyqtSignal()
    toggle_pc_recording = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Acquisition System")
        self.setGeometry(100, 100, 1200, 800)
        # Default Y axis controls
        self._ymin = 0
        self._ymax = 10

        self._init_ui()


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

        # Add Channel Configuration Group
        self.config_group = ChannelConfigGroup()
        self.control_layout.addWidget(self.config_group)

        self._create_replay_controls()
        self._create_visibility_controls()
        self._create_display_settings()
        # self._create_device_config()
        # self._create_recording_controls()
        # self._create_alarm_config()
        # self._create_optical_link()
        self._create_clear_button()

        # Tooltip Label
        self.tooltip_label = QLabel()
        self.tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.tooltip_label.setStyleSheet("background-color: #ffffe0; border: 1px solid black; padding: 2px;")
        self.tooltip_label.hide()

        self.status_bar = self.statusBar()

    from PyQt5.QtWidgets import QFrame  # Add this import

    def _create_display_settings(self):
        """Add controls for display settings like Y-axis range and max points."""
        display_group = QGroupBox("Display Settings")
        layout = QFormLayout()

        # Y-Axis Min and Max SpinBoxes
        self.ymin_spin = QDoubleSpinBox()
        self.ymin_spin.setRange(-1000, 1000)  # Adjust range as needed
        self.ymin_spin.setValue(self._ymin)  # Default min value
        self.ymin_spin.setSingleStep(1)  # Increment/decrement by 1
        layout.addRow("Y-Axis Min:", self.ymin_spin)

        self.ymax_spin = QDoubleSpinBox()
        self.ymax_spin.setRange(-1000, 1000)  # Adjust range as needed
        self.ymax_spin.setValue(self._ymax)  # Default max value
        self.ymax_spin.setSingleStep(1)  # Increment/decrement by 1
        layout.addRow("Y-Axis Max:", self.ymax_spin)

        # Add a horizontal separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)  # Horizontal line
        separator.setFrameShadow(QFrame.Sunken)  # Sunken style
        layout.addRow(separator)  # Add separator to the layout

        # Max Points SpinBox
        self.max_points_spin = QSpinBox()
        self.max_points_spin.setRange(10, 10000)
        self.max_points_spin.setValue(1000)  # Default value
        self.max_points_spin.setKeyboardTracking(True)  # Ensure real-time updates
        layout.addRow("Max Points:", self.max_points_spin)

        # Connect signals
        self.ymin_spin.valueChanged.connect(self._emit_axis_range_changed)
        self.ymax_spin.valueChanged.connect(self._emit_axis_range_changed)
        self.max_points_spin.valueChanged.connect(self._emit_max_points_changed)

        display_group.setLayout(layout)
        self.control_layout.addWidget(display_group)

    def _emit_max_points_changed(self):
        """Emit signal when max points changes."""
        self.max_points.emit(self.max_points_spin.value())

    def _emit_axis_range_changed(self):
        """Emit signal with updated Y-axis range."""
        self._ymin = self.ymin_spin.value()
        self._ymax = self.ymax_spin.value()
        self.axis_range_changed.emit(self._ymin, self._ymax)

    def _create_clear_button(self):
        """Add a button to clear all data."""
        clear_btn = QPushButton("Clear All Data")
        clear_btn.clicked.connect(self.clear_data.emit)  # Connect to the clear_data signal
        self.control_layout.addWidget(clear_btn)

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
        active_channels = []  # Reset active channels
        if self.voltage_check.isChecked():
           active_channels.append(CHANNEL_TYPE_VOLTAGE)
        if self.accel_check.isChecked():
            active_channels.append(CHANNEL_TYPE_ACCELERATION)
        if self.temp_check.isChecked():
            active_channels.append(CHANNEL_TYPE_TEMPERATURE)

        self.graph_canvas.set_active_channels(active_channels)  # Redefine the active channels

        # Invoke a signal to alert the controller
        self.channel_visibility_change.emit(None)

    def _on_load_replay(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if filename:
            self.load_replay.emit(filename)

    def get_y_axis(self):
        return self._ymin, self._ymax

    def get_graph_canvas(self):
        return self.graph_canvas

    def clear_graph(self):
        self.graph_canvas.clear_plot()
