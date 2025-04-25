# main.py

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

    recorded_struct_id = 0x05
    recording_state = 1#0x01

    config_id = 0x03
    channel_type = 0x56
    channel_id = 0x01
    input_range = 0x10
    alarm_type = 0x01
    alarm_state = 0x01
    alarm_occurring = 0x01
    resistive_temp = 0x00
    current_source = 0x00
    sensor_type = 0x00

    # Send the RTC struct

    ## Initiate PC communication signal thread




    # success = serial._send_struct_ack_wait(rtc_struct_id, rtc_struct_id, (2025 >> 8) & 0xFF, 2025 & 0xFF, month, day, hour, minute, second)
    #success = serial._send_struct_ack_wait(recorded_struct_id, recorded_struct_id, recording_state)
    # success = serial._send_struct_ack_wait(config_id, config_id, channel_type, channel_id, input_range, alarm_type, alarm_state, alarm_occurring, resistive_temp, current_source, sensor_type)
    # print(success)

    
    #while(1):
        #success = serial._send_struct_ack_wait(rtc_struct_id, rtc_struct_id, year, month, day, hour, minute, second)
        #success = serial._send_struct_ack_wait(recorded_struct_id, recorded_struct_id, recording_state)
        #print(success)

        #time.sleep(1)

        #success = serial._send_struct_ack_wait(recorded_struct_id, recorded_struct_id, recording_state)
        #print(success)

        #time.sleep(1)
    

    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()