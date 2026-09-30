"""
view.py  -  the two windows of the program.

  * MainWindow  - the table of tasks, the five buttons, the countdown (QTimer)
                  and the question that is asked when the program is closed.
  * TaskDialog  - the small "Add Task" form.

Both inherit from a normal PyQt5 class (QMainWindow and QDialog). No SQL is
written here, the windows only call TaskService, and the ask-before-closing
logic is in MainWindow.closeEvent().
"""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (QAbstractItemView, QDialog, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout,
                             QWidget)

from features.service import TaskServiceError
from features.task import seconds_to_text


class MainWindow(QMainWindow):
    """The TASK REMINDER SYSTEM window."""

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.tasks = []           # the Task objects that are shown in the table
        self.countdowns = {}      # task id -> seconds that are still left
        self.running_tasks = {}   # task id -> the Task that counts down

        self.setWindowTitle("RemindMe")
        self.resize(920, 470)

        self._build_widgets()
        self._connect_signals()

        # One QTimer for the whole program. It ticks once per second and only
        # runs while at least one task is counting down.
        self.timer = QTimer(self)
        self.timer.setInterval(1000)          # 1000 milliseconds = 1 second
        self.timer.timeout.connect(self.on_timer_tick)

        self.refresh_table()                  # load the saved tasks from SQLite

    # ------------------------------------------------------------------
    # Building the window
    # ------------------------------------------------------------------
    def _build_widgets(self):
        """Creates the header, the table, the buttons and the window layout."""
        # The blue banner on top. It is decoration only: it has no signal, no
        # slot and no SQL, and the colours live in style.qss (appHeader). The
        # name "banner" is used on purpose, because "header" below is Qt's name
        # for the row with the column titles.
        banner = self._build_banner()

        self.table = QTableWidget(0, 5)
        self.table.setObjectName("taskTable")
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Task Name", "Description", "Reminder Time", "Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # The Description column gets all the spare width of the window, so
        # long notes are shown instead of being cut off.
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Fixed)        # ID
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Task Name
        header.setSectionResizeMode(2, QHeaderView.Stretch)      # Description
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(1, 160)

        # A wrapped description needs a taller row: the rows grow on their own.
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)

        self.add_button = QPushButton("Add Task")
        self.delete_button = QPushButton("Delete Task")
        self.complete_button = QPushButton("Mark Complete")
        self.refresh_button = QPushButton("Refresh")
        self.exit_button = QPushButton("Exit")

        button_column = QVBoxLayout()
        for button in (self.add_button, self.delete_button,
                       self.complete_button, self.refresh_button,
                       self.exit_button):
            button.setMinimumWidth(130)
            button_column.addWidget(button)
        button_column.addStretch()

        self.info_label = QLabel("Countdown: none")
        self.info_label.setObjectName("infoLabel")

        table_column = QVBoxLayout()
        table_column.setSpacing(8)
        table_column.addWidget(self.table)
        table_column.addWidget(self.info_label)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(14)
        row_layout.addLayout(table_column, 4)
        row_layout.addLayout(button_column, 1)

        # The banner is placed above the row that holds the table + buttons.
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(16, 16, 16, 12)
        page_layout.setSpacing(12)
        page_layout.addWidget(banner)
        page_layout.addLayout(row_layout, 1)

        content = QWidget()
        content.setObjectName("mainContent")
        content.setLayout(page_layout)
        self.setCentralWidget(content)
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------
    def _build_banner(self):
        """The blue rounded banner: one big title and one small subtitle.

        It is a plain QWidget with two QLabels inside and no behaviour at all.
        The names appHeader, appTitle and appSubtitle are what style.qss uses
        to paint it blue, so no colour is written inside this file.
        """
        header = QWidget()
        header.setObjectName("appHeader")

        title = QLabel("RemindMe: Task Reminder System")
        title.setObjectName("appTitle")
        subtitle = QLabel("Manage your tasks and reminders")
        subtitle.setObjectName("appSubtitle")

        header_box = QVBoxLayout(header)
        header_box.setContentsMargins(18, 10, 18, 10)
        header_box.setSpacing(2)
        header_box.addWidget(title)
        header_box.addWidget(subtitle)
        return header

    # ------------------------------------------------------------------
    # Signals -> slots
    # ------------------------------------------------------------------
    def _connect_signals(self):
        """Connects every button signal to the slot that does the work."""
        self.add_button.clicked.connect(self.open_add_dialog)
        self.delete_button.clicked.connect(self.delete_task)
        self.complete_button.clicked.connect(self.mark_complete)
        self.refresh_button.clicked.connect(self.refresh_table)
        # The Exit button does exactly what the X of the window does: it calls
        # close(), and closeEvent() asks the question before closing.
        self.exit_button.clicked.connect(self.close)

    # ------------------------------------------------------------------
    # ADD TASK
    # ------------------------------------------------------------------
    def open_add_dialog(self):
        """Slot for 'Add Task': opens the dialog and waits for its signal."""
        dialog = TaskDialog(self.service, self)
        dialog.task_saved.connect(self.save_new_task)
        dialog.exec_()

    def save_new_task(self, task):
        """Slot for the signal of the dialog: INSERT it and count it down."""
        try:
            self.service.add_task(task)
        except TaskServiceError as error:
            QMessageBox.critical(self, "Database Error", str(error))
            return
        self.refresh_table()
        self.start_countdown(task)
        self.statusBar().showMessage(
            f"Saved task '{task.name}' ({task.reminder_text()})", 5000)

    # ------------------------------------------------------------------
    # VIEW THE TASKS (Refresh)
    # ------------------------------------------------------------------
    def refresh_table(self):
        """Slot for 'Refresh': SELECT every task from SQLite and show it."""
        try:
            tasks = self.service.get_tasks()
        except TaskServiceError as error:
            QMessageBox.critical(self, "Database Error", str(error))
            return

        # Remember which task was selected (by its real database id) so that
        # the selection can be put back after the table was rebuilt.
        selected_id = None
        current = self.table.currentRow()
        if 0 <= current < len(self.tasks):
            selected_id = self.tasks[current].task_id

        self.tasks = tasks
        self.table.setRowCount(0)
        for task in self.tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # The ID column shows the position in the list that is displayed
            # right now (1, 2, 3 ...). The real SQLite id (task.task_id) is
            # never changed and is used for every database operation.
            values = [row + 1, task.name, task.description,
                      self.reminder_display(task), task.status_label()]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                elif column == 2:
                    # Long descriptions are wrapped over several lines.
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter |
                                          Qt.TextWordWrap)
                self.table.setItem(row, column, item)
        self.table.resizeRowsToContents()
        self.restore_selection(selected_id)
        self.update_info_label()

    def restore_selection(self, task_id):
        """Selects the row of task_id again after the table was rebuilt."""
        if task_id is None:
            return
        for row, task in enumerate(self.tasks):
            if task.task_id == task_id:
                self.table.setCurrentCell(row, 0)
                self.table.selectRow(row)
                return

    # ------------------------------------------------------------------
    # Small helpers for the table
    # ------------------------------------------------------------------
    def update_countdown_display(self):
        """Rewrites the 'Reminder Time' column once per second.

        Only that one column is updated, the table is not built again, so the
        row the user selected stays selected while a countdown is running.
        """
        for row, task in enumerate(self.tasks):
            item = self.table.item(row, 3)
            if item is not None:
                item.setText(self.reminder_display(task))
        self.update_info_label()

    def reminder_display(self, task):
        """Text for the Reminder Time column (the time left while running)."""
        if task.task_id in self.countdowns:
            return seconds_to_text(self.countdowns[task.task_id])
        return task.reminder_text()

    def selected_task(self):
        """Returns the selected Task, or None when there is no selection."""
        row = self.table.currentRow()
        if row < 0:                      # no current cell: use the selection
            selected = self.table.selectionModel().selectedRows()
            if selected:
                row = selected[0].row()
        if row < 0 or row >= len(self.tasks):
            QMessageBox.information(self, "No Task Selected",
                                    "Please select a task in the table first.")
            return None
        return self.tasks[row]

    # ------------------------------------------------------------------
    # MARK COMPLETE (UPDATE)
    # ------------------------------------------------------------------
    def mark_complete(self):
        """Slot for 'Mark Complete': UPDATE the selected task to Completed."""
        task = self.selected_task()
        if task is None:
            return
        if task.is_completed():
            QMessageBox.information(self, "Already Completed",
                                    f"'{task.name}' is already completed.")
            return
        try:
            self.service.mark_complete(task)
        except TaskServiceError as error:
            QMessageBox.critical(self, "Database Error", str(error))
            return
        self.stop_countdown(task.task_id)
        self.refresh_table()
        self.statusBar().showMessage(
            f"'{task.name}' marked as completed", 5000)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete_task(self):
        """Slot for 'Delete Task': asks first, then DELETEs the task."""
        task = self.selected_task()
        if task is None:
            return
        answer = QMessageBox.question(
            self, "Delete Task",
            f"Do you really want to delete '{task.name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            self.service.delete_task(task)
        except TaskServiceError as error:
            QMessageBox.critical(self, "Database Error", str(error))
            return
        self.stop_countdown(task.task_id)
        self.refresh_table()
        self.statusBar().showMessage(f"Deleted task '{task.name}'", 5000)

    # ------------------------------------------------------------------
    # THE COUNTDOWN (the QTimer and the reminder popup)
    # ------------------------------------------------------------------
    def start_countdown(self, task):
        """Adds a task to the countdown. A completed task gives 0 seconds."""
        seconds = task.countdown_seconds()      # polymorphism
        if seconds <= 0 or task.task_id is None:
            return
        self.countdowns[task.task_id] = seconds
        self.running_tasks[task.task_id] = task
        if not self.timer.isActive():
            self.timer.start()              # the window stays responsive
        self.refresh_table()

    def stop_countdown(self, task_id):
        """Removes one task from the countdown."""
        self.countdowns.pop(task_id, None)
        self.running_tasks.pop(task_id, None)
        if not self.countdowns and self.timer.isActive():
            self.timer.stop()

    def on_timer_tick(self):
        """Slot of the QTimer: once per second every countdown loses 1."""
        finished = []
        for task_id in list(self.countdowns):
            self.countdowns[task_id] -= 1
            if self.countdowns[task_id] <= 0:
                finished.append(task_id)

        for task_id in finished:
            task = self.running_tasks.pop(task_id, None)
            self.countdowns.pop(task_id, None)
            self.update_info_label()
            if task is not None:
                # The reminder popup. Its text comes from the Task object.
                QMessageBox.information(self, "Time is up!",
                                        task.alarm_message())

        if not self.countdowns:
            self.timer.stop()      # nothing left to count down
        self.update_countdown_display()

    def update_info_label(self):
        """Shows the running countdowns in the label under the table."""
        if not self.countdowns:
            self.info_label.setText("Countdown: none")
            return
        parts = []
        for task_id, seconds in self.countdowns.items():
            task = self.running_tasks.get(task_id)
            name = task.name if task is not None else str(task_id)
            parts.append(f"{name} {seconds_to_text(seconds)}")
        self.info_label.setText("Countdown: " + "   |   ".join(parts))

    # ------------------------------------------------------------------
    # CLOSING THE PROGRAM (the X of the window and the Exit button)
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """Asks first, then finishes every pending task and closes.

        Yes -> all pending tasks become Completed inside SQLite, the QTimer is
               stopped and the window really closes, so the program ends.
        No  -> event.ignore() keeps the window open, nothing is changed and
               the countdown keeps running.
        """
        answer = QMessageBox.question(
            self, "Close Program",
            "Closing the program will immediately mark all pending tasks as "
            "COMPLETED. Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            event.ignore()                 # stay open, keep counting down
            return

        try:
            self.service.complete_all_pending_tasks()
        except TaskServiceError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        self.timer.stop()                  # the timer only lives while open
        event.accept()                     # now Qt is allowed to close


class TaskDialog(QDialog):
    """The 'Add Task' dialog: it collects the typed data and checks it."""

    # Emitted when the typed data is correct. It carries a Task object.
    task_saved = pyqtSignal(object)

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Add Task")
        self.setMinimumWidth(380)
        self._build_widgets()
        self._connect_signals()

    # ------------------------------------------------------------------
    def _build_widgets(self):
        """Places the labels, the input boxes and the buttons."""
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Example: Study Math")

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Optional notes about the task")
        self.description_input.setMaximumHeight(70)

        self.reminder_input = QLineEdit()
        self.reminder_input.setPlaceholderText("HH:MM:SS   Example: 00:05:30")
        self.reminder_input.setAlignment(Qt.AlignCenter)

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Task Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_input)
        layout.addWidget(QLabel("Reminder Time (HH:MM:SS):"))
        layout.addWidget(self.reminder_input)
        layout.addLayout(button_row)
        self.setLayout(layout)

        self.name_input.setFocus()      # the keyboard starts in the first box

    # ------------------------------------------------------------------
    def _connect_signals(self):
        """Slots: Save -> save_task, Cancel -> reject (built into QDialog)."""
        self.save_button.clicked.connect(self.save_task)
        self.cancel_button.clicked.connect(self.reject)

    # ------------------------------------------------------------------
    def save_task(self):
        """Slot for 'Save': checks the data, then sends the signal."""
        try:
            task = self.service.validate_new_task(
                self.name_input.text(),
                self.description_input.toPlainText(),
                self.reminder_input.text())
        except (ValueError, TaskServiceError) as error:
            QMessageBox.warning(self, "Invalid Input", str(error))
            return
        self.task_saved.emit(task)      # MainWindow does the INSERT
        self.accept()                   # and the dialog closes
