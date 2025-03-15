import sys
from PyQt5.QtWidgets import QApplication
from model import DataModel
from view import MainWindowView
from controller import MainController

def main():
    # Create the application
    app = QApplication(sys.argv)

    # Create the MVC components
    model = DataModel()
    view = MainWindowView()
    controller = MainController(model, view)

    # Show the main window
    view.show()

    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()