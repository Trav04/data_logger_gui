import sys
from PyQt5.QtWidgets import QApplication
from model import DataModel
from view import MainWindowView
from controller import MainController
from pprint import pprint

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
    controller = MainController(model, view)
    model.initialize_channel_config(1, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(2, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(3, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(4, CHANNEL_TYPE_VOLTAGE)
    model.initialize_channel_config(5, CHANNEL_TYPE_ACCELERATION)
    model.initialize_channel_config(6, CHANNEL_TYPE_ACCELERATION)
    model.initialize_channel_config(7, CHANNEL_TYPE_ACCELERATION)
    model.initialize_channel_config(8, CHANNEL_TYPE_TEMPERATURE)

    pprint(model.channel_configs)
    # Show the main window
    view.show()

    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()