"""Tests for spec task operations."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dignity.spec.tasks import (
    TaskNotFoundError,
    add_task,
    add_tasks,
    complete_task,
    discard_task,
    get_pending_tasks,
    get_task,
    load_tasks,
    save_tasks,
    start_task,
)
from dignity.spec.types import Status, Task, TasksFile


# Fixtures


@pytest.fixture
def spec_dir(tmp_path: Path) -> Path:
    """Create a spec directory for testing."""
    spec_path = tmp_path / "test-spec"
    spec_path.mkdir()
    return spec_path


@pytest.fixture
def empty_tasks_yaml(spec_dir: Path) -> Path:
    """Create an empty tasks.yaml file."""
    tasks_file = spec_dir / "tasks.yaml"
    content = {
        "spec": "test-spec",
        "code": "TS",
        "next_id": 1,
        "tasks": [],
    }
    tasks_file.write_text(yaml.dump(content))
    return spec_dir


@pytest.fixture
def populated_tasks_yaml(spec_dir: Path) -> Path:
    """Create a tasks.yaml with existing tasks."""
    tasks_file = spec_dir / "tasks.yaml"
    content = {
        "spec": "test-spec",
        "code": "TS",
        "next_id": 4,
        "tasks": [
            {
                "id": "TS-001",
                "content": "First task",
                "status": "completed",
                "active_form": "First task",
            },
            {
                "id": "TS-002",
                "content": "Second task",
                "status": "in_progress",
                "active_form": "Second task",
            },
            {
                "id": "TS-003",
                "content": "Third task",
                "status": "pending",
                "active_form": "Third task",
            },
        ],
    }
    tasks_file.write_text(yaml.dump(content))
    return spec_dir


# load_tasks tests


def test_load_tasks_returns_tasks_file(empty_tasks_yaml: Path) -> None:
    result = load_tasks(empty_tasks_yaml)
    assert isinstance(result, TasksFile)


def test_load_tasks_parses_empty_tasks_list(empty_tasks_yaml: Path) -> None:
    result = load_tasks(empty_tasks_yaml)
    assert result.tasks == []


def test_load_tasks_parses_spec_name(empty_tasks_yaml: Path) -> None:
    result = load_tasks(empty_tasks_yaml)
    assert result.spec == "test-spec"


def test_load_tasks_parses_code(empty_tasks_yaml: Path) -> None:
    result = load_tasks(empty_tasks_yaml)
    assert result.code == "TS"


def test_load_tasks_parses_next_id(empty_tasks_yaml: Path) -> None:
    result = load_tasks(empty_tasks_yaml)
    assert result.next_id == 1


def test_load_tasks_parses_tasks(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert len(result.tasks) == 3


def test_load_tasks_parses_task_id(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert result.tasks[0].id == "TS-001"


def test_load_tasks_parses_task_content(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert result.tasks[0].content == "First task"


def test_load_tasks_parses_task_status_completed(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert result.tasks[0].status == Status.COMPLETED


def test_load_tasks_parses_task_status_in_progress(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert result.tasks[1].status == Status.IN_PROGRESS


def test_load_tasks_parses_task_status_pending(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert result.tasks[2].status == Status.PENDING


def test_load_tasks_parses_task_active_form(populated_tasks_yaml: Path) -> None:
    result = load_tasks(populated_tasks_yaml)
    assert result.tasks[0].active_form == "First task"


def test_load_tasks_raises_file_not_found(spec_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_tasks(spec_dir)


def test_load_tasks_raises_for_missing_directory(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent-spec"
    with pytest.raises(FileNotFoundError):
        load_tasks(nonexistent)


# save_tasks tests


def test_save_tasks_creates_yaml_file(spec_dir: Path) -> None:
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[], next_id=1)
    save_tasks(spec_dir, tasks_file)
    assert (spec_dir / "tasks.yaml").exists()


def test_save_tasks_writes_spec_name(spec_dir: Path) -> None:
    tasks_file = TasksFile(spec="my-spec", code="MS", tasks=[], next_id=1)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["spec"] == "my-spec"


def test_save_tasks_writes_code(spec_dir: Path) -> None:
    tasks_file = TasksFile(spec="test-spec", code="ABC", tasks=[], next_id=1)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["code"] == "ABC"


def test_save_tasks_writes_next_id(spec_dir: Path) -> None:
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[], next_id=42)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["next_id"] == 42


def test_save_tasks_writes_empty_tasks_list(spec_dir: Path) -> None:
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[], next_id=1)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["tasks"] == []


def test_save_tasks_writes_task_id(spec_dir: Path) -> None:
    task = Task(id="TS-001", content="Test", status=Status.PENDING, active_form="Test")
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[task], next_id=2)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["tasks"][0]["id"] == "TS-001"


def test_save_tasks_writes_task_content(spec_dir: Path) -> None:
    task = Task(id="TS-001", content="My content", status=Status.PENDING, active_form="X")
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[task], next_id=2)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["tasks"][0]["content"] == "My content"


def test_save_tasks_writes_task_status(spec_dir: Path) -> None:
    task = Task(id="TS-001", content="X", status=Status.IN_PROGRESS, active_form="X")
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[task], next_id=2)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "in_progress"


def test_save_tasks_writes_task_active_form(spec_dir: Path) -> None:
    task = Task(id="TS-001", content="X", status=Status.PENDING, active_form="Doing X")
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[task], next_id=2)
    save_tasks(spec_dir, tasks_file)
    content = yaml.safe_load((spec_dir / "tasks.yaml").read_text())
    assert content["tasks"][0]["active_form"] == "Doing X"


def test_save_tasks_overwrites_existing_file(empty_tasks_yaml: Path) -> None:
    task = Task(id="TS-001", content="New", status=Status.PENDING, active_form="New")
    tasks_file = TasksFile(spec="test-spec", code="TS", tasks=[task], next_id=2)
    save_tasks(empty_tasks_yaml, tasks_file)
    content = yaml.safe_load((empty_tasks_yaml / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 1


def test_save_tasks_roundtrip(populated_tasks_yaml: Path) -> None:
    original = load_tasks(populated_tasks_yaml)
    save_tasks(populated_tasks_yaml, original)
    reloaded = load_tasks(populated_tasks_yaml)
    assert reloaded.spec == original.spec
    assert reloaded.code == original.code
    assert reloaded.next_id == original.next_id
    assert len(reloaded.tasks) == len(original.tasks)


# add_task tests


def test_add_task_returns_task(empty_tasks_yaml: Path) -> None:
    result = add_task(empty_tasks_yaml, "Do something", "Doing something")
    assert isinstance(result, Task)


def test_add_task_sets_content(empty_tasks_yaml: Path) -> None:
    result = add_task(empty_tasks_yaml, "Implement feature", "Implementing feature")
    assert result.content == "Implement feature"


def test_add_task_sets_active_form(empty_tasks_yaml: Path) -> None:
    result = add_task(empty_tasks_yaml, "Implement feature", "Implementing feature")
    assert result.active_form == "Implementing feature"


def test_add_task_sets_status_pending(empty_tasks_yaml: Path) -> None:
    result = add_task(empty_tasks_yaml, "Do something", "Doing something")
    assert result.status == Status.PENDING


def test_add_task_generates_id_with_code(empty_tasks_yaml: Path) -> None:
    result = add_task(empty_tasks_yaml, "Do something", "Doing something")
    assert result.id.startswith("TS-")


def test_add_task_generates_zero_padded_id(empty_tasks_yaml: Path) -> None:
    result = add_task(empty_tasks_yaml, "Do something", "Doing something")
    assert result.id == "TS-001"


def test_add_task_increments_id(empty_tasks_yaml: Path) -> None:
    add_task(empty_tasks_yaml, "First", "First")
    result = add_task(empty_tasks_yaml, "Second", "Second")
    assert result.id == "TS-002"


def test_add_task_persists_to_file(empty_tasks_yaml: Path) -> None:
    add_task(empty_tasks_yaml, "Persisted", "Persisting")
    tasks_file = load_tasks(empty_tasks_yaml)
    assert len(tasks_file.tasks) == 1


def test_add_task_increments_next_id_in_file(empty_tasks_yaml: Path) -> None:
    add_task(empty_tasks_yaml, "Task", "Task")
    tasks_file = load_tasks(empty_tasks_yaml)
    assert tasks_file.next_id == 2


def test_add_task_uses_existing_next_id(populated_tasks_yaml: Path) -> None:
    result = add_task(populated_tasks_yaml, "Fourth", "Fourth")
    assert result.id == "TS-004"


def test_add_task_preserves_existing_tasks(populated_tasks_yaml: Path) -> None:
    add_task(populated_tasks_yaml, "Fourth", "Fourth")
    tasks_file = load_tasks(populated_tasks_yaml)
    assert len(tasks_file.tasks) == 4


# add_tasks tests


def test_add_tasks_returns_list_of_tasks(empty_tasks_yaml: Path) -> None:
    tasks = [
        {"content": "First", "active_form": "First"},
        {"content": "Second", "active_form": "Second"},
    ]
    result = add_tasks(empty_tasks_yaml, tasks)
    assert isinstance(result, list)
    assert all(isinstance(t, Task) for t in result)


def test_add_tasks_returns_correct_count(empty_tasks_yaml: Path) -> None:
    tasks = [
        {"content": "A", "active_form": "A"},
        {"content": "B", "active_form": "B"},
        {"content": "C", "active_form": "C"},
    ]
    result = add_tasks(empty_tasks_yaml, tasks)
    assert len(result) == 3


def test_add_tasks_generates_sequential_ids(empty_tasks_yaml: Path) -> None:
    tasks = [
        {"content": "A", "active_form": "A"},
        {"content": "B", "active_form": "B"},
    ]
    result = add_tasks(empty_tasks_yaml, tasks)
    assert result[0].id == "TS-001"
    assert result[1].id == "TS-002"


def test_add_tasks_all_pending_status(empty_tasks_yaml: Path) -> None:
    tasks = [
        {"content": "A", "active_form": "A"},
        {"content": "B", "active_form": "B"},
    ]
    result = add_tasks(empty_tasks_yaml, tasks)
    assert all(t.status == Status.PENDING for t in result)


def test_add_tasks_persists_all_to_file(empty_tasks_yaml: Path) -> None:
    tasks = [
        {"content": "A", "active_form": "A"},
        {"content": "B", "active_form": "B"},
    ]
    add_tasks(empty_tasks_yaml, tasks)
    tasks_file = load_tasks(empty_tasks_yaml)
    assert len(tasks_file.tasks) == 2


def test_add_tasks_updates_next_id(empty_tasks_yaml: Path) -> None:
    tasks = [
        {"content": "A", "active_form": "A"},
        {"content": "B", "active_form": "B"},
    ]
    add_tasks(empty_tasks_yaml, tasks)
    tasks_file = load_tasks(empty_tasks_yaml)
    assert tasks_file.next_id == 3


def test_add_tasks_empty_list(empty_tasks_yaml: Path) -> None:
    result = add_tasks(empty_tasks_yaml, [])
    assert result == []


def test_add_tasks_preserves_existing(populated_tasks_yaml: Path) -> None:
    tasks = [{"content": "New", "active_form": "New"}]
    add_tasks(populated_tasks_yaml, tasks)
    tasks_file = load_tasks(populated_tasks_yaml)
    assert len(tasks_file.tasks) == 4


# complete_task tests


def test_complete_task_returns_task(populated_tasks_yaml: Path) -> None:
    result = complete_task(populated_tasks_yaml, "TS-003")
    assert isinstance(result, Task)


def test_complete_task_sets_status_completed(populated_tasks_yaml: Path) -> None:
    result = complete_task(populated_tasks_yaml, "TS-003")
    assert result.status == Status.COMPLETED


def test_complete_task_persists_status(populated_tasks_yaml: Path) -> None:
    complete_task(populated_tasks_yaml, "TS-003")
    tasks_file = load_tasks(populated_tasks_yaml)
    task = next(t for t in tasks_file.tasks if t.id == "TS-003")
    assert task.status == Status.COMPLETED


def test_complete_task_preserves_content(populated_tasks_yaml: Path) -> None:
    result = complete_task(populated_tasks_yaml, "TS-003")
    assert result.content == "Third task"


def test_complete_task_preserves_active_form(populated_tasks_yaml: Path) -> None:
    result = complete_task(populated_tasks_yaml, "TS-003")
    assert result.active_form == "Third task"


def test_complete_task_from_in_progress(populated_tasks_yaml: Path) -> None:
    result = complete_task(populated_tasks_yaml, "TS-002")
    assert result.status == Status.COMPLETED


def test_complete_task_already_completed(populated_tasks_yaml: Path) -> None:
    result = complete_task(populated_tasks_yaml, "TS-001")
    assert result.status == Status.COMPLETED


def test_complete_task_raises_task_not_found(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        complete_task(populated_tasks_yaml, "TS-999")


def test_complete_task_raises_for_invalid_id(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        complete_task(populated_tasks_yaml, "INVALID")


# start_task tests


def test_start_task_returns_task(populated_tasks_yaml: Path) -> None:
    result = start_task(populated_tasks_yaml, "TS-003")
    assert isinstance(result, Task)


def test_start_task_sets_status_in_progress(populated_tasks_yaml: Path) -> None:
    result = start_task(populated_tasks_yaml, "TS-003")
    assert result.status == Status.IN_PROGRESS


def test_start_task_persists_status(populated_tasks_yaml: Path) -> None:
    start_task(populated_tasks_yaml, "TS-003")
    tasks_file = load_tasks(populated_tasks_yaml)
    task = next(t for t in tasks_file.tasks if t.id == "TS-003")
    assert task.status == Status.IN_PROGRESS


def test_start_task_preserves_content(populated_tasks_yaml: Path) -> None:
    result = start_task(populated_tasks_yaml, "TS-003")
    assert result.content == "Third task"


def test_start_task_preserves_active_form(populated_tasks_yaml: Path) -> None:
    result = start_task(populated_tasks_yaml, "TS-003")
    assert result.active_form == "Third task"


def test_start_task_from_completed(populated_tasks_yaml: Path) -> None:
    result = start_task(populated_tasks_yaml, "TS-001")
    assert result.status == Status.IN_PROGRESS


def test_start_task_already_in_progress(populated_tasks_yaml: Path) -> None:
    result = start_task(populated_tasks_yaml, "TS-002")
    assert result.status == Status.IN_PROGRESS


def test_start_task_raises_task_not_found(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        start_task(populated_tasks_yaml, "TS-999")


def test_start_task_raises_for_invalid_id(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        start_task(populated_tasks_yaml, "INVALID")


# discard_task tests


def test_discard_task_returns_none(populated_tasks_yaml: Path) -> None:
    result = discard_task(populated_tasks_yaml, "TS-003")
    assert result is None


def test_discard_task_removes_from_file(populated_tasks_yaml: Path) -> None:
    discard_task(populated_tasks_yaml, "TS-003")
    tasks_file = load_tasks(populated_tasks_yaml)
    assert not any(t.id == "TS-003" for t in tasks_file.tasks)


def test_discard_task_reduces_count(populated_tasks_yaml: Path) -> None:
    discard_task(populated_tasks_yaml, "TS-003")
    tasks_file = load_tasks(populated_tasks_yaml)
    assert len(tasks_file.tasks) == 2


def test_discard_task_preserves_other_tasks(populated_tasks_yaml: Path) -> None:
    discard_task(populated_tasks_yaml, "TS-002")
    tasks_file = load_tasks(populated_tasks_yaml)
    ids = [t.id for t in tasks_file.tasks]
    assert "TS-001" in ids
    assert "TS-003" in ids


def test_discard_task_does_not_affect_next_id(populated_tasks_yaml: Path) -> None:
    discard_task(populated_tasks_yaml, "TS-003")
    tasks_file = load_tasks(populated_tasks_yaml)
    assert tasks_file.next_id == 4


def test_discard_task_raises_task_not_found(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        discard_task(populated_tasks_yaml, "TS-999")


def test_discard_task_raises_for_invalid_id(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        discard_task(populated_tasks_yaml, "INVALID")


# get_task tests


def test_get_task_returns_task(populated_tasks_yaml: Path) -> None:
    result = get_task(populated_tasks_yaml, "TS-001")
    assert isinstance(result, Task)


def test_get_task_returns_correct_task(populated_tasks_yaml: Path) -> None:
    result = get_task(populated_tasks_yaml, "TS-002")
    assert result.id == "TS-002"
    assert result.content == "Second task"


def test_get_task_returns_correct_status(populated_tasks_yaml: Path) -> None:
    result = get_task(populated_tasks_yaml, "TS-001")
    assert result.status == Status.COMPLETED


def test_get_task_returns_correct_active_form(populated_tasks_yaml: Path) -> None:
    result = get_task(populated_tasks_yaml, "TS-003")
    assert result.active_form == "Third task"


def test_get_task_raises_task_not_found(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        get_task(populated_tasks_yaml, "TS-999")


def test_get_task_raises_for_invalid_id(populated_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        get_task(populated_tasks_yaml, "INVALID")


def test_get_task_raises_for_empty_tasks(empty_tasks_yaml: Path) -> None:
    with pytest.raises(TaskNotFoundError):
        get_task(empty_tasks_yaml, "TS-001")


# get_pending_tasks tests


def test_get_pending_tasks_returns_list(populated_tasks_yaml: Path) -> None:
    result = get_pending_tasks(populated_tasks_yaml)
    assert isinstance(result, list)


def test_get_pending_tasks_returns_only_pending(populated_tasks_yaml: Path) -> None:
    result = get_pending_tasks(populated_tasks_yaml)
    assert all(t.status == Status.PENDING for t in result)


def test_get_pending_tasks_returns_correct_count(populated_tasks_yaml: Path) -> None:
    result = get_pending_tasks(populated_tasks_yaml)
    assert len(result) == 1


def test_get_pending_tasks_returns_correct_task(populated_tasks_yaml: Path) -> None:
    result = get_pending_tasks(populated_tasks_yaml)
    assert result[0].id == "TS-003"


def test_get_pending_tasks_empty_when_no_pending(empty_tasks_yaml: Path) -> None:
    result = get_pending_tasks(empty_tasks_yaml)
    assert result == []


def test_get_pending_tasks_empty_when_all_completed(spec_dir: Path) -> None:
    tasks_file = spec_dir / "tasks.yaml"
    content = {
        "spec": "test-spec",
        "code": "TS",
        "next_id": 3,
        "tasks": [
            {"id": "TS-001", "content": "Done", "status": "completed", "active_form": "Done"},
            {"id": "TS-002", "content": "Also done", "status": "completed", "active_form": "Also done"},
        ],
    }
    tasks_file.write_text(yaml.dump(content))
    result = get_pending_tasks(spec_dir)
    assert result == []


def test_get_pending_tasks_excludes_in_progress(populated_tasks_yaml: Path) -> None:
    result = get_pending_tasks(populated_tasks_yaml)
    assert not any(t.id == "TS-002" for t in result)


def test_get_pending_tasks_excludes_completed(populated_tasks_yaml: Path) -> None:
    result = get_pending_tasks(populated_tasks_yaml)
    assert not any(t.id == "TS-001" for t in result)


# TaskNotFoundError tests


def test_task_not_found_error_is_exception() -> None:
    assert issubclass(TaskNotFoundError, Exception)


def test_task_not_found_error_stores_task_id() -> None:
    error = TaskNotFoundError("TS-999")
    assert error.task_id == "TS-999"


def test_task_not_found_error_message() -> None:
    error = TaskNotFoundError("TS-999")
    assert "TS-999" in str(error)


# Edge cases


def test_add_task_with_high_next_id(spec_dir: Path) -> None:
    tasks_file = spec_dir / "tasks.yaml"
    content = {
        "spec": "test-spec",
        "code": "TS",
        "next_id": 999,
        "tasks": [],
    }
    tasks_file.write_text(yaml.dump(content))
    result = add_task(spec_dir, "High ID", "High ID")
    assert result.id == "TS-999"


def test_add_task_id_overflow_to_four_digits(spec_dir: Path) -> None:
    tasks_file = spec_dir / "tasks.yaml"
    content = {
        "spec": "test-spec",
        "code": "TS",
        "next_id": 1000,
        "tasks": [],
    }
    tasks_file.write_text(yaml.dump(content))
    result = add_task(spec_dir, "Overflow", "Overflow")
    assert result.id == "TS-1000"


def test_task_with_multiline_content(empty_tasks_yaml: Path) -> None:
    content = "Line 1\nLine 2\nLine 3"
    result = add_task(empty_tasks_yaml, content, "Multi-line")
    reloaded = get_task(empty_tasks_yaml, result.id)
    assert reloaded.content == content


def test_task_with_special_characters(empty_tasks_yaml: Path) -> None:
    content = "Task with: colons, quotes \"test\", and 'apostrophes'"
    result = add_task(empty_tasks_yaml, content, "Special")
    reloaded = get_task(empty_tasks_yaml, result.id)
    assert reloaded.content == content


def test_different_spec_codes(tmp_path: Path) -> None:
    spec_path = tmp_path / "feature-spec"
    spec_path.mkdir()
    tasks_file = spec_path / "tasks.yaml"
    content = {
        "spec": "feature-spec",
        "code": "FS",
        "next_id": 1,
        "tasks": [],
    }
    tasks_file.write_text(yaml.dump(content))
    result = add_task(spec_path, "Test", "Testing")
    assert result.id == "FS-001"


def test_single_character_code(tmp_path: Path) -> None:
    spec_path = tmp_path / "minimal-spec"
    spec_path.mkdir()
    tasks_file = spec_path / "tasks.yaml"
    content = {
        "spec": "minimal-spec",
        "code": "M",
        "next_id": 1,
        "tasks": [],
    }
    tasks_file.write_text(yaml.dump(content))
    result = add_task(spec_path, "Test", "Testing")
    assert result.id == "M-001"
