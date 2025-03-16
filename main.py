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

    # # Sample data rows matching the provided CSV example:
    # # (Timestamp, [CH1, CH2, CH3, CH4, CH5, CH6, CH7, CH8])
    # sample_data = [
    #     ("2025-03-08_12-30-15.123", [3.45, 2.78, 25.6, 4.12, 0.12, -0.05, 0.08, 26]),
    #     ("2025-03-08_12-30-16.456", [3.46, 2.79, 25.7, 4.11, 0.14, -0.07, 0.09, 26.1]),
    #     ("2025-03-08_12-30-17.789", [3.44, 2.77, 25.5, 4.1, 0.11, -0.04, 0.07, 25.9]),
    #     ("2025-03-08_12-30-19.012", [3.47, 2.8, 25.8, 4.13, 0.15, -0.06, 0.1, 26.2]),
    #     ("2025-03-08_12-30-20.345", [3.43, 2.76, 25.4, 4.09, 0.1, -0.03, 0.06, 25.8]),
    #     ("2025-03-08_12-30-21.678", [3.48, 2.81, 25.9, 4.14, 0.16, -0.08, 0.12, 26.3]),
    #     ("2025-03-08_12-30-23.001", [3.42, 2.75, 25.3, 4.08, 0.09, -0.02, 0.05, 25.7]),
    #     ("2025-03-08_12-30-24.334", [3.49, 2.82, 26.0, 4.15, 0.17, -0.09, 0.13, 26.4]),
    #     ("2025-03-08_12-30-25.667", [3.41, 2.74, 25.2, 4.07, 0.08, -0.01, 0.04, 25.6]),
    #     ("2025-03-08_12-30-27.000", [3.5, 2.83, 26.1, 4.16, 0.18, -0.1, 0.14, 26.5]),
    #     ("2025-03-08_12-30-28.333", [3.4, 2.73, 25.1, 4.06, 0.07, 0.0, 0.03, 25.5])
    # ]
    #
    # # Create an instance of DataModel
    # model = DataModel()
    #
    # # Simulate storing live data as if the data were arriving from a device
    # for ts, values in sample_data:
    #     model.store_live_data(ts, values)
    #
    #     # Print the current state after adding the new data point.
    #     print("After adding data point:")
    #     print("Relative Times (s):", model.live_relative_times)
    #     for ch in sorted(model.live_data.keys()):
    #         print(f"Channel {ch}: {model.live_data[ch]}")
    #     print("----------\n")
    # # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()