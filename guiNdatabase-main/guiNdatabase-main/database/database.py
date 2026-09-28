import sqlite3
from pathlib import Path

class Database:
    def __init__(self, database_path: str | Path = "school.db"):
        self.database_path = Path(database_path)

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def create_table(self) -> None:
        with self.connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL
                )
                """
            )