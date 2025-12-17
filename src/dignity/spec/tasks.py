"""Task operations for spec management."""

from __future__ import annotations

from pathlib import Path

import yaml

from dignity.spec.types import Status, Task, TasksFile


class TaskNotFoundError(Exception):
    """Raised when a task with the given ID is not found."""

    def __init__(self, task_id: str) -> None:
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


def load_tasks(spec_path: Path) -> TasksFile:
    """Load tasks from spec_path/tasks.yaml."""
    tasks_yaml = spec_path / "tasks.yaml"
    if not tasks_yaml.exists():
        raise FileNotFoundError(f"tasks.yaml not found in {spec_path}")

    content = yaml.safe_load(tasks_yaml.read_text())

    tasks = [
        Task(
            id=t["id"],
            content=t["content"],
            status=Status(t["status"]),
            active_form=t["active_form"],
        )
        for t in content.get("tasks", [])
    ]

    return TasksFile(
        spec=content["spec"],
        code=content["code"],
        tasks=tasks,
        next_id=content.get("next_id", 1),
    )


def save_tasks(spec_path: Path, tasks_file: TasksFile) -> None:
    """Save tasks to spec_path/tasks.yaml."""
    tasks_yaml = spec_path / "tasks.yaml"

    content = {
        "spec": tasks_file.spec,
        "code": tasks_file.code,
        "next_id": tasks_file.next_id,
        "tasks": [
            {
                "id": t.id,
                "content": t.content,
                "status": t.status.value,
                "active_form": t.active_form,
            }
            for t in tasks_file.tasks
        ],
    }

    tasks_yaml.write_text(yaml.dump(content, allow_unicode=True))


def _generate_task_id(code: str, number: int) -> str:
    """Generate task ID in format CODE-NNN."""
    return f"{code}-{number:03d}"


def add_task(spec_path: Path, content: str, active_form: str) -> Task:
    """Add a new task with auto-generated ID."""
    tasks_file = load_tasks(spec_path)

    task_id = _generate_task_id(tasks_file.code, tasks_file.next_id)
    task = Task(
        id=task_id,
        content=content,
        status=Status.PENDING,
        active_form=active_form,
    )

    tasks_file.tasks.append(task)
    tasks_file.next_id += 1
    save_tasks(spec_path, tasks_file)

    return task


def add_tasks(spec_path: Path, tasks: list[dict]) -> list[Task]:
    """Add multiple tasks in batch."""
    if not tasks:
        return []

    tasks_file = load_tasks(spec_path)
    result = []

    for task_dict in tasks:
        task_id = _generate_task_id(tasks_file.code, tasks_file.next_id)
        task = Task(
            id=task_id,
            content=task_dict["content"],
            status=Status.PENDING,
            active_form=task_dict["active_form"],
        )
        tasks_file.tasks.append(task)
        tasks_file.next_id += 1
        result.append(task)

    save_tasks(spec_path, tasks_file)
    return result


def _find_task(tasks_file: TasksFile, task_id: str) -> Task:
    """Find a task by ID, raising TaskNotFoundError if not found."""
    for task in tasks_file.tasks:
        if task.id == task_id:
            return task
    raise TaskNotFoundError(task_id)


def complete_task(spec_path: Path, task_id: str) -> Task:
    """Set a task's status to COMPLETED."""
    tasks_file = load_tasks(spec_path)
    task = _find_task(tasks_file, task_id)
    task.status = Status.COMPLETED
    save_tasks(spec_path, tasks_file)
    return task


def start_task(spec_path: Path, task_id: str) -> Task:
    """Set a task's status to IN_PROGRESS."""
    tasks_file = load_tasks(spec_path)
    task = _find_task(tasks_file, task_id)
    task.status = Status.IN_PROGRESS
    save_tasks(spec_path, tasks_file)
    return task


def discard_task(spec_path: Path, task_id: str) -> None:
    """Remove a task from the tasks file."""
    tasks_file = load_tasks(spec_path)
    _find_task(tasks_file, task_id)
    tasks_file.tasks = [t for t in tasks_file.tasks if t.id != task_id]
    save_tasks(spec_path, tasks_file)


def get_task(spec_path: Path, task_id: str) -> Task:
    """Get a task by ID."""
    tasks_file = load_tasks(spec_path)
    return _find_task(tasks_file, task_id)


def get_pending_tasks(spec_path: Path) -> list[Task]:
    """Get all tasks with PENDING status."""
    tasks_file = load_tasks(spec_path)
    return [t for t in tasks_file.tasks if t.status == Status.PENDING]


def update_task(
    spec_path: Path,
    task_id: str,
    content: str | None = None,
    active_form: str | None = None,
    status: Status | None = None,
) -> tuple[Task, bool]:
    """Update or create a task (upsert). Returns (task, created)."""
    tasks_file = load_tasks(spec_path)
    created = False

    try:
        task = _find_task(tasks_file, task_id)
    except TaskNotFoundError:
        if content is None or active_form is None:
            raise ValueError("content and active_form required for new task")
        task = Task(
            id=task_id,
            content=content,
            status=status or Status.PENDING,
            active_form=active_form,
        )
        tasks_file.tasks.append(task)
        created = True

    if not created:
        if content is not None:
            task.content = content
        if active_form is not None:
            task.active_form = active_form
        if status is not None:
            task.status = status

    save_tasks(spec_path, tasks_file)
    return task, created
