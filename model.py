# model.py
import csv
from datetime import datetime
import numpy as np

CHANNEL_TYPE_VOLTAGE = "Voltage"
CHANNEL_TYPE_RESISTIVE_TEMPERATURE = "Resistive Temperature"
CHANNEL_TYPE_ACCELERATION = "Acceleration"
CHANNEL_TYPE_TEMPERATURE = "Temperature"

UNIT_TYPE_MAP = {
    'Volts': 'Voltage',
    'V': 'Voltage',
    'C': 'Temperature',
    'm/s^2': 'Acceleration'
}

FORMAT_TIMESTAMP = "%Y-%m-%d_%H-%M-%S.%f"

TIMESTAMP = "Timestamp"

INPUT_RANGE_10V = "+/-10V"
INPUT_RANGE_1V = "+/-1V"
ALARM_TYPE_DISABLED = "Disabled"
ALARM_TYPE_LATCHED = "Latched"
ALARM_TYPE_LIVE = "Live"

CURRENT_SOURCE_10UA = "10μA"
CURRENT_SOURCE_200UA = "200μA"

TEMP_SENSOR_THERMISTOR = "Thermistor"
TEMP_SENSOR_RTD = "Platinum RTD"

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

    def initialize_channel_config(self, channel, channel_type):
        """Initialize default configuration for a channel"""
        if channel not in self.channel_configs:
            is_voltage = self.channel_info.get(channel, {}).get('type') == 'Voltage'
            self.channel_configs[channel] = {
                'channel_type': channel_type,
                'alarm_high': 100,
                'alarm_low': 0,
                'input_range': INPUT_RANGE_10V,  # Default to +/-10V
                'alarm_type': ALARM_TYPE_DISABLED,  # Default to disabled
                'alarm_state': False,  # Default OFF
                'temp_enabled': False,  # Default not resistive temperature mode
                'current_source': '10μA' if channel_type==CHANNEL_TYPE_RESISTIVE_TEMPERATURE else None,
                'sensor_type': 'Thermistor' if channel_type==CHANNEL_TYPE_RESISTIVE_TEMPERATURE else None
            }

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

