# controller.py
import threading
import time
from time import sleep

from PyQt5.QtCore import QTimer
import numpy as np
from datetime import datetime

from model import CHANNEL_TYPE_VOLTAGE, INPUT_RANGE, INPUT_RANGE_10V, INPUT_RANGE_1V, ALARM_TYPE, ALARM_STATE, \
    TEMP_ENABLED, CURRENT_SOURCE, SENSOR_TYPE, TEMP_SENSOR_DISABLED, CURRENT_SOURCE_DISABLED, ALARM_TYPE_LIVE, \
    ALARM_TYPE_LATCHED, ALARM_TYPE_DISABLED, ALARM_OCCURRING, ALARM_NOT_OCCURRING, RESISTIVE_TEMP_ENABLED
from model import CHANNEL_TYPE_TEMPERATURE
from model import CHANNEL_TYPE_ACCELERATION

from model import CHANNEL_TYPE
from model import CHANNEL_TYPE_MAP

from model import ALARM_HIGH
from model import ALARM_LOW
from serial_send_receive_manager import SerialSendReceiveManager

FAKE_DATA = [
    ("2025-03-08_12-30-15-123", [3.45, 2.78, 25.6, 4.12, 0.12, -0.05, 0.08, 26.0]),
    ("2025-03-08_12-30-16-456", [3.43, 2.81, 25.4, 4.18, 0.20, -0.03, 0.15, 26.2]),
    ("2025-03-08_12-30-17-789", [3.47, 2.76, 25.7, 4.10, 0.09, -0.07, 0.05, 25.8]),
    ("2025-03-08_12-30-19-012", [3.52, 2.79, 26.3, 4.20, 0.11, -0.12, 0.18, 26.6]),
    ("2025-03-08_12-30-20-345", [3.39, 2.75, 25.1, 4.00, 0.05, 0.02, 0.01, 25.4]),
    ("2025-03-08_12-30-21-678", [3.46, 2.84, 26.5, 4.19, 0.23, -0.06, 0.19, 26.9]),
    ("2025-03-08_12-30-23-001", [3.37, 2.72, 25.0, 4.03, 0.04, -0.01, 0.00, 25.3]),
    ("2025-03-08_12-30-24-334", [3.55, 2.85, 26.7, 4.22, 0.25, -0.14, 0.22, 27.0]),
    ("2025-03-08_12-30-25-667", [3.36, 2.70, 24.9, 3.99, 0.03, 0.01, -0.01, 25.2]),
    ("2025-03-08_12-30-27-000", [3.58, 2.87, 26.9, 4.25, 0.28, -0.16, 0.25, 27.2]),
    ("2025-03-08_12-30-28-333", [3.34, 2.69, 24.8, 3.97, 0.02, 0.03, -0.02, 25.0])
]


