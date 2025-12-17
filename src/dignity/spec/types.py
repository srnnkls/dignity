from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from pathlib import Path


class Status(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class Task:
    id: str
    content: str
    status: Status
    active_form: str


@dataclass
class TasksFile:
    spec: str
    code: str
    tasks: list[Task]
    next_id: int = field(default=1)


@dataclass
class Spec:
    name: str
    code: str
    issue_type: str
    created: date
    status: str
    path: Path
