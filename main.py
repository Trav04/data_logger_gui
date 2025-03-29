import sys
import time


from PyQt5.QtWidgets import QApplication
from model import DataModel
from serial_manager import SerialManager
from serial_send_receive_manager import SerialSendReceiveManager
from view import MainWindowView
from controller import MainController

from model import CHANNEL_TYPE_VOLTAGE
from model import CHANNEL_TYPE_TEMPERATURE
from model import CHANNEL_TYPE_ACCELERATION
from model import CHANNEL_TYPE_RESISTIVE_TEMPERATURE

def main():
    # Create the application
    app = QApplication(sys.argv)

    # Create the MVC components
    model = DataModel()
    view = MainWindowView()
    model.initialize_channel_config(1, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(2, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(3, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(4, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(5, CHANNEL_TYPE_ACCELERATION)
    model.initialize_channel_config(6, CHANNEL_TYPE_ACCELERATION)
    model.initialize_channel_config(7, CHANNEL_TYPE_ACCELERATION)
    model.initialize_channel_config(8, CHANNEL_TYPE_TEMPERATURE)

    controller = MainController(model, view)

    rtc_struct_id = 0x01
    year = 2024
    month = 3
    day = 26
    hour = 15
    minute = 48
    second = 32

    # Send the RTC struct

    ## Initiate PC communication signal thread
    serial = SerialSendReceiveManager()
    serial.start_heartbeat()

    # success = serial._send_struct_ack_wait(rtc_struct_id, rtc_struct_id, year, month, day, hour, minute, second)
    # print(success)
    view.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()