class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.current_max_points = 1000  # Track max points in controller (User input)

        # Initialise Serial Manager
        self.serial = SerialSendReceiveManager(self)  # Parse in controller

        self._recording_state = 0
        self._optical_state = 0

        self._current_channel = 1
        # Optical state timer
        self.optical_timer = 0

        self._connect_signals()
        self._init_timer()
        self._init_channel_configs()  # Add initialised channels to the drop down menu

        # Channel config debounce
        self._config_update_timer = QTimer()
        self._config_update_timer.setSingleShot(True)
        self._config_update_timer.timeout.connect(self._send_debounced_config)
        self._pending_channel_config = None  # Store the channel to send after debounce

        # # Initialise heartbeat to MCU
        self.serial.start_heartbeat()
        self.start_optical_check_thread()

        # Initialisation time
        self.cur_time = time.time()
        self._initialised = False
        threading.Timer(1, self._initialise_view_delayed).start()



    def start_optical_check_thread(self):
        self._check_optical_connection()
        timer = threading.Timer(0.5, self.start_optical_check_thread)
        timer.daemon = True
        timer.start()

    def _check_optical_connection(self):
        if time.time() - self.optical_timer > 1.5:
            self.optical_timer = time.time()
            self.view_set_optical_state(0)  # Set the optical connection to disconnected

    def _initialise_view_delayed(self):
        self._initialised = True
        # self._handle_channel_changed(self._current_channel)  # update het view for the current channel

    def schedule_channel_config_send(self, channel):
        self._pending_channel_config = channel
        self._config_update_timer.start(100)  # e.g., 100 ms debounce

    def _send_debounced_config(self):
        if self._pending_channel_config is not None:
            self.send_updated_channel_config(self._pending_channel_config)
            self._pending_channel_config = None

    def _init_channel_configs(self):
        channel_configs = self.model.get_channel_configs()
        for channel in channel_configs.keys():
            self.view.edit_channel_config_view().set_channel_drop_down_item(str(channel))

    def _connect_signals(self):
        self.view.load_replay.connect(self._handle_load_replay)
        self.view.max_points.connect(self.handle_max_points_changed)
        self.view.channel_visibility_change.connect(self._handle_visibility_changed)
        self.view.axis_range_changed.connect(self.handle_axis_range_changed)
        self.view.clear_data.connect(self._handle_clear_data)
        self.view.graph_canvas.hover_signal.connect(self._handle_hover)

        # Device status panel
        self.view.toggle_recording.connect(self._handle_toggle_recording)

        # Channel config connects
        self.view.config_group.selected_channel_changed.connect(self._handle_channel_changed)
        self.view.config_group.alarms_changed.connect(self._handle_alarms_changed)
        self.view.config_group.input_range_changed.connect(self._handle_input_range_changed)
        self.view.config_group.alarm_type_changed.connect(self._handle_alarm_type_changed)
        self.view.config_group.resistive_temp_mode_changed.connect(self._handle_resistive_temp_mode_changed)
        self.view.config_group.current_source_changed.connect(self._handle_current_source_changed)
        self.view.config_group.resistive_sensor_type_changed.connect(self._handle_resistive_temp_sensor_changed)
        self.view.config_group.receive_button_pressed.connect(self._handle_channel_changed)

        # RTC
        self.view.sync_rtc.connect(self._handle_rtc_sync)

    ## TODO Update the channel config in the model, update the entire structure for that channel each time a param changes

    def _handle_rtc_sync(self):
        print("Synced rtc time")
        self.serial.send_rtc_time()

    def _handle_toggle_recording(self):
        """Toggle recording state and update the view."""
        self._recording_state ^= 1  # Toggle the recording state
        self.view_start_stop_recording()
        self.serial.send_recording_status(self._recording_state)
        ### Only if fake data used ####
        # self._fake_data_index = 0
        # self._init_fake_data()

    def view_start_stop_recording(self):
        """ Set the recording state on the view """
        self.view.toggle_recording_status()

    def view_set_optical_state(self, state):
        """ Set the optical state on the view """
        self.view.set_optical_state(state)

    def model_set_channel_config(self):
        pass

    def _check_and_update_alarms(self):
        """
        Check if alarms are occuring and update the channel configs accordingly.
            # Check alarm state
                # If Live -> set/reset every sample
                # If Latched -> once set, never reset.
                # If disabled -> reset all LEDs
        """
        channel_config = self.model.get_channel_configs()
        all_channel_data  = self.model.get_data()
        for channel in channel_config.keys():
            channel_data = all_channel_data[channel]
            alarm_state = self.model.get_channel_config_param(channel, ALARM_STATE)

            # Ensure channel data exists, break if none
            if not channel_data:
                self.model.set_channel_config_param(channel, ALARM_STATE, ALARM_NOT_OCCURRING)
                continue

            alarm_type = self.model.get_channel_config_param(channel, ALARM_TYPE)
            alarm_low = self.model.get_channel_config_param(channel, ALARM_LOW) / 1000
            alarm_high = self.model.get_channel_config_param(channel, ALARM_HIGH) / 1000
            if alarm_type == ALARM_TYPE_LIVE:
                if not (alarm_low < channel_data[len(channel_data) - 1] < alarm_high):
                    self.model.set_channel_config_param(channel, ALARM_STATE, ALARM_OCCURRING)
                else:
                    self.model.set_channel_config_param(channel, ALARM_STATE, ALARM_NOT_OCCURRING)
            elif alarm_type == ALARM_TYPE_LATCHED:
                if not (alarm_low < channel_data[len(channel_data) - 1] < alarm_high) and alarm_state != ALARM_OCCURRING:
                    self.model.set_channel_config_param(channel, ALARM_STATE, ALARM_OCCURRING)
            if alarm_type == ALARM_TYPE_DISABLED:
                self.model.set_channel_config_param(channel, ALARM_STATE, ALARM_NOT_OCCURRING)

    def _update_alarm_indicator(self):
        """ Update the alarm indicator in the view"""
        # Update view
        alarm_state = self.model.get_channel_config_param(self._current_channel, ALARM_STATE)
        self.view.edit_channel_config_view().set_alarm_occurring(alarm_state)

    def _handle_channel_changed(self, channel: int):
        """Update channel type and update the model."""
        self._current_channel = channel
        alarm_high = self.model.get_channel_config_param(channel, ALARM_HIGH) / 1000 # Alarms have three decimals buffered
        alarm_low = self.model.get_channel_config_param(channel, ALARM_LOW) / 1000
        input_range = self.model.get_channel_config_param(channel, INPUT_RANGE)
        alarm_type = self.model.get_channel_config_param(channel, ALARM_TYPE)
        alarm_occurring = self.model.get_channel_config_param(channel, ALARM_STATE)
        resistive_temp_enabled = self.model.get_channel_config_param(channel, TEMP_ENABLED)
        resistive_temp_sensor_type = self.model.get_channel_config_param(channel, SENSOR_TYPE)
        current_source = self.model.get_channel_config_param(channel, CURRENT_SOURCE)
        self.view.update_channel_config_group(channel, alarm_high, alarm_low, input_range, alarm_type, alarm_occurring, resistive_temp_enabled, resistive_temp_sensor_type, current_source)

    def _handle_resistive_temp_sensor_changed(self, channel):
        """ Update the resistive temp sensor type """
        sensor = self.view.config_group.get_resistive_sensor_type()
        self.model.set_channel_config_param(channel, SENSOR_TYPE, sensor)
        self.schedule_channel_config_send(channel)

    def _handle_current_source_changed(self, channel):
        """Update current source used by the resistive temperature channel """
        current_source = self.view.config_group.get_current_source()
        self.model.set_channel_config_param(channel, CURRENT_SOURCE, current_source)
        self.schedule_channel_config_send(channel)

    def _handle_resistive_temp_mode_changed(self, channel):
        """
        Update resistive temperature mode for a channel. If resistive mode is checked, set the channel to resistive
        temperature mode, otherwise set the channel back to voltage. Change the channel type and the temp_enabled param
        """
        # Can only enable temp mode for channels 1-4
        if channel > 4:
            return

        resistive_temp_mode = self.view.config_group.get_resistive_temp_mode()
        if resistive_temp_mode:
            channel_type = CHANNEL_TYPE_TEMPERATURE
        else:
            channel_type = CHANNEL_TYPE_VOLTAGE
            self.model.set_channel_config_param(channel, CURRENT_SOURCE, TEMP_SENSOR_DISABLED) # Disable current source
            self.model.set_channel_config_param(channel, SENSOR_TYPE, CURRENT_SOURCE_DISABLED)  # Disable sensor type
        # Update channel type
        self.model.set_channel_config_param(channel, CHANNEL_TYPE, channel_type)
        # Update resistive temp mode
        self.model.set_channel_config_param(channel, TEMP_ENABLED, resistive_temp_mode)
        self.schedule_channel_config_send(channel)

    def _handle_alarm_type_changed(self, channel):
        """Update alarm type for a channel."""
        alarm_type = self.view.config_group.get_alarm_type()
        self.model.set_channel_config_param(channel, ALARM_TYPE, alarm_type)
        self.schedule_channel_config_send(channel)

    def _handle_input_range_changed(self, channel):
        """Update input range for a channel."""
        input_range = self.view.config_group.get_input_range()
        self.model.set_channel_config_param(channel, INPUT_RANGE, input_range)
        self.schedule_channel_config_send(channel)

    def _handle_alarms_changed(self, channel):
        """Validate and update alarm thresholds for a channel."""
        high = self.view.config_group.get_alarm_high()
        low = self.view.config_group.get_alarm_low()

        if high < low:
            self.view.config_group.alarm_high_spin.setValue(low)
            high = low

        self.model.set_channel_config_param(channel, ALARM_HIGH, high*1000)
        self.model.set_channel_config_param(channel, ALARM_LOW, low*1000)
        self.schedule_channel_config_send(channel)

    def _init_fake_data(self):
        """Start a timer that simulates incoming data every 500ms."""
        self.fake_data_timer = QTimer()
        self.fake_data_timer.timeout.connect(self._add_fake_data)
        self.fake_data_timer.start(500)  # 500ms interval

    def _add_fake_data(self):
        """Injects fake sample data into the model at a fixed interval."""
        if self._fake_data_index < len(FAKE_DATA):
            timestamp, data = FAKE_DATA[self._fake_data_index]
            self.add_data(timestamp, data)
            self._fake_data_index += 1
        else:
            self.fake_data_timer.stop()

    def add_data(self, timestamp, data):
        """Add data to the model and update the plot."""
        self.model.store_live_data(timestamp, data)
        # self.update_plot()

    def _init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(500)

    def handle_max_points_changed(self, max_points):
        """Update max points and refresh plot."""
        self.current_max_points = max_points
        self.update_plot()

    def handle_axis_range_changed(self, y_min, y_max):
        """Update the Y-axis range of the plot."""
        self.view.edit_graph_canvas_view().set_y_lim(y_min, y_max)

    def _handle_clear_data(self):
        """Clear all data from the model and update the plot."""
        self.view.edit_graph_canvas_view().clear_plot()
        self.model.clear_data()

    def _handle_load_replay(self, filename):
        success = self.model.load_csv(filename)
        if success:
            self.view.status_bar.showMessage(f"Loaded: {filename}", 5000)
            # Populate channel dropdown
            self.view.config_group.channel_combo.blockSignals(True)
            self.view.config_group.channel_combo.clear()
            self.view.config_group.channel_combo.addItems(self.model.replay_data.keys())
            self.view.config_group.channel_combo.blockSignals(False)

        else:
            self.view.status_bar.showMessage("Invalid file format", 5000)
        self.update_plot()

    def _handle_visibility_changed(self):
        self.update_plot()

    def _handle_hover(self, x, global_x, global_y):
        """Handle hover events on the plot canvas, showing tooltips for selected channels."""
        if x is None:
            self.view.tooltip_label.hide()
            return

        relative_times = self.model.get_relative_times()

        if not relative_times:  # Don't show tooltip if no data (avoid crashing)
            return

        # Find closest data point
        closest_idx = np.argmin(np.abs(np.array(relative_times) - x))

        # Build tooltip text for selected channels only
        text = f"Time: {relative_times[closest_idx]:.3f}s\n"
        for ch, values in self.model.get_data().items():
            # Build the hover tool tip text
            unit = CHANNEL_TYPE_MAP.get(self.model.get_channel_config_param(ch, CHANNEL_TYPE))
            text += f"{ch}: {values[closest_idx]:.3f} {unit}\n"

        # Update tooltip
        self.view.tooltip_label.setText(text)
        self.view.tooltip_label.adjustSize()
        self.view.tooltip_label.move(global_x + 15, global_y + 15)
        self.view.tooltip_label.show()

    def send_updated_channel_config(self, channel):
        """Send updated channel config to the controller."""
        self.serial.send_channel_config(channel)


    def update_channel_config(self, channel, channel_type, input_range, alarm_type, alarm_occurring,
                                    resistive_temp_enabled, current_source, resistive_temp_sensor_type, alarm_high, alarm_low):
        """Update channel config in the model and update the plot."""

        self.model.set_channel_config_param(channel, CHANNEL_TYPE, channel_type)
        self.model.set_channel_config_param(channel, INPUT_RANGE, input_range)
        self.model.set_channel_config_param(channel, ALARM_TYPE, alarm_type)
        self.model.set_channel_config_param(channel, ALARM_STATE, alarm_occurring)
        self.model.set_channel_config_param(channel, TEMP_ENABLED, resistive_temp_enabled)
        self.model.set_channel_config_param(channel, CURRENT_SOURCE, current_source)
        self.model.set_channel_config_param(channel, SENSOR_TYPE, resistive_temp_sensor_type)
        self.model.set_channel_config_param(channel, ALARM_HIGH, alarm_high)  # Store alarms without decimal
        self.model.set_channel_config_param(channel, ALARM_LOW, alarm_low)
        # Update the view TODO Make this function more reliable
        # if self._initialised:


    def update_channel_config_view_button(self):
        channel = self._current_channel
        alarm_high = self.model.get_channel_config_param(channel, ALARM_HIGH) / 1000  # Alarms have three decimals buffered
        alarm_low = self.model.get_channel_config_param(channel, ALARM_LOW) / 1000
        input_range = self.model.get_channel_config_param(channel, INPUT_RANGE)
        alarm_type = self.model.get_channel_config_param(channel, ALARM_TYPE)
        alarm_occurring = self.model.get_channel_config_param(channel, ALARM_STATE)
        resistive_temp_enabled = self.model.get_channel_config_param(channel, TEMP_ENABLED)
        resistive_temp_sensor_type = self.model.get_channel_config_param(channel, SENSOR_TYPE)
        current_source = self.model.get_channel_config_param(channel, CURRENT_SOURCE)
        self.view.update_channel_config_group(
                channel,
                alarm_high,
                alarm_low,
                input_range,
                alarm_type,
                alarm_occurring,
                resistive_temp_enabled,
                resistive_temp_sensor_type,
                current_source
            )

    def update_live_channel_data(self, timestamp, ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8):
        """Update live channel data in the model and update the plot."""
        channel_values = [ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8]
        self.model.store_live_data(timestamp, channel_values)
        # print(self.model.get_data())

    def update_plot(self):
        """Update plots with truncated data based on current_max_points."""
        plot_data = self.model.get_data()
        if plot_data:
            # Truncate data to current_max_points
            relative_times = self.model.get_relative_times()
            truncated_times = relative_times[:self.current_max_points]
            truncated_data = {
                ch: vals[:self.current_max_points]
                for ch, vals in plot_data.items()
            }

            # Get active channels and labels
            channels = self.model.get_channel_configs()
            channels_to_plot = [
                ch for ch in channels.keys()
                # if self.model.channel_info.get(ch, {}).get('type') in self.view.get_active_channels()
            ]
            y_labels = {ch: CHANNEL_TYPE_MAP.get(config[CHANNEL_TYPE], 'Unknown') for ch, config in channels.items()}

            # Group channels by types
            voltage_channels = []
            acceleration_channels = []
            temperature_channels = []
            for ch in channels_to_plot:
                ch_type = channels[ch][CHANNEL_TYPE]
                if ch_type == CHANNEL_TYPE_VOLTAGE:
                    voltage_channels.append(ch)
                elif ch_type == CHANNEL_TYPE_ACCELERATION:
                    acceleration_channels.append(ch)
                elif ch_type in [CHANNEL_TYPE_TEMPERATURE]:
                    temperature_channels.append(ch)

            # Get Y-axis range from view
            y_min, y_max = self.view.edit_graph_canvas_view().get_y_axis()

            # Update plot with grouped channels
            if self.model.get_data():
                self.view.graph_canvas.update_plot(
                    truncated_times,
                    truncated_data,
                    voltage_channels,
                    acceleration_channels,
                    temperature_channels,
                    "Time (s)",
                    y_labels,
                    y_min,
                    y_max
                )
            # Check and update alarms
            self._check_and_update_alarms()
            self._update_alarm_indicator()
        else:
            self.view.edit_graph_canvas_view().clear_plot()
            self.model.clear_data()