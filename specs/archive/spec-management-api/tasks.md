---
todofile: ~/.claude/todos/1d2f1331-7551-47df-93b4-2e109f8c7cb1-agent-1d2f1331-7551-47df-93b4-2e109f8c7cb1.json
---

# Tasks: Spec Management API

## Phase 1: Foundation

- [x] Create `src/dignity/spec/types.py` with Task, Status, TasksFile, Spec dataclasses
- [x] Add tests for types in `tests/spec/test_types.py`

## Phase 2: Task Operations

- [x] Create `src/dignity/spec/tasks.py` with load_tasks, save_tasks
- [x] Implement add_task with auto-ID generation
- [x] Implement add_tasks for batch operations
- [x] Implement complete_task, start_task, discard_task
- [x] Implement get_task, get_pending_tasks
- [x] Add tests in `tests/spec/test_tasks.py`

## Phase 3: Section Operations

- [x] Create `src/dignity/spec/sections.py` with get_section, set_section
- [x] Implement append_to_section, add_section, remove_section
- [x] Add tests in `tests/spec/test_sections.py`

## Phase 4: Query & Lifecycle

- [x] Create `src/dignity/spec/query.py` with get_spec, list_specs, find_by_code
- [x] Implement get_progress for completion stats
- [x] Create `src/dignity/spec/lifecycle.py` with archive, restore, set_status
- [x] Add tests in `tests/spec/test_query.py` and `tests/spec/test_lifecycle.py`

## Phase 5: Integration

- [x] Update `src/dignity/spec/__init__.py` to export new functions
- [x] Update `src/dignity/spec/templates/tasks.yaml.jinja2` to include next_id
- [x] Update `src/dignity/spec/create.py` to use Task model

## Phase 6: CLI

- [x] Add `dignity spec task add` command
- [x] Add `dignity spec task complete/start/discard` commands
- [x] Add `dignity spec task list` command
- [x] Add `dignity spec archive/restore` commands
- [x] Add `dignity spec list/show/progress` commands

## Completion

- [x] All tests passing
- [x] CLI commands working end-to-end
