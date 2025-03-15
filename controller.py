# controller.py
from PyQt5.QtCore import QTimer
import numpy as np

class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        self._connect_signals()
        self._init_timer()

    def _connect_signals(self):
        self.view.load_replay.connect(self.handle_load_replay)
        self.view.max_points_changed.connect(self.handle_max_points_changed)
        self.view.channel_visibility_change.connect(self.handle_visibility_changed)
        # self.view.axis_range_changed.connect(self.handle_axis_range_changed)
        # self.view.sync_rtc.connect(self.handle_sync_rtc)
        # self.view.toggle_recording.connect(self.handle_recording)
        self.view.clear_data.connect(self.handle_clear_data)
        self.view.graph_canvas.hover_signal.connect(self.handle_hover)

    def _init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(2000)

    def handle_clear_data(self):
        """Clear all data from the model and update the plot."""
        self.model.data.clear()  # Clear data dictionary
        self.model.relative_times = []  # Clear timestamps
        self.model.channel_info = {}  # Clear channel info
        self.update_plot()  # Refresh the plot

    def handle_load_replay(self, filename):
        success = self.model.load_csv(filename)
        if success:
            self.view.status_bar.showMessage(f"Loaded: {filename}", 5000)
        else:
            self.view.status_bar.showMessage("Invalid file format", 5000)
        self.update_plot()

    def handle_max_points_changed(self, value):
        self.model.max_points = value

    def handle_visibility_changed(self):
        self.update_plot()

    def handle_hover(self, x, global_x, global_y):
        """Handle hover events on the plot canvas."""
        if not self.model.data or x is None:
            self.view.tooltip_label.hide()
            return

        # Find closest data point
        closest_idx = np.argmin(np.abs(np.array(self.model.relative_times) - x))

        # Build tooltip text
        text = f"Time: {self.model.relative_times[closest_idx]:.3f}s\n"
        for ch, values in self.model.data.items():
            if ch in self.model.channel_info:
                unit = self.model.channel_info[ch]['unit']
                text += f"{ch}: {values[closest_idx]:.2f} {unit}\n"

        # Update tooltip
        self.view.tooltip_label.setText(text)
        self.view.tooltip_label.adjustSize()
        self.view.tooltip_label.move(global_x + 15, global_y + 15)
        self.view.tooltip_label.show()

    def update_plot(self):
        """Update the plots based on the current model data and active channels."""
        if self.model.data:
            # Get data from the model
            x_data = self.model.relative_times
            y_data = self.model.data
            y_labels = {ch: info['unit'] for ch, info in self.model.channel_info.items()}

            # Get active types from the view and filter channels
            channels_to_plot = [
                ch for ch in self.model.data
                if self.model.channel_info.get(ch, {}).get('type') in self.view.get_active_channels()

            ]

            # Update the plot in the view
            self.view.graph_canvas.update_plot(x_data, y_data, channels_to_plot, "Time (s)", y_labels)
        else:
            # Clear the plot if no data exists
            self.view.graph_canvas.axes.clear()
            self.view.graph_canvas.draw()