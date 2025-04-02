# view.py
import time

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QFileDialog, QLabel, QSpinBox, QComboBox, QFormLayout, QGroupBox, QScrollArea,
                             QCheckBox, QDoubleSpinBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from model import CHANNEL_TYPE_ACCELERATION, INPUT_RANGE_10V, INPUT_RANGE_1V, ALARM_TYPE_DISABLED, ALARM_TYPE_LIVE, \
    ALARM_TYPE_LATCHED, CURRENT_SOURCE_10UA, CURRENT_SOURCE_200UA, TEMP_SENSOR_THERMISTOR, TEMP_SENSOR_RTD, \
    RESISTIVE_TEMP_ENABLED, RESISTIVE_TEMP_DISABLED

from model import CHANNEL_TYPE_TEMPERATURE
from model import CHANNEL_TYPE_VOLTAGE

V_INPUT_RANGE_10V = "+/-10V"
V_INPUT_RANGE_1V = "+/-1V"

V_ALARM_TYPE_DISABLED = "Disabled"
V_ALARM_TYPE_LATCHED = "Latched"
V_ALARM_TYPE_LIVE = "Live"

V_CURRENT_SOURCE_10UA = "10μA"
V_CURRENT_SOURCE_200UA = "200μA"

V_TEMP_SENSOR_THERMISTOR = "Thermistor"
V_TEMP_SENSOR_RTD = "Platinum RTD"

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
        if (event.inaxes in [self.ax_voltage, self.ax_acceleration, self.ax_temperature]
                and event.xdata is not None
                and event.guiEvent is not None):  # Check guiEvent exists
            x = event.xdata
            pos = event.guiEvent.globalPos()
            self.hover_signal.emit(x, pos.x(), pos.y())
        else:
            self.hover_signal.emit(0, 0, 0)


class ChannelConfigGroup(QGroupBox):
    # config_changed = pyqtSignal(str)  # Emits channel name when config changes
    selected_channel_changed = pyqtSignal(int)
    alarms_changed = pyqtSignal(int)
    input_range_changed = pyqtSignal(int)
    alarm_type_changed = pyqtSignal(int)
    resistive_temp_mode_changed = pyqtSignal(int)
    current_source_changed = pyqtSignal(int)
    resistive_sensor_type_changed = pyqtSignal(int)


    def __init__(self):
        super().__init__("Channel Configuration")
        self.channel_combo = QComboBox()
        self.alarm_high_spin = QSpinBox()
        self.alarm_low_spin = QSpinBox()
        self.input_range_combo = QComboBox()
        self.alarm_type_combo = QComboBox()
        self.alarm_occurring_led = StatusLED()
        self.resistive_temp_checkbox = QCheckBox("Enable Temperature")
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
        self.input_range_combo.addItems([V_INPUT_RANGE_10V, V_INPUT_RANGE_1V])
        layout.addRow(QLabel("Input Range:"), self.input_range_combo)

        # Alarm State
        self.alarm_type_combo.addItems([V_ALARM_TYPE_DISABLED, V_ALARM_TYPE_LIVE, V_ALARM_TYPE_LATCHED])
        layout.addRow(QLabel("Alarm Type:"), self.alarm_type_combo)
        layout.addRow(QLabel("Alarm Occurring (YES/NO):"), self.alarm_occurring_led)

        # Temperature Conversion
        self.resistive_temp_checkbox.toggled.connect(self._toggle_temp_config)
        self.current_source_combo.addItems([V_CURRENT_SOURCE_10UA, V_CURRENT_SOURCE_200UA])
        self.sensor_type_combo.addItems([V_TEMP_SENSOR_THERMISTOR, V_TEMP_SENSOR_RTD])
        self.current_source_combo.setVisible(False)  # By default not shown
        self.sensor_type_combo.setVisible(False)  # By default not shown
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.current_source_combo)
        temp_layout.addWidget(self.sensor_type_combo)
        layout.addRow(self.resistive_temp_checkbox, temp_layout)

        self.setLayout(layout)

    def _toggle_temp_config(self, checked):
        self.current_source_combo.setVisible(checked)
        self.sensor_type_combo.setVisible(checked)

    def _connect_internal_signals(self):
        """Connect all UI changes to emit config_changed."""
        self.channel_combo.currentTextChanged.connect(self._emit_selected_channel_changed)
        self.alarm_high_spin.valueChanged.connect(self._emit_alarms_changed)
        self.alarm_low_spin.valueChanged.connect(self._emit_alarms_changed)
        self.input_range_combo.currentTextChanged.connect(self._emit_input_range_changed)
        self.alarm_type_combo.currentTextChanged.connect(self._emit_alarm_type_changed)
        self.resistive_temp_checkbox.toggled.connect(self._emit_resistive_temp_mode_changed)
        self.current_source_combo.currentTextChanged.connect(self._emit_current_source_changed)
        self.sensor_type_combo.currentTextChanged.connect(self._emit_resistive_temp_sensor_changed)

    def _emit_alarm_type_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.alarm_type_changed.emit(channel)

    def _emit_alarms_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.alarms_changed.emit(channel)

    def _emit_input_range_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.input_range_changed.emit(channel)

    def _emit_selected_channel_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.selected_channel_changed.emit(channel)

    def _emit_resistive_temp_mode_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.resistive_temp_mode_changed.emit(channel)

    def _emit_current_source_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.current_source_changed.emit(channel)

    def _emit_resistive_temp_sensor_changed(self):
        channel = int(self.get_selected_channel())
        if channel:
            self.resistive_sensor_type_changed.emit(channel)

    def get_selected_channel(self) -> str:
        """Get the currently selected channel name."""
        return self.channel_combo.currentText()

    def get_alarm_high(self) -> int:
        """Get the current alarm high value."""
        return self.alarm_high_spin.value()

    def get_alarm_low(self) -> int:
        """Get the current alarm low value."""
        return self.alarm_low_spin.value()

    def get_input_range(self) -> int|None:
        """Get the selected input range."""
        input_range = self.input_range_combo.currentText()
        if input_range == V_INPUT_RANGE_10V:
            return INPUT_RANGE_10V
        elif input_range == V_INPUT_RANGE_1V:
            return INPUT_RANGE_1V

    def get_resistive_temp_mode(self) -> int|None:
        """Check if temperature conversion is enabled."""
        if self.resistive_temp_checkbox.isChecked():
            return RESISTIVE_TEMP_ENABLED
        else:
            return RESISTIVE_TEMP_DISABLED

    def get_current_source(self) -> int|None:
        """Get the selected current source."""
        cs = self.current_source_combo.currentText()
        if cs == V_CURRENT_SOURCE_200UA:
            return CURRENT_SOURCE_200UA
        elif cs == V_CURRENT_SOURCE_10UA:
            return CURRENT_SOURCE_10UA

    def get_resistive_sensor_type(self) -> int|None:
        """Get the selected sensor type."""
        sensor = self.sensor_type_combo.currentText()
        if sensor == V_TEMP_SENSOR_THERMISTOR:
            return TEMP_SENSOR_THERMISTOR
        elif sensor == V_TEMP_SENSOR_RTD:
            return TEMP_SENSOR_RTD

    def get_alarm_type(self) -> int|None:
        """Get the selected alarm type."""
        alarm_type = self.alarm_type_combo.currentText()
        if alarm_type == V_ALARM_TYPE_DISABLED:
            return ALARM_TYPE_DISABLED
        elif alarm_type == V_ALARM_TYPE_LATCHED:
            return ALARM_TYPE_LATCHED
        elif alarm_type == V_ALARM_TYPE_LIVE:
            return ALARM_TYPE_LIVE

    def set_channel_drop_down_item(self, channel):
        """ Add a single string to the ch drop down list """
        self.channel_combo.addItem(channel)

    def set_alarm_occurring(self, status: bool):
        self.alarm_occurring_led.set_status(status)

