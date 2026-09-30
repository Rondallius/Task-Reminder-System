"""
service.py  -  the rules between the window and the database.

    MainWindow  ->  TaskService  ->  TaskDatabase  ->  tasks.db

The window asks the service for something, the service checks the data and
calls the database. SQLite problems are turned into one simple error type
(TaskServiceError) whose text can be shown in a QMessageBox.
"""

import sqlite3
from datetime import datetime

from features.task import CompletedTask, Task, parse_duration, task_from_row


class TaskServiceError(Exception):
    """A problem that the user should see as a message box."""


class TaskService:
    """Everything the program does with tasks: add, list, complete, delete."""

    def __init__(self, database):
        self.database = database

    # ---------------- check the data typed in the Add Task dialog ----------
    def validate_new_task(self, name, description, reminder_text):
        """Returns a ready to save Task object.

        Raises TaskServiceError (no name) or ValueError (bad reminder time).
        """
        if name is None or name.strip() == "":
            raise TaskServiceError("Please type a task name.")
        seconds = parse_duration(reminder_text)          # raises ValueError
        return Task(name=name.strip(), description=(description or "").strip(),
                    reminder_seconds=seconds)

    # ---------------- CREATE ----------------
    def add_task(self, task):
        """INSERT the task and keep the id that SQLite gave it."""
        task.status = Task.STATUS
        task.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            task.task_id = self.database.insert_task(task)
        except sqlite3.Error as error:
            raise TaskServiceError(f"Database error while saving: {error}")
        return task

    # ---------------- READ ----------------
    def get_tasks(self):
        """SELECT all tasks and turn the rows into Task objects."""
        try:
            rows = self.database.fetch_all_tasks()
        except sqlite3.Error as error:
            raise TaskServiceError(f"Database error while reading: {error}")
        return [task_from_row(row) for row in rows]

    # ---------------- UPDATE ----------------
    def mark_complete(self, task):
        """UPDATE one task to the status 'Completed'."""
        try:
            self.database.update_status(task.task_id, CompletedTask.STATUS)
        except sqlite3.Error as error:
            raise TaskServiceError(f"Database error while updating: {error}")
        task.status = CompletedTask.STATUS

    def complete_all_pending_tasks(self):
        """UPDATE every task that is still pending to 'Completed'.

        This is used when the user closes the program and answers 'Yes'.
        """
        try:
            self.database.complete_all_pending()
        except sqlite3.Error as error:
            raise TaskServiceError(f"Database error while updating: {error}")

    # ---------------- DELETE ----------------
    def delete_task(self, task):
        """DELETE one task from the database."""
        try:
            self.database.delete_task(task.task_id)
        except sqlite3.Error as error:
            raise TaskServiceError(f"Database error while deleting: {error}")
