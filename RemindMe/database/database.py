"""
database.py  -  the only place in the program that talks to SQLite.

TaskDatabase creates the file and the tasks table, and it runs every SQL
statement. Every statement that uses text from the user works with "?"
placeholders, so what the user typed is never glued into a query.
"""

import sqlite3
from pathlib import Path

# tasks.db always sits next to main.py, no matter from which folder the
# program was started.
DATABASE_FILE = Path(__file__).resolve().parent.parent / "tasks.db"


class TaskDatabase:
    """Saves the tasks in a SQLite file: INSERT, SELECT, UPDATE, DELETE."""

    def __init__(self, database_file=DATABASE_FILE):
        self.database_file = database_file
        self.create_table()

    # ------------------------------------------------------------------
    def connect(self):
        """Opens a connection to the SQLite file."""
        return sqlite3.connect(self.database_file)

    # ------------------------------------------------------------------
    def create_table(self):
        """CREATE TABLE - makes the file and the table when they are missing."""
        sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT    NOT NULL,
            description      TEXT,
            reminder_seconds INTEGER NOT NULL,
            created_at       TEXT    NOT NULL,
            status           TEXT    NOT NULL
        )
        """
        connection = self.connect()
        try:
            connection.execute(sql)
            connection.commit()
        finally:
            connection.close()

    # ------------------------------------------------------------------
    def insert_task(self, task):
        """INSERT - saves one new task and returns the id SQLite gave it."""
        sql = ("INSERT INTO tasks "
               "(name, description, reminder_seconds, created_at, status) "
               "VALUES (?, ?, ?, ?, ?)")
        values = (task.name, task.description, task.reminder_seconds,
                  task.created_at, task.status)
        connection = self.connect()
        try:
            cursor = connection.cursor()
            cursor.execute(sql, values)
            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()

    # ------------------------------------------------------------------
    def fetch_all_tasks(self):
        """SELECT - returns every row of the table as a list of tuples."""
        sql = ("SELECT id, name, description, reminder_seconds, created_at, "
               "status FROM tasks ORDER BY id")
        connection = self.connect()
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            connection.close()

    # ------------------------------------------------------------------
    def update_status(self, task_id, status):
        """UPDATE - changes the status of one single task."""
        sql = "UPDATE tasks SET status = ? WHERE id = ?"
        connection = self.connect()
        try:
            connection.execute(sql, (status, task_id))
            connection.commit()
        finally:
            connection.close()

    # ------------------------------------------------------------------
    def complete_all_pending(self):
        """UPDATE - one statement that finishes every pending task.

        It is used when the user closes the program and answers "Yes".
        The two status words are the same as Task.STATUS and
        CompletedTask.STATUS in features/task.py. This statement needs no "?"
        placeholders, because the text comes from the program and not from a
        user, so nothing can be injected into it.
        """
        sql = "UPDATE tasks SET status = 'Completed' WHERE status = 'Pending'"
        connection = self.connect()
        try:
            connection.execute(sql)
            connection.commit()
        finally:
            connection.close()

    # ------------------------------------------------------------------
    def delete_task(self, task_id):
        """DELETE - removes one task from the table."""
        sql = "DELETE FROM tasks WHERE id = ?"
        connection = self.connect()
        try:
            connection.execute(sql, (task_id,))
            connection.commit()
        finally:
            connection.close()
