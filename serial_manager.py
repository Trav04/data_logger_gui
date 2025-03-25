import serial
import struct
import threading
import time

from serial_receive_manager import SerialReceiveManager
from serial_send_manager import SerialSendManager


class SerialManager:

    def __init__(self, port='COM10', baudrate=115200):
        self._port = port
        self._baudrate = baudrate
        self._ser = None
        self.lock = threading.Lock()
        self._connect_serial()
        self.reconnect_thread = threading.Thread(target=self._reconnect_serial, daemon=True)
        self.reconnect_thread.start()

    def _connect_serial(self):
        """Attempt to connect to the serial port."""
        try:
            self._ser = serial.Serial(self._port, self._baudrate, timeout=1)
            print(f"Connected to {self._port}")
        except serial.SerialException as e:
            print(f"Failed to connect to {self._port}: {e}")
            self._ser = None

    def _reconnect_serial(self):
        """Continuously attempts to reconnect if the serial port is disconnected."""
        while True:
            if self._ser is None or not self._ser.is_open:
                self._close()
                print("Attempting to reconnect...")
                self._connect_serial()
            time.sleep(0.5)  # Retry every 2 seconds
