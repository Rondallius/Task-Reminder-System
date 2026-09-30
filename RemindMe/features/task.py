"""
task.py  -  the model of the program.

Task keeps the data of one task and the few rules that belong to that data.
CompletedTask is a normal Task, but it answers three methods differently
(inheritance and polymorphism, see the class comments below).

The plain functions at the bottom belong to the "HH:MM:SS" reminder text.
They are normal functions and not methods, so nothing complicated is needed.
"""


class Task:
    """One task of the list. status is 'Pending' while it is not finished."""

    STATUS = "Pending"

    def __init__(self, name, description="", reminder_seconds=0,
                 task_id=None, created_at="", status=STATUS):
        self.task_id = task_id                    # None until it is saved
        self.name = name
        self.description = description
        self.reminder_seconds = reminder_seconds  # length of the reminder
        self.created_at = created_at              # text, filled in by TaskService
        self.status = status

    # ---------------- the three methods CompletedTask answers differently ----
    def status_label(self):
        """Text for the Status column of the table."""
        return "Pending"

    def countdown_seconds(self):
        """How many seconds this task counts down."""
        return self.reminder_seconds

    def alarm_message(self):
        """Text of the reminder popup when the countdown reaches zero."""
        return f"\U0001F514 Reminder: {self.name} - Time is up!"

    # ---------------- small helpers that use the stored data ----------------
    def reminder_text(self):
        """The reminder time as 'HH:MM:SS' text, for example '00:05:30'."""
        return seconds_to_text(self.reminder_seconds)

    def is_completed(self):
        """True when the user already marked this task as completed."""
        return self.status == CompletedTask.STATUS


class CompletedTask(Task):
    """A task the user has finished: it never counts down again."""

    STATUS = "Completed"

    def status_label(self):
        """Same method name as in Task, different result -> polymorphism."""
        return "Completed"

    def countdown_seconds(self):
        return 0

    def alarm_message(self):
        return f"Reminder: {self.name} was already completed."


# ----------------------------------------------------------------------
# Helpers for the reminder time text
# ----------------------------------------------------------------------
def parse_duration(text):
    """Turns 'HH:MM:SS' text into seconds: '00:05:30' -> 330.

    Raises ValueError with a message that can be shown to the user when the
    typed time is not a valid reminder time.
    """
    cleaned = "" if text is None else text.strip()
    parts = cleaned.split(":")
    if len(parts) != 3:
        raise ValueError("Reminder time must be written as HH:MM:SS "
                         "(example: 00:05:30).")
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"'{cleaned}' is not a valid HH:MM:SS time. "
                             "Use numbers only, example: 00:05:30.")
    hours, minutes, seconds = (int(part) for part in parts)
    if minutes > 59:
        raise ValueError("Minutes (MM) must be between 00 and 59.")
    if seconds > 59:
        raise ValueError("Seconds (SS) must be between 00 and 59.")
    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise ValueError("Reminder time must be more than 00:00:00.")
    return total


def seconds_to_text(total_seconds):
    """Turns seconds into 'HH:MM:SS' text: 90 -> '00:01:30'."""
    seconds = max(0, int(total_seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, rest = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{rest:02d}"


def task_from_row(row):
    """Builds the right object from one row of the tasks table.

    Row order: id, name, description, reminder_seconds, created_at, status.
    A completed row becomes a CompletedTask, every other row a Task.
    """
    task_id, name, description, reminder_seconds, created_at, status = row
    if status == CompletedTask.STATUS:
        return CompletedTask(name=name, description=description or "",
                             reminder_seconds=reminder_seconds,
                             task_id=task_id, created_at=created_at or "",
                             status=status)
    return Task(name=name, description=description or "",
                reminder_seconds=reminder_seconds, task_id=task_id,
                created_at=created_at or "", status=status)
