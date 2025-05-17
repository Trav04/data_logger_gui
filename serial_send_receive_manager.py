# SerialSendReceiveManager.py

import serial
import struct
import threading
import time
from datetime import datetime

from serial_manager import SerialManager

from model import CHANNEL_TYPE_VOLTAGE, INPUT_RANGE, INPUT_RANGE_10V, INPUT_RANGE_1V, ALARM_TYPE, ALARM_STATE, \
    TEMP_ENABLED, CURRENT_SOURCE, SENSOR_TYPE, ALARM_HIGH, ALARM_LOW, CHANNEL_TYPE

class SerialSendReceiveManager(SerialManager):

    """ Class that handles the receiving of data """
    STRUCT_ID_HEARTBEAT = 0x06
    STRUCT_ID_RTC_TIME = 0x01
    STRUCT_ID_CHANNEL_LIVE_DATA = 0x02
    STRUCT_ID_CHANNEL_CONFIG = 0x03
    STRUCT_ID_OPTIC_CONNECTION = 0x04
    STRUCT_ID_DEVICE_RECORDING_STATE = 0x05

    ACKNOWLEDGEMENT_PREFIX = ";A"

    HEARTBEAT_BEAT_VALUE = 0x06

    STRUCT_FORMATS = {
        STRUCT_ID_HEARTBEAT: "B",  # uint8_t beat = 0x00                                                                  # SEND TO Control Unit
        STRUCT_ID_RTC_TIME: "B B B 5B",  # struct_id (uint8), year (uint16), month, day, hour, min, sec (5x uint8)          # SEND to Control Unit
        STRUCT_ID_CHANNEL_LIVE_DATA: "B B B 5B 9h",  # struct_id (uint8), rtc_struct, 8x uint16 channels                  # Receive from Control Unit
        STRUCT_ID_OPTIC_CONNECTION: "B B",  # struct_id (uint8), recording_state (uint8)                                  # Receive from Control Unit
        STRUCT_ID_CHANNEL_CONFIG: "B 8B h h",  # struct_id (uint8), 7x uint8_t values                                     # Send & Receive from Control Unit
        STRUCT_ID_DEVICE_RECORDING_STATE: "B B"  # struct_id (uint8), optic_state (uint8)                                 # Send & Receive from Control Unit
    }

    def __init__(self, controller):
        super().__init__()
        self.STRUCT_PARSERS = {
            0x02: self._parse_channel_live_data,
            0x03: self._parse_channel_config,
            0x04: self._parse_optic_connection,
            0x05: self._parse_device_recording_state
        }
        self._controller = controller
        self._start_receive_struct_thread()
        self.count = 0

    #### SENDING DATA ####

    def send_struct_no_ack(self, struct_id, *args):
        """
        Send struct over serial with no acknowledgement wait
        :param struct_id: the id of the struct being sent
        :param args: the arguments sent in that struct of the specified ID
        :return: True if the args are sent, false otherwise
        """
        time.sleep(0.5)
        if struct_id not in self.STRUCT_FORMATS:
            print(f"Error: Unknown struct type {struct_id}")
            return False

        fmt = self.STRUCT_FORMATS[struct_id]
        try:
            packed_data = bytearray(struct.pack(fmt, *args))

            with self.lock:
                if self._ser and self._ser.is_open:
                    self._ser.write(packed_data)
                    print(f"Sending {struct_id}: {packed_data}")
                    self.count = 1 - self.count
                    self._ser.flush()
                    return True
                else:
                    print("Serial port not available.")
                    self._close()
                    return False
        except struct.error as e:
            print(f"Error packing data for struct type {struct_id}: {e}")
            self._close()
            return False
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            self._close()
            return False

    def send_struct_ack_wait(self, struct_id, *args, ack_timeout=2.0) -> bool:
        """
        Send a struct and await an acknowledgement back
        :param struct_id: the ID of the struct to be sent
        :param args: the parameters of that struct to be sent
        :param ack_timeout: (optional) the duration that should be waited for the ack packet
        :return: True if struct sent and ack received, false otherwise
        """
        if struct_id not in self.STRUCT_FORMATS:
            print(f"Error: Unknown struct type {struct_id}")
            return False

        fmt = self.STRUCT_FORMATS[struct_id]

        try:
            packed_data = struct.pack(fmt, *args)
            ack_expected = b";A" + struct.pack("B", struct_id)  # Expected ACK packet

            with self.lock:
                if self._ser and self._ser.is_open:
                    # Send the packed struct data
                    self._ser.write(packed_data)
                    self._ser.flush()

                    # Wait for ACK response
                    start_time = time.time()
                    ack_received = b""

                    while time.time() - start_time < ack_timeout:
                        ack_received += self._ser.read(1)  # Read one byte at a time

                        # Check if ACK string is in received data
                        if ack_expected in ack_received:
                            return True
                    
                    print(f"ACK Timeout: Expected {ack_expected}, but got {ack_received}")
                    return False
                else:
                    print("Serial port not available.")
                    self._close()
                    return False

        except struct.error as e:
            print(f"Error packing data for struct type {struct_id}: {e}")
            self._close()
            return False
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            self._close()
            return False

    def _close(self):
        """Close the serial connection safely."""
        if self._ser and self._ser.is_open:
            self._ser.close()
            print("Serial connection closed.")

    def _send_acknowledgement_packet(self, struct_id: str):
        """ Sends an acknowledgement for the given struct type """
        if self._ser and self._ser.is_open:
            ack_packet = b";A" + struct.pack("B", struct_id)
            self._ser.write(ack_packet)

    def _send_heartbeat(self):
        self.send_struct_no_ack(self.STRUCT_ID_HEARTBEAT, self.HEARTBEAT_BEAT_VALUE)

    def start_heartbeat(self):
        """ Starts the heart beat thread to periodically send heart beat signals to the device"""
        self._send_heartbeat()
        heartbeat = threading.Timer(0.5, self.start_heartbeat)
        heartbeat.daemon = True  # Set as daemon thread (exit when main thread exits)
        heartbeat.start()

    #### RECEIVING AND PROCESSING DATA ####

    def _parse_channel_live_data(self, unpacked_data: tuple):
        print("Channel Live Data Received:", unpacked_data)
        timestamp = datetime((unpacked_data[2]<<8) | unpacked_data[3], unpacked_data[4], unpacked_data[5], unpacked_data[6], unpacked_data[7], unpacked_data[8])
        self._controller.update_live_channel_data(timestamp, unpacked_data[9] / 1000, unpacked_data[10] / 1000, unpacked_data[11] / 1000, unpacked_data[12] / 1000, unpacked_data[13] / 1000, unpacked_data[14] / 1000, unpacked_data[15] / 1000, unpacked_data[16] / 1000)
        # Update the model's data structure

    def _parse_device_recording_state(self, unpacked_data: tuple):
        print("Recording State Received:", unpacked_data)
        struct_id, recording_state = unpacked_data
        self._controller.view_start_stop_recording()

    def _parse_optic_connection(self, unpacked_data: tuple):
        print("Optic channel Data Received:", unpacked_data)
        # self._controller.view_set_optical_state(unpacked_data[1])

    def _parse_channel_config(self, unpacked_data: tuple):
        print("Channel Config Received:", unpacked_data)
        self._controller.update_channel_config(unpacked_data[1], unpacked_data[2], unpacked_data[3],
                                               unpacked_data[4], unpacked_data[5], unpacked_data[6],
                                               unpacked_data[7], unpacked_data[8], unpacked_data[9], unpacked_data[10])

    def _receive_structs(self):
        """ Polls for receiving data from the control unit """
        while True:
            try:
                if not self._ser or not self._ser.is_open:
                    time.sleep(1)  # Avoid tight loop if port is closed
                    continue

                # Use select with a timeout to prevent blocking indefinitely
                if self._ser.in_waiting > 0:
                    struct_id = self._ser.read(1)[0]  # Extract the struct id from the first byte

                    if struct_id in self.STRUCT_PARSERS:
                        # Send ACK
                        # self._send_acknowledgement_packet(struct_id)

                        struct_format = self.STRUCT_FORMATS[struct_id]
                        struct_size = struct.calcsize(struct_format)  # size includes the struct id

                        struct_data = self._ser.read(struct_size - 1)  # -1 as struct ID (1 byte) already read
                        print("Struct ID", struct_id)
                        print("Struct Data", struct_data)

                        if len(struct_data) != (struct_size - 1):
                            print("RECEIVE ERROR: Incomplete data received!")
                            continue  # Fail gracefully and skip this data

                        # Unpack the data into a tuple (excluding the struct_id)
                        unpacked_data = struct.unpack(struct_format, bytes([struct_id]) + struct_data)

                        # Parse data
                        self.STRUCT_PARSERS[struct_id](unpacked_data)
                    else:
                        time.sleep(0.01)  # Short sleep to prevent CPU spinning
                else:
                    time.sleep(0.01)  # Short sleep when no data is available
            except (serial.SerialException, OSError) as e:
                print(f"Serial communication error: {e}")
                self._close()
                time.sleep(1)  # Prevent tight error loop
            except Exception as e:
                print(f"Unexpected error in receive thread: {e}")
                time.sleep(1)

    def _start_receive_struct_thread(self):
        """ Starts the receiving struct thread """
        receive_thread = threading.Thread(target=self._receive_structs, daemon=True)
        receive_thread.start()

    def send_rtc_time(self):
        """Calculate the current time and send it to the Control unit"""
        now = datetime.now()
        self.send_struct_no_ack(
            self.STRUCT_ID_RTC_TIME,
            self.STRUCT_ID_RTC_TIME,
            (now.year >> 8) & 0xFF,
            now.year & 0xFF,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second
        )

    def send_channel_config(self, channel):
        """Gets all of the updated channel config parameters and sends them to the Control Unit"""
        config_id = 0x03
        channel_type = self._controller.model.get_channel_config_param(channel, CHANNEL_TYPE)
        channel_id = channel
        input_range = self._controller.model.get_channel_config_param(channel, INPUT_RANGE)
        alarm_type = self._controller.model.get_channel_config_param(channel, ALARM_TYPE)
        alarm_state = self._controller.model.get_channel_config_param(channel, ALARM_STATE)
        resistive_temp = self._controller.model.get_channel_config_param(channel, TEMP_ENABLED)
        current_source = self._controller.model.get_channel_config_param(channel, CURRENT_SOURCE)
        sensor_type = self._controller.model.get_channel_config_param(channel, SENSOR_TYPE)
        alarm_high = self._controller.model.get_channel_config_param(channel, ALARM_HIGH)
        alarm_low = self._controller.model.get_channel_config_param(channel, ALARM_LOW)

        print(config_id, config_id, channel_id, channel_type, input_range, alarm_type, alarm_state, resistive_temp,
              current_source, sensor_type, int(alarm_high), int(alarm_low))
        self.send_struct_no_ack(config_id, config_id, channel_id, channel_type, input_range, alarm_type,
                                       alarm_state, resistive_temp, current_source, sensor_type, int(alarm_high),
                                       int(alarm_low))

    def send_recording_status(self, recording_state):
        self.send_struct_no_ack(self.STRUCT_ID_DEVICE_RECORDING_STATE,self.STRUCT_ID_DEVICE_RECORDING_STATE, recording_state)
