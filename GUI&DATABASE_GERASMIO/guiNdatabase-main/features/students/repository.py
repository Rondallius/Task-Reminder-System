from database.database import Database
from .model import Student

class StudentRepository:
    def __init__(self, database: Database):
        self.database = database

    def add(self, student: Student) -> Student:
        with self.database.connect() as con:
            cursor = con.execute(
                "INSERT INTO students (name, email) VALUES (?, ?)",
                (student.name, student.email)
            )
            student.id = cursor.lastrowid
        return student

    def list(self) -> list[Student]:
        with self.database.connect() as con:
            rows = con.execute("SELECT id, name, email FROM students").fetchall()
        return [Student(id=row[0], name=row[1], email=row[2]) for row in rows]