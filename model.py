# model.py
import csv
from datetime import datetime
import numpy as np

CHANNEL_TYPE_VOLTAGE = "Voltage"
CHANNEL_TYPE_TEMPERATURE = "Temperature"
CHANNEL_TYPE_ACCELERATION = "Acceleration"


UNIT_TYPE_MAP = {
    'Volts': 'Voltage',
    'V': 'Voltage',
    'C': 'Temperature',
    'm/s^2': 'Acceleration'
}

FORMAT_TIMESTAMP = "%Y-%m-%d_%H-%M-%S.%f"

TIMESTAMP = "Timestamp"

class DataModel:
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
        self.channel_configs = {}  # Stores configuration for all channels
        self.temp_sensor_types = ['Thermistor', 'Platinum RTD']
        self.current_sources = ['10μA', '200μA']
        self.input_ranges = ['+/-10V', '+/-1V']
        self.alarm_types = ['Disabled', 'Latched', 'Live']

    def initialize_channel_config(self, channel):
        """Initialize default configuration for a channel"""
        if channel not in self.channel_configs:
            is_voltage = self.channel_info.get(channel, {}).get('type') == 'Voltage'
            self.channel_configs[channel] = {
                'alarm_high': 100,
                'alarm_low': 0,
                'input_range': '+/-10V',
                'alarm_type': 'Disabled',
                'alarm_state': False,
                'temp_enabled': False,
                'current_source': '10μA' if is_voltage else None,
                'sensor_type': 'Thermistor' if is_voltage else None
            }

    def update_channel_type(self, channel):
        """Update channel type if temperature conversion is enabled"""
        if self.channel_configs[channel]['temp_enabled']:
            self.channel_info[channel]['type'] = 'Temperature'
            self.channel_info[channel]['unit'] = 'C'

    def load_csv(self, filename):
        """
        Loads data from a CSV file, processes timestamps, and extracts channel information.

        Params:
            filename (str): The path to the CSV file to be loaded.

        Returns:
            bool: True if the file was successfully loaded, False otherwise.
        """
        self.data.clear()
        self.relative_times = []
        self.channel_info = {}

        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader)
                headers = [h.strip('\ufeff') for h in headers]

                # Make sure timestamp column exists
                if len(headers) < 1 or headers[0] != TIMESTAMP:
                    return False

                timestamps = []
                data = {header: [] for header in headers[1:]}

                for row in reader:
                    if len(row) != len(headers):
                        continue

                    try:
                        timestamp = datetime.strptime(row[0], FORMAT_TIMESTAMP)
                        timestamps.append(timestamp)
                        for header, value in zip(headers[1:], row[1:]):
                            data[header].append(float(value))
                    except (ValueError, IndexError):
                        continue

                # Timestamps not valid
                if not timestamps:
                    return False

                # Manage timestamps
                first_ts = timestamps[0]
                self.relative_times = [(ts - first_ts).total_seconds() for ts in timestamps]

                # Store all data (no truncation)
                for header in headers[1:]:
                    self.data[header] = data[header]

                # Extract channel info
                for header in headers[1:]:
                    # Extract unit from header (supports "Channel (V)" or "Channel V")
                    unit = ""
                    if '(' in header and ')' in header:
                        # Handle parentheses format: "Channel (Unit)"
                        unit = header.split('(')[-1].split(')')[0].strip()
                    else:
                        # Handle space-separated format: "Channel Unit"
                        parts = header.split()
                        unit = parts[-1] if len(parts) > 1 else ''

                    channel_type = UNIT_TYPE_MAP.get(unit, 'unknown')  # Use 'unknown' as default
                    self.channel_info[header] = {'unit': unit, 'type': channel_type}

                return True
        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
            return False

