"""
main.py  -  the entry point of the program.

It only starts things up. The real work is done by the classes it builds:

    TaskDatabase  ->  TaskService  ->  QApplication  ->  MainWindow  ->  loop
"""

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from database.database import TaskDatabase
from features.service import TaskService
from features.view import MainWindow

STYLE_FILE = Path(__file__).with_name("style.qss")


def main():
    """Creates the database, the service, the window and the Qt event loop."""
    database = TaskDatabase()          # creates tasks.db and the tasks table
    service = TaskService(database)    # the rules that work with that database

    app = QApplication(sys.argv)

    # The look of the program lives in style.qss, not inside the Python code.
    if STYLE_FILE.exists():
        app.setStyleSheet(STYLE_FILE.read_text(encoding="utf-8"))

    window = MainWindow(service)
    window.show()
    return app.exec_()                 # starts the Qt event loop


if __name__ == "__main__":
    sys.exit(main())
