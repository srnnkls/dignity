"""Tests for spec types."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from pathlib import Path

from dignity.spec.types import Spec, Status, Task, TasksFile


# Status enum tests


def test_status_is_str_enum() -> None:
    assert issubclass(Status, StrEnum)


def test_status_has_pending_value() -> None:
    assert Status.PENDING == "pending"


def test_status_has_in_progress_value() -> None:
    assert Status.IN_PROGRESS == "in_progress"


def test_status_has_completed_value() -> None:
    assert Status.COMPLETED == "completed"


def test_status_values_count() -> None:
    assert len(Status) == 3


def test_status_string_conversion() -> None:
    assert str(Status.PENDING) == "pending"
    assert str(Status.IN_PROGRESS) == "in_progress"
    assert str(Status.COMPLETED) == "completed"


# Task dataclass tests


def test_task_instantiation() -> None:
    task = Task(
        id="SMA-001",
        content="Implement Status enum",
        status=Status.PENDING,
        active_form="Implementing Status enum",
    )
    assert task.id == "SMA-001"
    assert task.content == "Implement Status enum"
    assert task.status == Status.PENDING
    assert task.active_form == "Implementing Status enum"


def test_task_with_all_status_values() -> None:
    pending = Task(id="SMA-001", content="t", status=Status.PENDING, active_form="t")
    in_progress = Task(id="SMA-002", content="t", status=Status.IN_PROGRESS, active_form="t")
    completed = Task(id="SMA-003", content="t", status=Status.COMPLETED, active_form="t")

    assert pending.status == Status.PENDING
    assert in_progress.status == Status.IN_PROGRESS
    assert completed.status == Status.COMPLETED


def test_task_id_format_variations() -> None:
    task1 = Task(id="SMA-001", content="t", status=Status.PENDING, active_form="t")
    task2 = Task(id="FSD-042", content="t", status=Status.PENDING, active_form="t")
    task3 = Task(id="D-001", content="t", status=Status.PENDING, active_form="t")
    task4 = Task(id="HM-123", content="t", status=Status.PENDING, active_form="t")

    assert task1.id == "SMA-001"
    assert task2.id == "FSD-042"
    assert task3.id == "D-001"
    assert task4.id == "HM-123"


# TasksFile dataclass tests


def test_tasks_file_instantiation() -> None:
    tasks_file = TasksFile(
        spec="spec-management-api",
        code="SMA",
        next_id=1,
        tasks=[],
    )
    assert tasks_file.spec == "spec-management-api"
    assert tasks_file.code == "SMA"
    assert tasks_file.next_id == 1
    assert tasks_file.tasks == []


def test_tasks_file_next_id_default() -> None:
    tasks_file = TasksFile(spec="my-spec", code="MS", tasks=[])
    assert tasks_file.next_id == 1


def test_tasks_file_with_tasks() -> None:
    task1 = Task(id="MS-001", content="First", status=Status.COMPLETED, active_form="First")
    task2 = Task(id="MS-002", content="Second", status=Status.IN_PROGRESS, active_form="Second")
    task3 = Task(id="MS-003", content="Third", status=Status.PENDING, active_form="Third")

    tasks_file = TasksFile(spec="my-spec", code="MS", next_id=4, tasks=[task1, task2, task3])

    assert len(tasks_file.tasks) == 3
    assert tasks_file.tasks[0].id == "MS-001"
    assert tasks_file.tasks[1].id == "MS-002"
    assert tasks_file.tasks[2].id == "MS-003"


# Spec dataclass tests


def test_spec_instantiation() -> None:
    spec = Spec(
        name="spec-management-api",
        code="SMA",
        issue_type="feature",
        created=date(2025, 12, 17),
        status="Active",
        path=Path("/path/to/specs/active/spec-management-api"),
    )
    assert spec.name == "spec-management-api"
    assert spec.code == "SMA"
    assert spec.issue_type == "feature"
    assert spec.created == date(2025, 12, 17)
    assert spec.status == "Active"
    assert spec.path == Path("/path/to/specs/active/spec-management-api")


def test_spec_with_archived_status() -> None:
    spec = Spec(
        name="old-feature",
        code="OF",
        issue_type="feature",
        created=date(2024, 6, 1),
        status="Archived",
        path=Path("/specs/archived/old-feature"),
    )
    assert spec.status == "Archived"


def test_spec_issue_types() -> None:
    feature = Spec(
        name="f", code="F", issue_type="feature", created=date(2025, 1, 1), status="Active", path=Path(".")
    )
    bug = Spec(
        name="b", code="B", issue_type="bug", created=date(2025, 1, 1), status="Active", path=Path(".")
    )
    chore = Spec(
        name="c", code="C", issue_type="chore", created=date(2025, 1, 1), status="Active", path=Path(".")
    )

    assert feature.issue_type == "feature"
    assert bug.issue_type == "bug"
    assert chore.issue_type == "chore"


def test_spec_with_relative_path() -> None:
    spec = Spec(
        name="my-spec",
        code="MS",
        issue_type="feature",
        created=date(2025, 12, 17),
        status="Active",
        path=Path("specs/active/my-spec"),
    )
    assert spec.path == Path("specs/active/my-spec")
