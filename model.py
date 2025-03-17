# model.py
import csv
from datetime import datetime
from pprint import pprint

import numpy as np

CHANNEL_TYPE_VOLTAGE = "Voltage"
CHANNEL_TYPE_RESISTIVE_TEMPERATURE = "Resistive Temperature"
CHANNEL_TYPE_ACCELERATION = "Acceleration"
CHANNEL_TYPE_TEMPERATURE = "Temperature"

UNIT_TYPE_MAP = {
    'Volts': CHANNEL_TYPE_VOLTAGE,
    'V': CHANNEL_TYPE_VOLTAGE,
    'C': CHANNEL_TYPE_TEMPERATURE,
    'm/s^2': CHANNEL_TYPE_ACCELERATION
}

CHANNEL_TYPE_MAP = {
    CHANNEL_TYPE_VOLTAGE : "V",
    CHANNEL_TYPE_TEMPERATURE : "C",
    CHANNEL_TYPE_ACCELERATION : "m/s^2",
    CHANNEL_TYPE_RESISTIVE_TEMPERATURE : "C"
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

## Channel CONFIG defines
CHANNEL_TYPE = 'channel_type'
ALARM_HIGH = "alarm_high"
ALARM_LOW = "alarm_low"
INPUT_RANGE = 'input_range'
ALARM_STATE = 'alarm_state'
TEMP_ENABLED = 'temp_enabled'
CURRENT_SOURCE = 'current_source'
SENSOR_TYPE = 'sensor_type'
ALARM_TYPE = 'alarm_type'

class DataModel:
    def __init__(self):
        # Replay data
        self.replay_data = {}
        self.replay_relative_times = []
        self.channel_info = {}

        # Live mode data
        self.channel_configs = {}  # Stores configuration for all channels
        self.live_data = {channel: [] for channel in range(1, 9)}
        self.live_relative_times = []
        self.start_time = None

    def initialize_channel_config(self, channel, channel_type):
        """Initialize default configuration for a channel"""
        if channel not in self.channel_configs:
            self.channel_configs[channel] = {
                CHANNEL_TYPE: channel_type,
                ALARM_HIGH: 100,
                ALARM_LOW: 0,
                INPUT_RANGE: INPUT_RANGE_10V,  # Default to +/-10V
                ALARM_TYPE: ALARM_TYPE_DISABLED,  # Default to disabled
                ALARM_STATE: False,  # Default OFF
                TEMP_ENABLED: False,  # Default not resistive temperature mode
                CURRENT_SOURCE: CURRENT_SOURCE_10UA if channel_type == CHANNEL_TYPE_RESISTIVE_TEMPERATURE else None,
                SENSOR_TYPE: TEMP_SENSOR_THERMISTOR if channel_type == CHANNEL_TYPE_RESISTIVE_TEMPERATURE else None
            }

    def store_live_data(self, timestamp, channel_values):
        """
        Stores live data for all 8 channels using relative time.

        Params:
            timestamp (datetime): The timestamp of the data sample.
            channel_values (list): List of 8 float values, one per channel.
        """
        if len(channel_values) != 8:
            raise ValueError("Expected 8 channel values, got {}".format(len(channel_values)))

        # Format the time
        timestamp_f = datetime.strptime(timestamp, FORMAT_TIMESTAMP)

        # Set initial time reference
        if self.start_time is None:
            self.start_time = timestamp_f

        relative_time = (timestamp_f - self.start_time).total_seconds()

        # Compute relative time in seconds
        self.live_relative_times.append(relative_time)

        # Append channel data
        for i in range(8):
            self.live_data[i + 1].append(channel_values[i])

    def _update_channel_type(self, channel, channel_type):
        self.channel_configs[channel][CHANNEL_TYPE] = channel_type

    def load_csv(self, filename):
        """
        Loads data from a CSV file, processes timestamps, and extracts channel
        configuration based on header units. The loaded data is appended to the
        live mode data structures (self.live_data and self.live_relative_times),
        so if more data becomes available it will be added to what is already there.

        Params:
            filename (str): The path to the CSV file to be loaded.

        Returns:
            bool: True if the file was successfully loaded, False otherwise.
        """
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                headers = next(reader)
                headers = [h.strip('\ufeff') for h in headers]

                # Ensure the first header is the Timestamp column.
                if len(headers) < 1 or headers[0] != TIMESTAMP:
                    return False

                # Determine the number of channels from the CSV file.
                num_channels = len(headers) - 1

                # Initialize channel configurations based on header info.
                # Supports both "Channel (Unit)" and "Channel Unit" formats.
                for channel_num, header in enumerate(headers[1:], start=1):
                    unit = ""
                    if '(' in header and ')' in header:
                        unit = header.split('(')[-1].split(')')[0].strip()
                    else:
                        parts = header.split()
                        unit = parts[-1] if len(parts) > 1 else ''
                    channel_type = UNIT_TYPE_MAP.get(unit, CHANNEL_TYPE_VOLTAGE)
                    self._update_channel_type(channel_num, channel_type)

                # Process each row in the CSV file.
                for row in reader:
                    if len(row) != len(headers):
                        continue
                    try:
                        # Parse timestamp.
                        timestamp = datetime.strptime(row[0], FORMAT_TIMESTAMP)
                        # If start_time is not set, initialize it with the first timestamp.
                        if self.start_time is None:
                            self.start_time = timestamp
                        relative_time = (timestamp - self.start_time).total_seconds()
                        self.live_relative_times.append(relative_time)

                        # Process and store channel values.
                        for i, value in enumerate(row[1:], start=1):
                            try:
                                channel_value = float(value)
                            except ValueError:
                                channel_value = 0.0  # Fallback in case of conversion issues.
                            self.live_data[i].append(channel_value)
                    except Exception:
                        continue
                return True

        except Exception as e:
            print(f"Error loading CSV: {str(e)}")
            return False

    def get_data(self):
        return self.live_data

    def get_relative_times(self):
        return self.live_relative_times

    def get_channel_configs(self):
        return self.channel_configs


    # def load_csv(self, filename):
    #     """
    #     Loads data from a CSV file, processes timestamps, and extracts channel information.
    #
    #     Params:
    #         filename (str): The path to the CSV file to be loaded.
    #
    #     Returns:
    #         bool: True if the file was successfully loaded, False otherwise.
    #     """
    #     # Clear existing data
    #     self.replay_data.clear()
    #     self.replay_relative_times = []
    #     self.channel_info = {}
    #
    #     try:
    #         with open(filename, 'r', encoding='utf-8-sig') as f:
    #             reader = csv.reader(f)
    #             headers = next(reader)
    #             headers = [h.strip('\ufeff') for h in headers]
    #
    #             # Make sure timestamp column exists
    #             if len(headers) < 1 or headers[0] != TIMESTAMP:
    #                 return False
    #
    #             timestamps = []
    #             data = {header: [] for header in headers[1:]}
    #
    #             for row in reader:
    #                 if len(row) != len(headers):
    #                     continue
    #
    #                 try:
    #                     timestamp = datetime.strptime(row[0], FORMAT_TIMESTAMP)
    #                     timestamps.append(timestamp)
    #                     for header, value in zip(headers[1:], row[1:]):
    #                         data[header].append(float(value))
    #                 except (ValueError, IndexError):
    #                     continue
    #
    #             # Timestamps not valid
    #             if not timestamps:
    #                 return False
    #
    #             # Manage timestamps
    #             first_ts = timestamps[0]
    #             self.replay_relative_times = [(ts - first_ts).total_seconds() for ts in timestamps]
    #
    #             # Store all data (no truncation)
    #             for header in headers[1:]:
    #                 self.replay_data[header] = data[header]
    #
    #             # Extract channel info
    #             for header in headers[1:]:
    #                 # Extract unit from header (supports "Channel (V)" or "Channel V")
    #                 unit = ""
    #                 if '(' in header and ')' in header:
    #                     # Handle parentheses format: "Channel (Unit)"
    #                     unit = header.split('(')[-1].split(')')[0].strip()
    #                 else:
    #                     # Handle space-separated format: "Channel Unit"
    #                     parts = header.split()
    #                     unit = parts[-1] if len(parts) > 1 else ''
    #
    #                 channel_type = UNIT_TYPE_MAP.get(unit, CHANNEL_TYPE_VOLTAGE)  # Use voltage as default
    #                 self.channel_info[header] = {'unit': unit, 'type': channel_type}
    #
    #             return True
    #     except Exception as e:
    #         print(f"Error loading CSV: {str(e)}")
#         return False


