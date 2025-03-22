import serial
import struct
import threading
import time

class SerialManager:
    HEARTBEAT = "heartbeat"
    RTC_TIME = "rtc_time"
    CHANNEL_LIVE_DATA = "channel_live_data"
    CHANNEL_CONFIG = "channel_config"
    OPTIC_CONNECTION = "optic_connection"
    DEVICE_RECORDING_STATE = "device_recording_state"

    HEARTBEAT_BEAT = 0x06

    STRUCT_FORMATS = {
        HEARTBEAT: "B",  # uint8_t beat = 0x00
        RTC_TIME: "B H 5B",  # struct_id (uint8), year (uint16), month, day, hour, min, sec (5x uint8)
        CHANNEL_LIVE_DATA: "B B H 5B 8B",  # struct_id (uint8), rtc_struct, 8x uint8 channels
        CHANNEL_CONFIG: "B 7B",  # struct_id (uint8), 7x uint8_t values
        OPTIC_CONNECTION: "B B",  # struct_id (uint8), recording_state (uint8)
        DEVICE_RECORDING_STATE: "B B"  # struct_id (uint8), optic_state (uint8)
    }

    def __init__(self, port='COM10', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.lock = threading.Lock()
        self.connect_serial()
        self.reconnect_thread = threading.Thread(target=self.reconnect_serial, daemon=True)
        self.reconnect_thread.start()

    def connect_serial(self):
        """Attempt to connect to the serial port."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"Connected to {self.port}")
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            self.ser = None

    def reconnect_serial(self):
        """Continuously attempts to reconnect if the serial port is disconnected."""
        while True:
            if self.ser is None or not self.ser.is_open:
                self.close()
                print("Attempting to reconnect...")
                self.connect_serial()
            time.sleep(0.5)  # Retry every 2 seconds

    def send_struct(self, struct_type, *data):
        if struct_type not in self.STRUCT_FORMATS:
            print(f"Error: Unknown struct type {struct_type}")
            return False

        fmt = self.STRUCT_FORMATS[struct_type]
        try:
            packed_data = struct.pack(fmt, *data)
            with self.lock:
                if self.ser and self.ser.is_open:
                    self.ser.write(packed_data)
                    self.ser.flush()
                    return True
                else:
                    print("Serial port not available.")
                    self.close()
                    return False
        except struct.error as e:
            print(f"Error packing data for struct type {struct_type}: {e}")
            self.close()
            return False
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            self.close()
            return False

    def send_heartbeat(self):
        self.send_struct(self.HEARTBEAT, self.HEARTBEAT_BEAT)

    def heartbeat_timer(self):
        self.send_heartbeat()
        threading.Timer(0.5, self.heartbeat_timer).start()

    def start_heartbeat(self):
        self.heartbeat_timer()

    def close(self):
        """Close the serial connection safely."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial connection closed.")
