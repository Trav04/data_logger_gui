import serial
import struct
import threading
import time

from serial_comms import STRUCT_FORMATS
from serial_manager import SerialManager

class SerialSendReceiveManager(SerialManager):
    """ Class that handles the receiving of data """
    HEARTBEAT = "heartbeat"
    RTC_TIME = "rtc_time"
    CHANNEL_LIVE_DATA = "channel_live_data"
    CHANNEL_CONFIG = "channel_config"
    OPTIC_CONNECTION = "optic_connection"
    DEVICE_RECORDING_STATE = "device_recording_state"

    HEARTBEAT_BEAT = 0x06  # Heartbeat signal

    STRUCT_FORMATS = {
        HEARTBEAT: "B",  # uint8_t beat = 0x06
        RTC_TIME: "B H 5B",  # struct_id (uint8), year (uint16), month, day, hour, min, sec (5x uint8)
        CHANNEL_LIVE_DATA: "B B H 5B 8B",  # struct_id (uint8), rtc_struct, 8x uint8 channels
        CHANNEL_CONFIG: "B 7B",  # struct_id (uint8), 7x uint8_t values
        OPTIC_CONNECTION: "B B",  # struct_id (uint8), recording_state (uint8)
        DEVICE_RECORDING_STATE: "B B"  # struct_id (uint8), optic_state (uint8)
    }


    def __init__(self):
        super().__init__()
        self._start_receive_struct_thread()

    #### SENDING DATA ####

    def _send_struct(self, struct_type, *data):
        if struct_type not in self.STRUCT_FORMATS:
            print(f"Error: Unknown struct type {struct_type}")
            return False

        fmt = self.STRUCT_FORMATS[struct_type]
        try:
            packed_data = struct.pack(fmt, *data)
            with self.lock:
                if self._ser and self._ser.is_open:
                    self._ser.write(packed_data)
                    self._ser.flush()
                    return True
                else:
                    print("Serial port not available.")
                    self._close()
                    return False
        except struct.error as e:
            print(f"Error packing data for struct type {struct_type}: {e}")
            self._close()
            return False
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            self._close()
            return False

    def _send_heartbeat(self):
        self._send_struct(self.HEARTBEAT, self.HEARTBEAT_BEAT)

    def _heartbeat_timer(self):
        """ Starts the heart beat thread to periodically send heart beat signals to the device"""
        self._send_heartbeat()
        heartbeat = threading.Timer(0.5, self._heartbeat_timer)
        heartbeat.daemon = True  # Set as daemon thread (exit when main thread exits)
        heartbeat.start()

    def _close(self):
        """Close the serial connection safely."""
        if self._ser and self._ser.is_open:
            self._ser.close()
            print("Serial connection closed.")

    def _send_acknowledgement_packet(self, struct_id: str):
        """ Sends an acknowledgement for the given struct type """
        if self._ser and self._ser.is_open:
            self._ser.write(f";A{struct_id}")

    def start_heartbeat(self):
        """ Starts the heartbeat """
        self._heartbeat_timer()

    #### RECEIVING AND PROCESSING DATA ####

    def _parse_channel_live_data(self, unpacked_data: tuple):
        pass

    STRUCT_PARSERS = {
        0x01: _parse_channel_live_data,

    }

    def _receive_structs(self):
        """ Start a thread for receiving structs """
        while True:
            struct_id = self._ser.read(1)[0]  # Extract the struct id from the first byte

            if struct_id in self.STRUCT_PARSERS:
                # Send ACK
                self._send_acknowledgement_packet(struct_id)

                struct_format = STRUCT_FORMATS[struct_id]
                struct_size = struct.calcsize(struct_format)

                struct_data = self._ser.read(struct_size - 1)  # -1 as struct ID (1 byte) already read

                if len(struct_data) != struct_size - 1:
                    print("RECEIVE ERROR: Incomplete data received!")
                    continue  # Fail gracefully and skip this data

                # Unpack the data into a tuple (excluding the struct_id)
                unpacked_data = struct.unpack(struct_format, struct_data)

                # Parse data
                self.STRUCT_PARSERS[struct_id](unpacked_data)

    def _start_receive_struct_thread(self):
        """ Starts the receiving struct thread """
        receive_thread = threading.Thread(target=self._receive_structs, daemon=True)
        receive_thread.start()