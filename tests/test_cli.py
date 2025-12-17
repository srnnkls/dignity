"""Tests for CLI commands.

These tests verify the CLI interface for spec management commands.
Tests are written to FAIL initially (RED phase) as the commands do not exist yet.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from dignity.cli import app


runner = CliRunner()


# Helper functions


def create_spec_md(
    spec_dir: Path,
    code: str,
    issue_type: str,
    created: date,
    status: str,
) -> None:
    """Create a spec.md file with frontmatter."""
    frontmatter = f"""---
code: {code}
issue_type: {issue_type}
created: {created.isoformat()}
status: {status}
---

# Spec: {spec_dir.name}

## Overview

Test spec content.
"""
    (spec_dir / "spec.md").write_text(frontmatter)


def create_tasks_yaml(
    spec_dir: Path,
    spec_name: str,
    code: str,
    tasks: list[dict],
    next_id: int | None = None,
) -> None:
    """Create a tasks.yaml file."""
    content = {
        "spec": spec_name,
        "code": code,
        "next_id": next_id if next_id is not None else len(tasks) + 1,
        "tasks": tasks,
    }
    (spec_dir / "tasks.yaml").write_text(yaml.dump(content))


# Fixtures


@pytest.fixture
def specs_base(tmp_path: Path) -> Path:
    """Create a specs base directory with active and archive subdirectories."""
    active = tmp_path / "active"
    archive = tmp_path / "archive"
    active.mkdir()
    archive.mkdir()
    return tmp_path


@pytest.fixture
def active_spec(specs_base: Path) -> Path:
    """Create an active spec directory with tasks."""
    spec_dir = specs_base / "active" / "test-feature"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "TF", "Feature", date(2025, 12, 17), "Active")
    create_tasks_yaml(
        spec_dir,
        "test-feature",
        "TF",
        [
            {"id": "TF-001", "content": "First task", "status": "completed", "active_form": "Completing first"},
            {"id": "TF-002", "content": "Second task", "status": "in_progress", "active_form": "Working on second"},
            {"id": "TF-003", "content": "Third task", "status": "pending", "active_form": "Doing third"},
        ],
        next_id=4,
    )
    return spec_dir


@pytest.fixture
def empty_spec(specs_base: Path) -> Path:
    """Create an active spec directory with no tasks."""
    spec_dir = specs_base / "active" / "empty-spec"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "ES", "Task", date(2025, 12, 17), "Active")
    create_tasks_yaml(spec_dir, "empty-spec", "ES", [])
    return spec_dir


@pytest.fixture
def archived_spec(specs_base: Path) -> Path:
    """Create an archived spec directory."""
    spec_dir = specs_base / "archive" / "old-feature"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "OF", "Feature", date(2024, 6, 1), "Archived")
    create_tasks_yaml(
        spec_dir,
        "old-feature",
        "OF",
        [
            {"id": "OF-001", "content": "Done task", "status": "completed", "active_form": "Done"},
        ],
    )
    return spec_dir


@pytest.fixture
def multiple_specs(specs_base: Path) -> Path:
    """Create multiple specs in both active and archive."""
    spec1 = specs_base / "active" / "spec-alpha"
    spec1.mkdir()
    create_spec_md(spec1, "SA", "Feature", date(2025, 12, 1), "Active")
    create_tasks_yaml(
        spec1,
        "spec-alpha",
        "SA",
        [{"id": "SA-001", "content": "Alpha task", "status": "pending", "active_form": "Alpha"}],
    )

    spec2 = specs_base / "active" / "spec-beta"
    spec2.mkdir()
    create_spec_md(spec2, "SB", "Task", date(2025, 12, 10), "Active")
    create_tasks_yaml(spec2, "spec-beta", "SB", [])

    spec3 = specs_base / "archive" / "spec-gamma"
    spec3.mkdir()
    create_spec_md(spec3, "SG", "Initiative", date(2025, 11, 1), "Archived")
    create_tasks_yaml(
        spec3,
        "spec-gamma",
        "SG",
        [
            {"id": "SG-001", "content": "Gamma done", "status": "completed", "active_form": "Gamma"},
            {"id": "SG-002", "content": "Gamma also done", "status": "completed", "active_form": "Gamma 2"},
        ],
    )

    return specs_base


# Task Commands: dignity spec task add


def test_spec_task_add_success(empty_spec: Path) -> None:
    """Adding a task returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "Write tests", "Writing tests"],
    )
    assert result.exit_code == 0


