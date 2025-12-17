"""Tests for spec query operations."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from dignity.spec.query import (
    SpecNotFoundError,
    find_by_code,
    get_progress,
    get_spec,
    list_specs,
)
from dignity.spec.types import Spec


# Fixtures


@pytest.fixture
def specs_base(tmp_path: Path) -> Path:
    """Create a specs base directory with active and archive subdirectories."""
    active = tmp_path / "active"
    archive = tmp_path / "archive"
    active.mkdir()
    archive.mkdir()
    return tmp_path


def create_spec_md(spec_dir: Path, code: str, issue_type: str, created: date, status: str) -> None:
    """Helper to create a spec.md file with frontmatter."""
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
) -> None:
    """Helper to create a tasks.yaml file."""
    content = {
        "spec": spec_name,
        "code": code,
        "next_id": len(tasks) + 1,
        "tasks": tasks,
    }
    (spec_dir / "tasks.yaml").write_text(yaml.dump(content))


@pytest.fixture
def active_spec(specs_base: Path) -> Path:
    """Create an active spec directory."""
    spec_dir = specs_base / "active" / "feature-one"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "FO", "Feature", date(2025, 12, 17), "Active")
    create_tasks_yaml(
        spec_dir,
        "feature-one",
        "FO",
        [
            {"id": "FO-001", "content": "Task 1", "status": "completed", "active_form": "Task 1"},
            {"id": "FO-002", "content": "Task 2", "status": "in_progress", "active_form": "Task 2"},
            {"id": "FO-003", "content": "Task 3", "status": "pending", "active_form": "Task 3"},
        ],
    )
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
            {"id": "OF-001", "content": "Done", "status": "completed", "active_form": "Done"},
            {"id": "OF-002", "content": "Also done", "status": "completed", "active_form": "Also done"},
        ],
    )
    return spec_dir


@pytest.fixture
def multiple_specs(specs_base: Path) -> Path:
    """Create multiple specs in both active and archive."""
    spec1 = specs_base / "active" / "spec-alpha"
    spec1.mkdir()
    create_spec_md(spec1, "SA", "Feature", date(2025, 12, 1), "Active")
    create_tasks_yaml(spec1, "spec-alpha", "SA", [])

    spec2 = specs_base / "active" / "spec-beta"
    spec2.mkdir()
    create_spec_md(spec2, "SB", "Task", date(2025, 12, 10), "Active")
    create_tasks_yaml(spec2, "spec-beta", "SB", [])

    spec3 = specs_base / "archive" / "spec-gamma"
    spec3.mkdir()
    create_spec_md(spec3, "SG", "Initiative", date(2025, 11, 1), "Archived")
    create_tasks_yaml(spec3, "spec-gamma", "SG", [])

    return specs_base


# SpecNotFoundError tests


def test_spec_not_found_error_is_exception() -> None:
    assert issubclass(SpecNotFoundError, Exception)


def test_spec_not_found_error_stores_path() -> None:
    error = SpecNotFoundError(Path("/some/path"))
    assert error.path == Path("/some/path")


def test_spec_not_found_error_message() -> None:
    error = SpecNotFoundError(Path("/some/path"))
    assert "/some/path" in str(error)


# get_spec tests - happy path


def test_get_spec_returns_spec(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert isinstance(result, Spec)


def test_get_spec_parses_name_from_directory(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert result.name == "feature-one"


def test_get_spec_parses_code_from_frontmatter(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert result.code == "FO"


def test_get_spec_parses_issue_type_from_frontmatter(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert result.issue_type == "Feature"


def test_get_spec_parses_created_date_from_frontmatter(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert result.created == date(2025, 12, 17)


def test_get_spec_parses_status_from_frontmatter(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert result.status == "Active"


def test_get_spec_stores_path(active_spec: Path) -> None:
    result = get_spec(active_spec)
    assert result.path == active_spec


def test_get_spec_from_archived(archived_spec: Path) -> None:
    result = get_spec(archived_spec)
    assert result.status == "Archived"
    assert result.code == "OF"


# get_spec tests - error cases


def test_get_spec_raises_for_nonexistent_directory(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent"
    with pytest.raises(SpecNotFoundError):
        get_spec(nonexistent)


def test_get_spec_raises_for_missing_spec_md(tmp_path: Path) -> None:
    spec_dir = tmp_path / "no-spec-md"
    spec_dir.mkdir()
    with pytest.raises(SpecNotFoundError):
        get_spec(spec_dir)


def test_get_spec_error_contains_path(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent"
    with pytest.raises(SpecNotFoundError) as exc_info:
        get_spec(nonexistent)
    assert exc_info.value.path == nonexistent


# get_spec tests - edge cases


def test_get_spec_handles_different_date_formats(tmp_path: Path) -> None:
    spec_dir = tmp_path / "date-test"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "DT", "Feature", date(2020, 1, 1), "Active")
    result = get_spec(spec_dir)
    assert result.created == date(2020, 1, 1)


def test_get_spec_handles_single_char_code(tmp_path: Path) -> None:
    spec_dir = tmp_path / "single-code"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "S", "Task", date(2025, 1, 1), "Active")
    result = get_spec(spec_dir)
    assert result.code == "S"


def test_get_spec_handles_long_code(tmp_path: Path) -> None:
    spec_dir = tmp_path / "long-code"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "ABCDEF", "Initiative", date(2025, 1, 1), "Active")
    result = get_spec(spec_dir)
    assert result.code == "ABCDEF"


def test_get_spec_handles_spec_name_with_hyphens(tmp_path: Path) -> None:
    spec_dir = tmp_path / "my-long-spec-name"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "MLS", "Feature", date(2025, 1, 1), "Active")
    result = get_spec(spec_dir)
    assert result.name == "my-long-spec-name"


# list_specs tests - basic functionality


def test_list_specs_returns_list(specs_base: Path) -> None:
    result = list_specs(specs_base)
    assert isinstance(result, list)


def test_list_specs_returns_empty_for_no_specs(specs_base: Path) -> None:
    result = list_specs(specs_base)
    assert result == []


def test_list_specs_returns_single_active_spec(active_spec: Path, specs_base: Path) -> None:
    result = list_specs(specs_base)
    assert len(result) == 1


def test_list_specs_returns_spec_objects(active_spec: Path, specs_base: Path) -> None:
    result = list_specs(specs_base)
    assert all(isinstance(s, Spec) for s in result)


def test_list_specs_returns_active_and_archived(
    active_spec: Path,
    archived_spec: Path,
    specs_base: Path,
) -> None:
    result = list_specs(specs_base)
    assert len(result) == 2


def test_list_specs_returns_multiple_specs(multiple_specs: Path) -> None:
    result = list_specs(multiple_specs)
    assert len(result) == 3


# list_specs tests - status filtering


def test_list_specs_filters_by_active_status(
    active_spec: Path,
    archived_spec: Path,
    specs_base: Path,
) -> None:
    result = list_specs(specs_base, status="Active")
    assert len(result) == 1
    assert result[0].status == "Active"


def test_list_specs_filters_by_archived_status(
    active_spec: Path,
    archived_spec: Path,
    specs_base: Path,
) -> None:
    result = list_specs(specs_base, status="Archived")
    assert len(result) == 1
    assert result[0].status == "Archived"


def test_list_specs_none_status_returns_all(
    active_spec: Path,
    archived_spec: Path,
    specs_base: Path,
) -> None:
    result = list_specs(specs_base, status=None)
    assert len(result) == 2


def test_list_specs_returns_empty_for_nonmatching_status(
    active_spec: Path,
    specs_base: Path,
) -> None:
    result = list_specs(specs_base, status="NonexistentStatus")
    assert result == []


# list_specs tests - edge cases


def test_list_specs_ignores_non_directories(specs_base: Path, active_spec: Path) -> None:
    (specs_base / "active" / "random-file.txt").write_text("not a spec")
    result = list_specs(specs_base)
    assert len(result) == 1


def test_list_specs_ignores_directories_without_spec_md(specs_base: Path, active_spec: Path) -> None:
    invalid_spec = specs_base / "active" / "no-spec-md"
    invalid_spec.mkdir()
    (invalid_spec / "tasks.yaml").write_text("spec: test\ncode: T\ntasks: []")
    result = list_specs(specs_base)
    assert len(result) == 1


def test_list_specs_with_only_archived(archived_spec: Path, specs_base: Path) -> None:
    result = list_specs(specs_base)
    assert len(result) == 1
    assert result[0].status == "Archived"


def test_list_specs_handles_empty_active_dir(specs_base: Path, archived_spec: Path) -> None:
    result = list_specs(specs_base, status="Active")
    assert result == []


def test_list_specs_handles_empty_archive_dir(specs_base: Path, active_spec: Path) -> None:
    result = list_specs(specs_base, status="Archived")
    assert result == []


# find_by_code tests - happy path


def test_find_by_code_returns_spec(active_spec: Path, specs_base: Path) -> None:
    result = find_by_code(specs_base, "FO")
    assert isinstance(result, Spec)


def test_find_by_code_finds_correct_spec(active_spec: Path, specs_base: Path) -> None:
    result = find_by_code(specs_base, "FO")
    assert result is not None
    assert result.code == "FO"
    assert result.name == "feature-one"


def test_find_by_code_finds_archived_spec(archived_spec: Path, specs_base: Path) -> None:
    result = find_by_code(specs_base, "OF")
    assert result is not None
    assert result.code == "OF"
    assert result.status == "Archived"


def test_find_by_code_among_multiple(multiple_specs: Path) -> None:
    result = find_by_code(multiple_specs, "SB")
    assert result is not None
    assert result.code == "SB"
    assert result.name == "spec-beta"


# find_by_code tests - not found


def test_find_by_code_returns_none_for_nonexistent(specs_base: Path) -> None:
    result = find_by_code(specs_base, "NONEXISTENT")
    assert result is None


def test_find_by_code_returns_none_when_empty(specs_base: Path) -> None:
    result = find_by_code(specs_base, "XX")
    assert result is None


def test_find_by_code_returns_none_for_partial_match(active_spec: Path, specs_base: Path) -> None:
    result = find_by_code(specs_base, "F")
    assert result is None


# find_by_code tests - edge cases


def test_find_by_code_case_sensitive(tmp_path: Path) -> None:
    specs_base = tmp_path
    active = specs_base / "active"
    archive = specs_base / "archive"
    active.mkdir()
    archive.mkdir()

    spec_dir = active / "lowercase-spec"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "abc", "Feature", date(2025, 1, 1), "Active")
    create_tasks_yaml(spec_dir, "lowercase-spec", "abc", [])

    result_lower = find_by_code(specs_base, "abc")
    result_upper = find_by_code(specs_base, "ABC")

    assert result_lower is not None
    assert result_lower.code == "abc"
    assert result_upper is None


def test_find_by_code_first_match_when_duplicate_codes(tmp_path: Path) -> None:
    specs_base = tmp_path
    active = specs_base / "active"
    archive = specs_base / "archive"
    active.mkdir()
    archive.mkdir()

    spec1 = active / "first-spec"
    spec1.mkdir()
    create_spec_md(spec1, "DUP", "Feature", date(2025, 1, 1), "Active")
    create_tasks_yaml(spec1, "first-spec", "DUP", [])

    spec2 = active / "second-spec"
    spec2.mkdir()
    create_spec_md(spec2, "DUP", "Feature", date(2025, 1, 2), "Active")
    create_tasks_yaml(spec2, "second-spec", "DUP", [])

    result = find_by_code(specs_base, "DUP")
    assert result is not None
    assert result.code == "DUP"


# get_progress tests - happy path


def test_get_progress_returns_dict(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert isinstance(result, dict)


def test_get_progress_has_total_key(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert "total" in result


def test_get_progress_has_completed_key(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert "completed" in result


def test_get_progress_has_in_progress_key(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert "in_progress" in result


def test_get_progress_has_pending_key(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert "pending" in result


def test_get_progress_has_percent_complete_key(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert "percent_complete" in result


def test_get_progress_total_count(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert result["total"] == 3


def test_get_progress_completed_count(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert result["completed"] == 1


def test_get_progress_in_progress_count(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert result["in_progress"] == 1


def test_get_progress_pending_count(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert result["pending"] == 1


def test_get_progress_percent_calculation(active_spec: Path) -> None:
    result = get_progress(active_spec)
    assert result["percent_complete"] == pytest.approx(33.33, rel=0.1)


# get_progress tests - edge cases


def test_get_progress_all_completed(archived_spec: Path) -> None:
    result = get_progress(archived_spec)
    assert result["total"] == 2
    assert result["completed"] == 2
    assert result["in_progress"] == 0
    assert result["pending"] == 0
    assert result["percent_complete"] == 100.0


def test_get_progress_no_tasks(tmp_path: Path) -> None:
    spec_dir = tmp_path / "empty-tasks"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "ET", "Feature", date(2025, 1, 1), "Active")
    create_tasks_yaml(spec_dir, "empty-tasks", "ET", [])

    result = get_progress(spec_dir)
    assert result["total"] == 0
    assert result["completed"] == 0
    assert result["in_progress"] == 0
    assert result["pending"] == 0
    assert result["percent_complete"] == 0.0


def test_get_progress_all_pending(tmp_path: Path) -> None:
    spec_dir = tmp_path / "all-pending"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "AP", "Feature", date(2025, 1, 1), "Active")
    create_tasks_yaml(
        spec_dir,
        "all-pending",
        "AP",
        [
            {"id": "AP-001", "content": "Task 1", "status": "pending", "active_form": "Task 1"},
            {"id": "AP-002", "content": "Task 2", "status": "pending", "active_form": "Task 2"},
        ],
    )

    result = get_progress(spec_dir)
    assert result["total"] == 2
    assert result["pending"] == 2
    assert result["completed"] == 0
    assert result["percent_complete"] == 0.0


def test_get_progress_all_in_progress(tmp_path: Path) -> None:
    spec_dir = tmp_path / "all-in-progress"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "AI", "Feature", date(2025, 1, 1), "Active")
    create_tasks_yaml(
        spec_dir,
        "all-in-progress",
        "AI",
        [
            {"id": "AI-001", "content": "Task 1", "status": "in_progress", "active_form": "Task 1"},
        ],
    )

    result = get_progress(spec_dir)
    assert result["total"] == 1
    assert result["in_progress"] == 1
    assert result["completed"] == 0
    assert result["percent_complete"] == 0.0


# get_progress tests - missing tasks.yaml


def test_get_progress_without_tasks_yaml(tmp_path: Path) -> None:
    spec_dir = tmp_path / "no-tasks"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "NT", "Feature", date(2025, 1, 1), "Active")

    result = get_progress(spec_dir)
    assert result["total"] == 0
    assert result["completed"] == 0
    assert result["in_progress"] == 0
    assert result["pending"] == 0
    assert result["percent_complete"] == 0.0


# get_progress tests - error cases


def test_get_progress_raises_for_nonexistent_directory(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent"
    with pytest.raises(SpecNotFoundError):
        get_progress(nonexistent)


# Integration tests


def test_get_spec_and_list_specs_consistency(active_spec: Path, specs_base: Path) -> None:
    listed = list_specs(specs_base)
    direct = get_spec(active_spec)

    assert len(listed) == 1
    assert listed[0].code == direct.code
    assert listed[0].name == direct.name


def test_find_by_code_and_get_spec_consistency(active_spec: Path, specs_base: Path) -> None:
    found = find_by_code(specs_base, "FO")
    direct = get_spec(active_spec)

    assert found is not None
    assert found.code == direct.code
    assert found.path == direct.path


def test_list_specs_paths_are_valid(multiple_specs: Path) -> None:
    specs = list_specs(multiple_specs)
    for spec in specs:
        assert spec.path.exists()
        assert (spec.path / "spec.md").exists()
