import sys

from PyQt6.QtWidgets import QApplication

from database.database import Database
from features.students.service import StudentService
from features.students.view import StudentView

def main() -> int:
    database = Database()
    database.create_table()


    app = QApplication(sys.argv)
    service = StudentService(database)
    window = StudentView(service)
    window.show()

    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