def test_spec_task_add_shows_task_id(empty_spec: Path) -> None:
    """Adding a task outputs the generated task ID."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "Write tests", "Writing tests"],
    )
    assert "ES-001" in result.stdout


def test_spec_task_add_shows_content(empty_spec: Path) -> None:
    """Adding a task outputs the task content."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "Write tests", "Writing tests"],
    )
    assert "Write tests" in result.stdout


def test_spec_task_add_persists_to_file(empty_spec: Path) -> None:
    """Adding a task persists to tasks.yaml."""
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "Write tests", "Writing tests"],
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 1
    assert content["tasks"][0]["content"] == "Write tests"


def test_spec_task_add_increments_id(active_spec: Path) -> None:
    """Adding task to spec with existing tasks uses next ID."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(active_spec), "Fourth task", "Fourth task"],
    )
    assert "TF-004" in result.stdout


def test_spec_task_add_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Adding task to nonexistent spec returns error exit code."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(nonexistent), "Task", "Task"],
    )
    assert result.exit_code != 0


def test_spec_task_add_nonexistent_spec_shows_error(tmp_path: Path) -> None:
    """Adding task to nonexistent spec shows error message."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(nonexistent), "Task", "Task"],
    )
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


# Task Commands: dignity spec task complete


def test_spec_task_complete_success(active_spec: Path) -> None:
    """Completing a task returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-003"],
    )
    assert result.exit_code == 0


def test_spec_task_complete_shows_task_id(active_spec: Path) -> None:
    """Completing a task outputs the task ID."""
    result = runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-003"],
    )
    assert "TF-003" in result.stdout


def test_spec_task_complete_shows_completed_status(active_spec: Path) -> None:
    """Completing a task shows completed status."""
    result = runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-003"],
    )
    assert "completed" in result.stdout.lower()


def test_spec_task_complete_persists(active_spec: Path) -> None:
    """Completing a task persists the status change."""
    runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-003"],
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    task = next(t for t in content["tasks"] if t["id"] == "TF-003")
    assert task["status"] == "completed"


def test_spec_task_complete_nonexistent_task_fails(active_spec: Path) -> None:
    """Completing nonexistent task returns error exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-999"],
    )
    assert result.exit_code != 0


def test_spec_task_complete_nonexistent_task_shows_error(active_spec: Path) -> None:
    """Completing nonexistent task shows error message."""
    result = runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-999"],
    )
    assert "TF-999" in result.stdout or "not found" in result.stdout.lower()


# Task Commands: dignity spec task start


def test_spec_task_start_success(active_spec: Path) -> None:
    """Starting a task returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "start", str(active_spec), "TF-003"],
    )
    assert result.exit_code == 0


def test_spec_task_start_shows_task_id(active_spec: Path) -> None:
    """Starting a task outputs the task ID."""
    result = runner.invoke(
        app,
        ["spec", "task", "start", str(active_spec), "TF-003"],
    )
    assert "TF-003" in result.stdout


def test_spec_task_start_shows_in_progress_status(active_spec: Path) -> None:
    """Starting a task shows in_progress status."""
    result = runner.invoke(
        app,
        ["spec", "task", "start", str(active_spec), "TF-003"],
    )
    assert "in_progress" in result.stdout.lower() or "in progress" in result.stdout.lower()


def test_spec_task_start_persists(active_spec: Path) -> None:
    """Starting a task persists the status change."""
    runner.invoke(
        app,
        ["spec", "task", "start", str(active_spec), "TF-003"],
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    task = next(t for t in content["tasks"] if t["id"] == "TF-003")
    assert task["status"] == "in_progress"


def test_spec_task_start_nonexistent_task_fails(active_spec: Path) -> None:
    """Starting nonexistent task returns error exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "start", str(active_spec), "TF-999"],
    )
    assert result.exit_code != 0


def test_spec_task_start_nonexistent_task_shows_error(active_spec: Path) -> None:
    """Starting nonexistent task shows error message."""
    result = runner.invoke(
        app,
        ["spec", "task", "start", str(active_spec), "TF-999"],
    )
    assert "TF-999" in result.stdout or "not found" in result.stdout.lower()


# Task Commands: dignity spec task discard


