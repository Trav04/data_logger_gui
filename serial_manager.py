import serial
import threading
import time


class SerialManager:

    def __init__(self, port='COM10', baudrate=115200): # Was 10 for Travis' computer.
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

    def set_port(self, port: str):
        """Sets the serial port, reconnecting if already connected."""
        try:
            # Disconnect if already connected
            if hasattr(self, '_serial') and self._serial.is_open:
                print(f"Closing current port: {self._serial.port}")
                self._ser.close()

            # Set new port
            self._port = port
            print(f"Setting new port: {port}")

            # Create and open new serial connection
            self._ser = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
            )

            if self._ser.is_open:
                print(f"Connected to {self._port}")
            else:
                print(f"Failed to open {self._port}")

        except serial.SerialException as e:
            print(f"Serial error: {e}")

