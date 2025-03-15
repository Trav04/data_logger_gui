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
        self.view.visibility_changed.connect(self.handle_visibility_changed)
        # self.view.axis_range_changed.connect(self.handle_axis_range_changed)
        # self.view.sync_rtc.connect(self.handle_sync_rtc)
        # self.view.toggle_recording.connect(self.handle_recording)
        # self.view.clear_data.connect(self.handle_clear_data)
        # self.view.plot_canvas.hover_signal.connect(self.handle_hover)

    def _init_timer(self):
        self.timer = QTimer()
        # self.timer.timeout.connect(self.update_plots)
        # self.timer.start(100)

    def handle_load_replay(self, filename):
        success = self.model.load_csv(filename)
        if success:
            self.view.status_bar.showMessage(f"Loaded: {filename}", 5000)
        else:
            self.view.status_bar.showMessage("Invalid file format", 5000)

    def handle_max_points_changed(self, value):
        self.model.max_points = value

    def handle_visibility_changed(self, active_types):
        self.active_types = active_types

    # Other signal handlers following same pattern...