def test_spec_task_discard_success(active_spec: Path) -> None:
    """Discarding a task returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "discard", str(active_spec), "TF-003"],
    )
    assert result.exit_code == 0


def test_spec_task_discard_shows_confirmation(active_spec: Path) -> None:
    """Discarding a task outputs confirmation."""
    result = runner.invoke(
        app,
        ["spec", "task", "discard", str(active_spec), "TF-003"],
    )
    assert "TF-003" in result.stdout or "discard" in result.stdout.lower()


def test_spec_task_discard_removes_from_file(active_spec: Path) -> None:
    """Discarding a task removes it from tasks.yaml."""
    runner.invoke(
        app,
        ["spec", "task", "discard", str(active_spec), "TF-003"],
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    task_ids = [t["id"] for t in content["tasks"]]
    assert "TF-003" not in task_ids


def test_spec_task_discard_preserves_others(active_spec: Path) -> None:
    """Discarding a task preserves other tasks."""
    runner.invoke(
        app,
        ["spec", "task", "discard", str(active_spec), "TF-003"],
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 2


def test_spec_task_discard_nonexistent_task_fails(active_spec: Path) -> None:
    """Discarding nonexistent task returns error exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "discard", str(active_spec), "TF-999"],
    )
    assert result.exit_code != 0


def test_spec_task_discard_nonexistent_task_shows_error(active_spec: Path) -> None:
    """Discarding nonexistent task shows error message."""
    result = runner.invoke(
        app,
        ["spec", "task", "discard", str(active_spec), "TF-999"],
    )
    assert "TF-999" in result.stdout or "not found" in result.stdout.lower()


# Task Commands: dignity spec task list


def test_spec_task_list_success(active_spec: Path) -> None:
    """Listing tasks returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "list", str(active_spec)],
    )
    assert result.exit_code == 0


def test_spec_task_list_shows_all_task_ids(active_spec: Path) -> None:
    """Listing tasks shows all task IDs."""
    result = runner.invoke(
        app,
        ["spec", "task", "list", str(active_spec)],
    )
    assert "TF-001" in result.stdout
    assert "TF-002" in result.stdout
    assert "TF-003" in result.stdout


def test_spec_task_list_shows_content(active_spec: Path) -> None:
    """Listing tasks shows task content."""
    result = runner.invoke(
        app,
        ["spec", "task", "list", str(active_spec)],
    )
    assert "First task" in result.stdout
    assert "Second task" in result.stdout
    assert "Third task" in result.stdout


def test_spec_task_list_shows_status(active_spec: Path) -> None:
    """Listing tasks shows task status."""
    result = runner.invoke(
        app,
        ["spec", "task", "list", str(active_spec)],
    )
    assert "completed" in result.stdout.lower()
    assert "in_progress" in result.stdout.lower() or "in progress" in result.stdout.lower()
    assert "pending" in result.stdout.lower()


def test_spec_task_list_empty_tasks(empty_spec: Path) -> None:
    """Listing empty tasks shows appropriate message."""
    result = runner.invoke(
        app,
        ["spec", "task", "list", str(empty_spec)],
    )
    assert result.exit_code == 0


def test_spec_task_list_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Listing tasks for nonexistent spec returns error."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "task", "list", str(nonexistent)],
    )
    assert result.exit_code != 0


# Lifecycle Commands: dignity spec archive


def test_spec_archive_success(active_spec: Path) -> None:
    """Archiving a spec returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "archive", str(active_spec)],
    )
    assert result.exit_code == 0


def test_spec_archive_shows_new_location(active_spec: Path, specs_base: Path) -> None:
    """Archiving a spec shows the archive location."""
    result = runner.invoke(
        app,
        ["spec", "archive", str(active_spec)],
    )
    assert "archive" in result.stdout.lower()


def test_spec_archive_moves_directory(active_spec: Path, specs_base: Path) -> None:
    """Archiving a spec moves it from active to archive."""
    runner.invoke(
        app,
        ["spec", "archive", str(active_spec)],
    )
    assert not active_spec.exists()
    assert (specs_base / "archive" / "test-feature").exists()


def test_spec_archive_preserves_files(active_spec: Path, specs_base: Path) -> None:
    """Archiving a spec preserves all files."""
    runner.invoke(
        app,
        ["spec", "archive", str(active_spec)],
    )
    archived = specs_base / "archive" / "test-feature"
    assert (archived / "spec.md").exists()
    assert (archived / "tasks.yaml").exists()


