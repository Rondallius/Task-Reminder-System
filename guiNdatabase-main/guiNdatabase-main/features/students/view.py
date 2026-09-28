from PyQt6.QtWidgets import *

from .model import Student
from .service import StudentService

class StudentView(QWidget):
    def __init__(self, service: StudentService):
        super().__init__()
        self.service = service
        self.setWindowTitle("Student Management")
        self.resize(600, 400)
        self.build_ui()
        self.refresh()

    def build_ui(self) -> None:
        layout = QVBoxLayout()

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()

        form.addRow("Name", self.name_input)
        form.addRow("Email", self.email_input)
        layout.addLayout(form)

        add_button = QPushButton("Add Student")
        add_button.clicked.connect(self.add_student)
        layout.addWidget(add_button)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Email"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def add_student(self) -> None:
        try:
            student = Student(self.name_input.text(), self.email_input.text())
            self.service.add_student(student)
        except ValueError as error:
            QMessageBox.warning(self, "Invalid Student", str(error))
            return

        self.name_input.clear()
        self.email_input.clear()
        self.refresh()

    def refresh(self) -> None:
        students = self.service.get_students()
        self.table.setRowCount(len(students))

        for row, student in enumerate(students):
            values = [student.id, student.name, student.email]
            for column, value in enumerate(values):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value))
                )
