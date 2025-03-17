# controller.py
from PyQt5.QtCore import QTimer
import numpy as np

class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.current_max_points = 1000  # Track max points in controller (User input)

        self._connect_signals()
        self._init_timer()

    def _connect_signals(self):
        self.view.load_replay.connect(self.handle_load_replay)
        self.view.max_points.connect(self.handle_max_points_changed)
        self.view.channel_visibility_change.connect(self.handle_visibility_changed)
        self.view.axis_range_changed.connect(self.handle_axis_range_changed)
        # self.view.sync_rtc.connect(self.handle_sync_rtc)
        # self.view.toggle_recording.connect(self.handle_recording)
        self.view.clear_data.connect(self.handle_clear_data)
        self.view.graph_canvas.hover_signal.connect(self.handle_hover)

        # Channel config connects
        self.view.config_group.config_changed.connect(self.handle_config_changed)

    ## TODO Update the channel config in the model, update the entire structure for that channel each time a param changes

    def handle_config_changed(self, channel):
        """Handle configuration changes and persist to model."""

        # Get current UI values
        config = {
            'alarm_high': self.view.config_group.get_alarm_high(),
            'alarm_low': self.view.config_group.get_alarm_low(),
            'input_range': self.view.config_group.get_input_range(),
            'resistive_temp_enabled': self.view.config_group.get_temp_enabled(),
            'current_source': self.view.config_group.get_current_source(),
            'sensor_type': self.view.config_group.get_sensor_type()
        }

        # Update model with new config
        self.model.channel_configs[channel].update(config)
        print(self.model.channel_configs[channel])

        # Convert voltage to temperature if enabled
        if config['resistive_temp_enabled']:
            self.model.update_channel_type(channel)

        self.update_plot()

    def _update_config_ui(self, channel):
        """Update UI with current channel configuration"""
        if not channel:
            return

        self.model.initialize_channel_config(channel)
        config = self.model.channel_configs[channel]

        # Update UI elements
        self.view.config_group.alarm_high_spin.setValue(config['alarm_high'])
        self.view.config_group.alarm_low_spin.setValue(config['alarm_low'])
        self.view.config_group.input_range_combo.setCurrentText(config['input_range'])
        self.view.config_group.alarm_type_combo.setCurrentText(config['alarm_type'])
        self.view.config_group.alarm_state_led.set_status(config['alarm_state'])

        # Temperature config
        is_voltage = self.model.channel_info[channel]['type'] == 'Voltage'
        self.view.config_group.temp_enable_check.setVisible(is_voltage)
        self.view.config_group.temp_enable_check.setChecked(config['temp_enabled'])
        self.view.config_group.current_source_combo.setCurrentText(config['current_source'])
        self.view.config_group.sensor_type_combo.setCurrentText(config['sensor_type'])

    def _validate_alarm_thresholds(self, channel):
        """Validate and update alarm thresholds for a channel."""
        high = self.view.config_group.get_alarm_high()
        low = self.view.config_group.get_alarm_low()

        if high < low:
            self.view.config_group.alarm_high_spin.setValue(low)
            high = low

        self.model.channel_configs[channel]['alarm_high'] = high
        self.model.channel_configs[channel]['alarm_low'] = low

    def _update_input_range(self, channel):
        """Update input range for a channel."""
        input_range = self.view.config_group.get_input_range()
        self.model.channel_configs[channel]['input_range'] = input_range

    def _update_temp_config(self, channel):
        """Update temperature conversion for a channel."""
        enabled = self.view.config_group.get_temp_enabled()
        self.model.channel_configs[channel]['resistive_temp_enabled'] = enabled
        self.model.update_channel_type(channel)

    def _update_current_source(self, channel):
        """Update current source for a channel."""
        current_source = self.view.config_group.get_current_source()
        self.model.channel_configs[channel]['current_source'] = current_source

    def _update_sensor_type(self, channel):
        """Update sensor type for a channel."""
        sensor_type = self.view.config_group.get_sensor_type()
        self.model.channel_configs[channel]['sensor_type'] = sensor_type

    def _init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(2000)

    def handle_max_points_changed(self, max_points):
        """Update max points and refresh plot."""
        self.current_max_points = max_points
        self.update_plot()

    def handle_axis_range_changed(self, ymin, ymax):
        """Update the Y-axis range of the plot."""
        self.update_plot()
        # self.view.graph_canvas.axes.set_ylim(ymin, ymax)
        # self.view.graph_canvas.draw()  # Redraw the canvas

    def handle_clear_data(self):
        """Clear all data from the model and update the plot."""
        self.model.replay_data.clear()  # Clear data dictionary
        self.model.replay_relative_times = []  # Clear timestamps
        self.model.channel_info = {}  # Clear channel info
        self.update_plot()  # Refresh the plot

    def handle_load_replay(self, filename):
        success = self.model.load_csv(filename)
        if success:
            self.view.status_bar.showMessage(f"Loaded: {filename}", 5000)
            # Populate channel dropdown
            self.view.config_group.channel_combo.clear()
            self.view.config_group.channel_combo.addItems(self.model.replay_data.keys())
        else:
            self.view.status_bar.showMessage("Invalid file format", 5000)
        self.update_plot()

    def handle_visibility_changed(self):
        self.update_plot()

    def handle_hover(self, x, global_x, global_y):
        """Handle hover events on the plot canvas, showing tooltips for selected channels."""
        if not self.model.replay_data or x is None:
            self.view.tooltip_label.hide()
            return

        # Find closest data point
        closest_idx = np.argmin(np.abs(np.array(self.model.replay_relative_times) - x))

        # Build tooltip text for selected channels only
        text = f"Time: {self.model.replay_relative_times[closest_idx]:.3f}s\n"
        for ch, values in self.model.replay_data.items():
            # Only include channels that are currently visible
            if ch in self.model.channel_info and self.model.channel_info[ch]['type'] in self.view.get_active_channels():
                unit = self.model.channel_info[ch]['unit']
                text += f"{ch}: {values[closest_idx]:.2f} {unit}\n"

        # Update tooltip
        self.view.tooltip_label.setText(text)
        self.view.tooltip_label.adjustSize()
        self.view.tooltip_label.move(global_x + 15, global_y + 15)
        self.view.tooltip_label.show()

    def update_plot(self):
        """Update plots with truncated data based on current_max_points."""
        if self.model.replay_data:
            # Truncate data to current_max_points
            truncated_times = self.model.replay_relative_times[:self.current_max_points]
            truncated_data = {
                ch: vals[:self.current_max_points]
                for ch, vals in self.model.replay_data.items()
            }

            # Get active channels and labels
            channels_to_plot = [
                ch for ch in self.model.replay_data
                if self.model.channel_info.get(ch, {}).get('type') in self.view.get_active_channels()
            ]
            y_labels = {ch: info['unit'] for ch, info in self.model.channel_info.items()}

            # Get Y-axis range from view
            y_min, y_max = self.view.get_y_axis()

            # Update plot with truncated data
            self.view.graph_canvas.update_plot(
                truncated_times,
                truncated_data,
                channels_to_plot,
                "Time (s)",
                y_labels,
                y_min,
                y_max
            )
        else:
            self.view.clear_graph()