def test_spec_archive_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Archiving nonexistent spec returns error exit code."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "archive", str(nonexistent)],
    )
    assert result.exit_code != 0


def test_spec_archive_nonexistent_spec_shows_error(tmp_path: Path) -> None:
    """Archiving nonexistent spec shows error message."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "archive", str(nonexistent)],
    )
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_spec_archive_already_archived_fails(archived_spec: Path) -> None:
    """Archiving already archived spec returns error."""
    result = runner.invoke(
        app,
        ["spec", "archive", str(archived_spec)],
    )
    assert result.exit_code != 0


# Lifecycle Commands: dignity spec restore


def test_spec_restore_success(archived_spec: Path) -> None:
    """Restoring a spec returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "restore", str(archived_spec)],
    )
    assert result.exit_code == 0


def test_spec_restore_shows_new_location(archived_spec: Path, specs_base: Path) -> None:
    """Restoring a spec shows the active location."""
    result = runner.invoke(
        app,
        ["spec", "restore", str(archived_spec)],
    )
    assert "active" in result.stdout.lower()


def test_spec_restore_moves_directory(archived_spec: Path, specs_base: Path) -> None:
    """Restoring a spec moves it from archive to active."""
    runner.invoke(
        app,
        ["spec", "restore", str(archived_spec)],
    )
    assert not archived_spec.exists()
    assert (specs_base / "active" / "old-feature").exists()


def test_spec_restore_preserves_files(archived_spec: Path, specs_base: Path) -> None:
    """Restoring a spec preserves all files."""
    runner.invoke(
        app,
        ["spec", "restore", str(archived_spec)],
    )
    restored = specs_base / "active" / "old-feature"
    assert (restored / "spec.md").exists()
    assert (restored / "tasks.yaml").exists()


def test_spec_restore_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Restoring nonexistent spec returns error exit code."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "restore", str(nonexistent)],
    )
    assert result.exit_code != 0


def test_spec_restore_nonexistent_spec_shows_error(tmp_path: Path) -> None:
    """Restoring nonexistent spec shows error message."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "restore", str(nonexistent)],
    )
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


def test_spec_restore_already_active_fails(active_spec: Path) -> None:
    """Restoring already active spec returns error."""
    result = runner.invoke(
        app,
        ["spec", "restore", str(active_spec)],
    )
    assert result.exit_code != 0


# Query Commands: dignity spec list


def test_spec_list_success(multiple_specs: Path) -> None:
    """Listing specs returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(multiple_specs)],
    )
    assert result.exit_code == 0


def test_spec_list_shows_all_specs(multiple_specs: Path) -> None:
    """Listing specs shows all spec names."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(multiple_specs)],
    )
    assert "spec-alpha" in result.stdout
    assert "spec-beta" in result.stdout
    assert "spec-gamma" in result.stdout


def test_spec_list_shows_codes(multiple_specs: Path) -> None:
    """Listing specs shows spec codes."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(multiple_specs)],
    )
    assert "SA" in result.stdout
    assert "SB" in result.stdout
    assert "SG" in result.stdout


def test_spec_list_shows_status(multiple_specs: Path) -> None:
    """Listing specs shows status."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(multiple_specs)],
    )
    assert "Active" in result.stdout
    assert "Archived" in result.stdout


def test_spec_list_filter_active(multiple_specs: Path) -> None:
    """Listing specs with active filter shows only active specs."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(multiple_specs), "--status", "Active"],
    )
    assert "spec-alpha" in result.stdout
    assert "spec-beta" in result.stdout
    assert "spec-gamma" not in result.stdout


def test_spec_list_filter_archived(multiple_specs: Path) -> None:
    """Listing specs with archived filter shows only archived specs."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(multiple_specs), "--status", "Archived"],
    )
    assert "spec-alpha" not in result.stdout
    assert "spec-beta" not in result.stdout
    assert "spec-gamma" in result.stdout


def test_spec_list_empty(specs_base: Path) -> None:
    """Listing specs in empty directory shows no specs."""
    result = runner.invoke(
        app,
        ["spec", "list", "--base", str(specs_base)],
    )
    assert result.exit_code == 0


# Query Commands: dignity spec show


def test_spec_show_success(active_spec: Path) -> None:
    """Showing a spec returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "show", str(active_spec)],
    )
    assert result.exit_code == 0


def test_spec_show_displays_name(active_spec: Path) -> None:
    """Showing a spec displays the spec name."""
    result = runner.invoke(
        app,
        ["spec", "show", str(active_spec)],
    )
    assert "test-feature" in result.stdout


