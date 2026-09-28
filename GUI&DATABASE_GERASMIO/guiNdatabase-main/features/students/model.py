from dataclasses import dataclass
import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class Student:
    name: str
    email: str
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.email = self.email.strip().lower()

        if len(self.name) < 2:
            raise ValueError("Name must have at least 3 characters")

        if not EMAIL_PATTERN.fullmatch(self.email):
            raise ValueError("Invalid email format")