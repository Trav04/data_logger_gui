# controller.py
from PyQt5.QtCore import QTimer


class MainController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.active_types = []

        self._connect_signals()
        self._init_timer()

    def _connect_signals(self):
        self.view.load_replay.connect(self.handle_load_replay)
        self.view.max_points_changed.connect(self.handle_max_points_changed)
        self.view.channel_visibility_change.connect(self.handle_visibility_changed)
        # self.view.axis_range_changed.connect(self.handle_axis_range_changed)
        # self.view.sync_rtc.connect(self.handle_sync_rtc)
        # self.view.toggle_recording.connect(self.handle_recording)
        # self.view.clear_data.connect(self.handle_clear_data)
        # self.view.plot_canvas.hover_signal.connect(self.handle_hover)

    def _init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(2000)

    def handle_load_replay(self, filename):
        success = self.model.load_csv(filename)
        if success:
            self.view.status_bar.showMessage(f"Loaded: {filename}", 5000)
        else:
            self.view.status_bar.showMessage("Invalid file format", 5000)
        self.update_plot()

    def handle_max_points_changed(self, value):
        self.model.max_points = value

    def handle_visibility_changed(self, active_types):
        self.active_types = active_types
        self.update_plot()

    def update_plot(self):
        """Update the plots based on the current model data and active channels."""
        if self.model.data:
            # Get data from the model
            x_data = self.model.relative_times
            y_data = self.model.data
            y_labels = {ch: info['unit'] for ch, info in self.model.channel_info.items()}

            # Get active types from the view and filter channels
            active_types = self.view.get_active_types()
            channels_to_plot = [
                ch for ch in self.model.data
                if self.model.channel_info.get(ch, {}).get('type') in active_types
            ]

            # Update the plot in the view
            self.view.graph_canvas.update_plot(x_data, y_data, channels_to_plot, "Time (s)", y_labels)