def test_spec_show_displays_code(active_spec: Path) -> None:
    """Showing a spec displays the spec code."""
    result = runner.invoke(
        app,
        ["spec", "show", str(active_spec)],
    )
    assert "TF" in result.stdout


def test_spec_show_displays_status(active_spec: Path) -> None:
    """Showing a spec displays the status."""
    result = runner.invoke(
        app,
        ["spec", "show", str(active_spec)],
    )
    assert "Active" in result.stdout


def test_spec_show_displays_issue_type(active_spec: Path) -> None:
    """Showing a spec displays the issue type."""
    result = runner.invoke(
        app,
        ["spec", "show", str(active_spec)],
    )
    assert "Feature" in result.stdout


def test_spec_show_displays_created_date(active_spec: Path) -> None:
    """Showing a spec displays the created date."""
    result = runner.invoke(
        app,
        ["spec", "show", str(active_spec)],
    )
    assert "2025-12-17" in result.stdout


def test_spec_show_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Showing nonexistent spec returns error exit code."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "show", str(nonexistent)],
    )
    assert result.exit_code != 0


def test_spec_show_nonexistent_spec_shows_error(tmp_path: Path) -> None:
    """Showing nonexistent spec shows error message."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "show", str(nonexistent)],
    )
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


# Query Commands: dignity spec progress


def test_spec_progress_success(active_spec: Path) -> None:
    """Getting progress returns success exit code."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert result.exit_code == 0


def test_spec_progress_shows_total(active_spec: Path) -> None:
    """Progress shows total task count."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert "3" in result.stdout or "total" in result.stdout.lower()


def test_spec_progress_shows_completed(active_spec: Path) -> None:
    """Progress shows completed task count."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert "completed" in result.stdout.lower()


def test_spec_progress_shows_in_progress(active_spec: Path) -> None:
    """Progress shows in progress task count."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert "in_progress" in result.stdout.lower() or "in progress" in result.stdout.lower()


def test_spec_progress_shows_pending(active_spec: Path) -> None:
    """Progress shows pending task count."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert "pending" in result.stdout.lower()


def test_spec_progress_shows_percentage(active_spec: Path) -> None:
    """Progress shows completion percentage."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert "%" in result.stdout or "33" in result.stdout


def test_spec_progress_empty_spec(empty_spec: Path) -> None:
    """Progress for empty spec shows 0%."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(empty_spec)],
    )
    assert result.exit_code == 0
    assert "0" in result.stdout


def test_spec_progress_all_completed(archived_spec: Path) -> None:
    """Progress for fully completed spec shows 100%."""
    result = runner.invoke(
        app,
        ["spec", "progress", str(archived_spec)],
    )
    assert "100" in result.stdout


def test_spec_progress_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Progress for nonexistent spec returns error exit code."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "progress", str(nonexistent)],
    )
    assert result.exit_code != 0


def test_spec_progress_nonexistent_spec_shows_error(tmp_path: Path) -> None:
    """Progress for nonexistent spec shows error message."""
    nonexistent = tmp_path / "nonexistent"
    result = runner.invoke(
        app,
        ["spec", "progress", str(nonexistent)],
    )
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()


# Edge Cases and Integration Tests


