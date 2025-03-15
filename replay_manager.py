import sys
import csv
from datetime import datetime

UNIT_TYPE_MAP = {
    'Volts': 'voltage',
    'V': 'voltage',
    'C': 'temperature',
    'm/s^2': 'acceleration'
}

class ReplayManager:
    def __init__(self):
        self.data = {}
        self.relative_times = []
        self.channel_info = {}
        self.rtc_time = datetime.now()
        self.recording = False
        self.optical_link = True
        self.alarm_thresholds = {}
        self.input_ranges = {}
        self.temp_configs = {}

    def load_csv(self, filename, max_points):
        self.data.clear()
        self.relative_times = []
        self.channel_info = {}

        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader)
                headers = [h.strip('\ufeff') for h in headers]

                if len(headers) < 1 or headers[0] != "Timestamp":
                    return False

                timestamps = []
                data = {header: [] for header in headers[1:]}

                for row in reader:
                    if len(row) != len(headers):
                        continue

                    try:
                        timestamp = datetime.strptime(row[0], "%Y-%m-%d_%H-%M-%S.%f")
                        timestamps.append(timestamp)
                        for header, value in zip(headers[1:], row[1:]):
                            data[header].append(float(value))
                    except (ValueError, IndexError):
                        continue

                if not timestamps:
                    return False

                first_ts = timestamps[0]
                self.relative_times = [(ts - first_ts).total_seconds() for ts in timestamps]

                for header in headers[1:]:
                    self.data[header] = data[header][:max_points]
                self.relative_times = self.relative_times[:max_points]

                for header in headers[1:]:
                    parts = header.split()
                    unit = parts[1] if len(parts) > 1 else ''
                    channel_type = UNIT_TYPE_MAP.get(unit, 'unknown')
                    self.channel_info[header] = {'unit': unit, 'type': channel_type}

                return True
        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
            return False