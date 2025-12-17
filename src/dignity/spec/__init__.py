"""Spec management utilities."""

from __future__ import annotations

from dignity.spec.create import SpecConfig, SpecCreateError, create
from dignity.spec.lifecycle import archive, restore, set_status
from dignity.spec.query import SpecNotFoundError, find_by_code, get_progress, get_spec, list_specs
from dignity.spec.sections import (
    SectionNotFoundError,
    add_section,
    append_to_section,
    get_section,
    remove_section,
    set_section,
)
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
    update_task,
)
from dignity.spec.types import Spec, Status, Task, TasksFile
from dignity.spec.validation import generate_code, make_code_unique, validate_spec_name

__all__ = [
    # Creation
    "create",
    "SpecConfig",
    "SpecCreateError",
    # Validation
    "generate_code",
    "make_code_unique",
    "validate_spec_name",
    # Types
    "Spec",
    "Status",
    "Task",
    "TasksFile",
    # Tasks
    "TaskNotFoundError",
    "load_tasks",
    "save_tasks",
    "add_task",
    "add_tasks",
    "complete_task",
    "start_task",
    "discard_task",
    "get_task",
    "get_pending_tasks",
    "update_task",
    # Sections
    "SectionNotFoundError",
    "get_section",
    "set_section",
    "append_to_section",
    "add_section",
    "remove_section",
    # Query
    "SpecNotFoundError",
    "get_spec",
    "list_specs",
    "find_by_code",
    "get_progress",
    # Lifecycle
    "archive",
    "restore",
    "set_status",
]