def test_task_add_with_special_characters(empty_spec: Path) -> None:
    """Adding task with special characters works."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "Task with: colons, \"quotes\", 'apostrophes'", "Special task"],
    )
    assert result.exit_code == 0


def test_task_add_with_long_content(empty_spec: Path) -> None:
    """Adding task with long content works."""
    long_content = "A" * 500
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), long_content, "Long task"],
    )
    assert result.exit_code == 0


def test_list_then_complete_integration(active_spec: Path) -> None:
    """List tasks, complete one, verify list updated."""
    list_result = runner.invoke(
        app,
        ["spec", "task", "list", str(active_spec)],
    )
    assert "pending" in list_result.stdout.lower()

    runner.invoke(
        app,
        ["spec", "task", "complete", str(active_spec), "TF-003"],
    )

    progress_result = runner.invoke(
        app,
        ["spec", "progress", str(active_spec)],
    )
    assert "66" in progress_result.stdout or "67" in progress_result.stdout


def test_archive_then_restore_integration(active_spec: Path, specs_base: Path) -> None:
    """Archive spec, then restore it."""
    archive_result = runner.invoke(
        app,
        ["spec", "archive", str(active_spec)],
    )
    assert archive_result.exit_code == 0

    archived_path = specs_base / "archive" / "test-feature"
    restore_result = runner.invoke(
        app,
        ["spec", "restore", str(archived_path)],
    )
    assert restore_result.exit_code == 0
    assert active_spec.exists()


# JSON Task Commands: dignity spec task add --json


def test_task_add_json_adds_single_task(empty_spec: Path) -> None:
    """Adding a single task via JSON returns success."""
    json_input = '{"content": "Run tests", "status": "pending", "activeForm": "Running tests"}'
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code == 0


def test_task_add_json_single_task_persists(empty_spec: Path) -> None:
    """Adding a single task via JSON persists to tasks.yaml."""
    json_input = '{"content": "Run tests", "status": "pending", "activeForm": "Running tests"}'
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 1
    assert content["tasks"][0]["content"] == "Run tests"


def test_task_add_json_adds_multiple_tasks_from_todos_array(empty_spec: Path) -> None:
    """Adding multiple tasks via todos array returns success."""
    json_input = json.dumps({
        "todos": [
            {"content": "Create types", "status": "completed", "activeForm": "Creating types"},
            {"content": "Write tests", "status": "in_progress", "activeForm": "Writing tests"},
        ]
    })
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code == 0


def test_task_add_json_multiple_tasks_persist_all(empty_spec: Path) -> None:
    """Adding multiple tasks via JSON persists all to tasks.yaml."""
    json_input = json.dumps({
        "todos": [
            {"content": "Create types", "status": "completed", "activeForm": "Creating types"},
            {"content": "Write tests", "status": "in_progress", "activeForm": "Writing tests"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 2


def test_task_add_json_preserves_completed_status(empty_spec: Path) -> None:
    """Adding task with completed status preserves it."""
    json_input = '{"content": "Done task", "status": "completed", "activeForm": "Done task"}'
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "completed"


def test_task_add_json_preserves_in_progress_status(empty_spec: Path) -> None:
    """Adding task with in_progress status preserves it."""
    json_input = '{"content": "Active task", "status": "in_progress", "activeForm": "Active task"}'
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "in_progress"


def test_task_add_json_generates_sequential_ids(empty_spec: Path) -> None:
    """Adding tasks via JSON generates sequential IDs."""
    json_input = json.dumps({
        "todos": [
            {"content": "First", "status": "pending", "activeForm": "First"},
            {"content": "Second", "status": "pending", "activeForm": "Second"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["id"] == "ES-001"
    assert content["tasks"][1]["id"] == "ES-002"


def test_task_add_json_appends_to_existing(active_spec: Path) -> None:
    """Adding tasks via JSON appends to existing tasks."""
    json_input = '{"content": "New task", "status": "pending", "activeForm": "New task"}'
    runner.invoke(
        app,
        ["spec", "task", "add", str(active_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 4
    assert content["tasks"][3]["id"] == "TF-004"


def test_task_add_json_outputs_added_ids(empty_spec: Path) -> None:
    """Adding tasks via JSON outputs the added task IDs."""
    json_input = json.dumps({
        "todos": [
            {"content": "First", "status": "pending", "activeForm": "First"},
            {"content": "Second", "status": "pending", "activeForm": "Second"},
        ]
    })
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    assert "ES-001" in result.stdout
    assert "ES-002" in result.stdout


def test_task_add_json_invalid_json_fails(empty_spec: Path) -> None:
    """Adding task with invalid JSON returns error."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input="not valid json",
    )
    assert result.exit_code != 0


def test_task_add_json_invalid_json_shows_error(empty_spec: Path) -> None:
    """Adding task with invalid JSON shows error message."""
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input="not valid json",
    )
    assert "error" in result.stdout.lower() or "json" in result.stdout.lower()


def test_task_add_json_missing_content_fails(empty_spec: Path) -> None:
    """Adding task without content field returns error."""
    json_input = '{"status": "pending", "activeForm": "Test"}'
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code != 0


def test_task_add_json_missing_activeform_fails(empty_spec: Path) -> None:
    """Adding task without activeForm field returns error."""
    json_input = '{"content": "Test", "status": "pending"}'
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code != 0


def test_task_add_json_empty_todos_array_succeeds(empty_spec: Path) -> None:
    """Adding empty todos array returns success with no tasks added."""
    json_input = '{"todos": []}'
    result = runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code == 0
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 0