class MainWindowView(QMainWindow):
    load_replay = pyqtSignal(str)
    max_points = pyqtSignal(int)
    channel_visibility_change = pyqtSignal(object)
    axis_range_changed = pyqtSignal(float, float)
    sync_rtc = pyqtSignal()
    toggle_recording = pyqtSignal(bool)
    clear_data = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Acquisition System")
        self.setGeometry(100, 100, 1200, 800)
        # Default Y axis controls
        self._ymin = 0
        self._ymax = 10

        self._init_ui()

        self._is_recording = False


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

        # Replay group
        self._create_replay_controls()

        # Visibility group
        self._create_visibility_controls()

        # Display Settings group
        self._create_display_settings()

        # Device status group
        self._create_device_status_panel()

        # Clear data button
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

    def _create_device_status_panel(self):
        """Creates a device status group with hardcoded Optical Link and Recording indicators."""
        status_group = QGroupBox("Device Status")
        status_layout = QFormLayout()

        # Optical Link Status
        self.optical_status = QLabel("Disconnected")  # Default to disconnected
        self.optical_status.setStyleSheet("color: red;")
        status_layout.addRow("Optical Link:", self.optical_status)

        # Recording Status and Button
        recording_layout = QHBoxLayout()
        self.recording_status = QLabel("Not Recording")  # Default to not recording
        self.recording_status.setStyleSheet("color: red;")
        recording_layout.addWidget(self.recording_status)

        self.toggle_recording_btn = QPushButton("Start Recording")
        self.toggle_recording_btn.clicked.connect(lambda: self.toggle_recording.emit(True))
        recording_layout.addWidget(self.toggle_recording_btn)
        status_layout.addRow("Recording:", recording_layout)

        # RTC Status and Button
        rtc_layout = QHBoxLayout()
        self.rtc_status = QLabel("Not Synced")
        self.rtc_status.setStyleSheet("color: red;")
        rtc_layout.addWidget(self.rtc_status)

        # System Time Display
        self.system_time_label = QLabel(time.strftime('%H:%M:%S'))
        rtc_layout.addWidget(self.system_time_label)

        sync_rtc_btn = QPushButton("Sync RTC")
        sync_rtc_btn.clicked.connect(self.sync_rtc.emit)
        rtc_layout.addWidget(sync_rtc_btn)
        status_layout.addRow("RTC:", rtc_layout)

        status_group.setLayout(status_layout)
        self.control_layout.addWidget(status_group)


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

    def edit_graph_canvas_view(self):
        return self.graph_canvas

    def edit_channel_config_view(self):
        return self.config_group

    def clear_graph(self):
        self.graph_canvas.clear_plot()

    def toggle_recording_status(self):
        self._is_recording = not self._is_recording
        if self._is_recording:
            self.recording_status.setText("Recording")
            self.recording_status.setStyleSheet("color: green;")
            self.toggle_recording_btn.setText("Stop Recording")
        else:
            self.recording_status.setText("Not Recording")
            self.recording_status.setStyleSheet("color: red;")
            self.toggle_recording_btn.setText("Start Recording")

    def set_rtc_time(self):
        self.rtc_status.setText("Synced")
        self.rtc_status.setStyleSheet("color: green;")

    # def update_rtc_time(self):
    #
