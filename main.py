import sys
import time

from PyQt5.QtWidgets import QApplication
from model import DataModel, INPUT_RANGE_10V, ALARM_TYPE_DISABLED, ALARM_NOT_OCCURRING, RESISTIVE_TEMP_ENABLED, \
    CURRENT_SOURCE, TEMP_SENSOR_THERMISTOR
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

    # Create the controller
    controller = MainController(model, view)

    controller.update_channel_config(2, CHANNEL_TYPE_VOLTAGE,INPUT_RANGE_10V, ALARM_TYPE_DISABLED, ALARM_NOT_OCCURRING, RESISTIVE_TEMP_ENABLED, CURRENT_SOURCE, TEMP_SENSOR_THERMISTOR, 1, 0)
    controller.update_channel_config(1, CHANNEL_TYPE_VOLTAGE,INPUT_RANGE_10V, ALARM_TYPE_DISABLED, ALARM_NOT_OCCURRING, RESISTIVE_TEMP_ENABLED, CURRENT_SOURCE, TEMP_SENSOR_THERMISTOR, 1, 0)


    # Show the GUI
    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()