def test_task_add_json_defaults_status_to_pending(empty_spec: Path) -> None:
    """Adding task without status field defaults to pending."""
    json_input = '{"content": "No status task", "activeForm": "No status task"}'
    runner.invoke(
        app,
        ["spec", "task", "add", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "pending"


# JSON Task Commands: dignity spec task sync --json


def test_task_sync_json_replaces_all_tasks(active_spec: Path) -> None:
    """Syncing tasks replaces all existing tasks."""
    json_input = json.dumps({
        "todos": [
            {"content": "New task 1", "status": "pending", "activeForm": "New task 1"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 1
    assert content["tasks"][0]["content"] == "New task 1"


def test_task_sync_json_returns_success(active_spec: Path) -> None:
    """Syncing tasks returns success exit code."""
    json_input = json.dumps({
        "todos": [
            {"content": "Task 1", "status": "pending", "activeForm": "Task 1"},
        ]
    })
    result = runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code == 0


def test_task_sync_json_resets_id_counter(active_spec: Path) -> None:
    """Syncing tasks resets the ID counter based on new task count."""
    json_input = json.dumps({
        "todos": [
            {"content": "Task 1", "status": "pending", "activeForm": "Task 1"},
            {"content": "Task 2", "status": "pending", "activeForm": "Task 2"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    assert content["next_id"] == 3


def test_task_sync_json_generates_fresh_ids(active_spec: Path) -> None:
    """Syncing tasks generates fresh sequential IDs for all tasks."""
    json_input = json.dumps({
        "todos": [
            {"content": "Task A", "status": "completed", "activeForm": "Task A"},
            {"content": "Task B", "status": "in_progress", "activeForm": "Task B"},
            {"content": "Task C", "status": "pending", "activeForm": "Task C"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["id"] == "TF-001"
    assert content["tasks"][1]["id"] == "TF-002"
    assert content["tasks"][2]["id"] == "TF-003"


def test_task_sync_json_empty_todos_clears_all(active_spec: Path) -> None:
    """Syncing with empty todos array clears all tasks."""
    json_input = '{"todos": []}'
    runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    assert len(content["tasks"]) == 0
    assert content["next_id"] == 1


def test_task_sync_json_preserves_completed_status(empty_spec: Path) -> None:
    """Syncing tasks preserves completed status."""
    json_input = json.dumps({
        "todos": [
            {"content": "Done", "status": "completed", "activeForm": "Done"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "completed"


def test_task_sync_json_preserves_in_progress_status(empty_spec: Path) -> None:
    """Syncing tasks preserves in_progress status."""
    json_input = json.dumps({
        "todos": [
            {"content": "Working", "status": "in_progress", "activeForm": "Working"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "in_progress"


def test_task_sync_json_preserves_pending_status(empty_spec: Path) -> None:
    """Syncing tasks preserves pending status."""
    json_input = json.dumps({
        "todos": [
            {"content": "Waiting", "status": "pending", "activeForm": "Waiting"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "pending"


def test_task_sync_json_invalid_json_fails(active_spec: Path) -> None:
    """Syncing with invalid JSON returns error."""
    result = runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input="not valid json",
    )
    assert result.exit_code != 0


def test_task_sync_json_missing_todos_key_fails(active_spec: Path) -> None:
    """Syncing without todos key returns error."""
    json_input = '{"content": "Task", "status": "pending"}'
    result = runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    assert result.exit_code != 0


def test_task_sync_json_outputs_summary(active_spec: Path) -> None:
    """Syncing outputs a summary of synced tasks."""
    json_input = json.dumps({
        "todos": [
            {"content": "Task 1", "status": "pending", "activeForm": "Task 1"},
            {"content": "Task 2", "status": "pending", "activeForm": "Task 2"},
            {"content": "Task 3", "status": "pending", "activeForm": "Task 3"},
        ]
    })
    result = runner.invoke(
        app,
        ["spec", "task", "sync", str(active_spec), "--json"],
        input=json_input,
    )
    assert "3" in result.stdout
    assert "sync" in result.stdout.lower() or "task" in result.stdout.lower()


def test_task_sync_json_nonexistent_spec_fails(tmp_path: Path) -> None:
    """Syncing to nonexistent spec returns error."""
    nonexistent = tmp_path / "nonexistent"
    json_input = '{"todos": []}'
    result = runner.invoke(
        app,
        ["spec", "task", "sync", str(nonexistent), "--json"],
        input=json_input,
    )
    assert result.exit_code != 0


def test_task_sync_json_defaults_status_to_pending(empty_spec: Path) -> None:
    """Syncing task without status field defaults to pending."""
    json_input = json.dumps({
        "todos": [
            {"content": "No status", "activeForm": "No status"},
        ]
    })
    runner.invoke(
        app,
        ["spec", "task", "sync", str(empty_spec), "--json"],
        input=json_input,
    )
    content = yaml.safe_load((empty_spec / "tasks.yaml").read_text())
    assert content["tasks"][0]["status"] == "pending"


# Task Commands: dignity spec task update


def test_task_update_content_only(active_spec: Path) -> None:
    """Updating only content changes just that field."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--content", "Updated content"],
    )
    assert result.exit_code == 0


def test_task_update_status_only(active_spec: Path) -> None:
    """Updating only status changes just that field."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-003", "--status", "completed"],
    )
    assert result.exit_code == 0


def test_task_update_active_form_only(active_spec: Path) -> None:
    """Updating only active_form changes just that field."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--active-form", "New active form"],
    )
    assert result.exit_code == 0


def test_task_update_multiple_fields(active_spec: Path) -> None:
    """Updating multiple fields at once works."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--content", "New content", "--status", "completed"],
    )
    assert result.exit_code == 0


def test_task_update_all_fields(active_spec: Path) -> None:
    """Updating all fields at once works."""
    result = runner.invoke(
        app,
        [
            "spec", "task", "update", str(active_spec), "TF-002",
            "--content", "All new content",
            "--active-form", "All new active form",
            "--status", "pending",
        ],
    )
    assert result.exit_code == 0


def test_task_update_persists_changes(active_spec: Path) -> None:
    """Updating a task persists the changes to tasks.yaml."""
    runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--content", "Persisted content"],
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    task = next(t for t in content["tasks"] if t["id"] == "TF-002")
    assert task["content"] == "Persisted content"


def test_task_update_preserves_unchanged_fields(active_spec: Path) -> None:
    """Updating a task preserves fields that were not specified."""
    runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--content", "New content only"],
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    task = next(t for t in content["tasks"] if t["id"] == "TF-002")
    assert task["content"] == "New content only"
    assert task["status"] == "in_progress"
    assert task["active_form"] == "Working on second"


def test_task_update_creates_nonexistent_task(active_spec: Path) -> None:
    """Updating nonexistent task creates it (upsert)."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-999", "--content", "New task", "--active-form", "Creating new"],
    )
    assert result.exit_code == 0
    assert "Created" in result.stdout
    assert "TF-999" in result.stdout


def test_task_update_create_requires_content_and_active_form(active_spec: Path) -> None:
    """Creating via update requires both content and active_form."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-999", "--content", "Only content"],
    )
    assert result.exit_code != 0


def test_task_update_invalid_status_fails(active_spec: Path) -> None:
    """Updating with invalid status returns error exit code."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--status", "invalid_status"],
    )
    assert result.exit_code != 0


def test_task_update_json_single_task(active_spec: Path) -> None:
    """Updating task via JSON single task format works."""
    json_input = '{"content": "JSON updated content", "status": "completed", "activeForm": "JSON active"}'
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--json"],
        input=json_input,
    )
    assert result.exit_code == 0


def test_task_update_json_partial_update(active_spec: Path) -> None:
    """Updating task via JSON with partial fields preserves others."""
    json_input = '{"content": "Partial JSON update"}'
    runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--json"],
        input=json_input,
    )
    content = yaml.safe_load((active_spec / "tasks.yaml").read_text())
    task = next(t for t in content["tasks"] if t["id"] == "TF-002")
    assert task["content"] == "Partial JSON update"
    assert task["status"] == "in_progress"
    assert task["active_form"] == "Working on second"


def test_task_update_json_invalid_fails(active_spec: Path) -> None:
    """Updating task with invalid JSON returns error."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--json"],
        input="not valid json",
    )
    assert result.exit_code != 0


def test_task_update_outputs_confirmation(active_spec: Path) -> None:
    """Updating a task outputs confirmation with task ID."""
    result = runner.invoke(
        app,
        ["spec", "task", "update", str(active_spec), "TF-002", "--content", "Confirmed content"],
    )
    assert "TF-002" in result.stdout
