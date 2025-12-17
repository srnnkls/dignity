"""Tests for spec lifecycle operations."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from dignity.spec.lifecycle import archive, restore, set_status
from dignity.spec.query import SpecNotFoundError


# Fixtures


@pytest.fixture
def specs_base(tmp_path: Path) -> Path:
    """Create a specs base directory with active and archive subdirectories."""
    active = tmp_path / "active"
    archive_dir = tmp_path / "archive"
    active.mkdir()
    archive_dir.mkdir()
    return tmp_path


def create_spec_md(
    spec_dir: Path,
    code: str,
    issue_type: str,
    created: date,
    status: str,
) -> None:
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


def read_frontmatter(spec_path: Path) -> dict:
    """Read YAML frontmatter from spec.md."""
    content = (spec_path / "spec.md").read_text()
    if not content.startswith("---"):
        return {}
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}
    frontmatter = content[3:end_idx].strip()
    return yaml.safe_load(frontmatter) or {}


@pytest.fixture
def active_spec(specs_base: Path) -> Path:
    """Create an active spec directory with multiple files."""
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
        ],
    )
    (spec_dir / "context.md").write_text("# Context\n\nSome context here.")
    (spec_dir / "validation-checklist.md").write_text("# Validation\n\n- [ ] Check 1")
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
        ],
    )
    return spec_dir


# archive() tests - happy path


def test_archive_returns_path(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert isinstance(result, Path)


def test_archive_returns_archive_location(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert "archive" in result.parts


def test_archive_moves_spec_directory(active_spec: Path, specs_base: Path) -> None:
    archive(active_spec)
    assert not active_spec.exists()


def test_archive_creates_spec_in_archive(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert result.exists()


def test_archive_preserves_spec_name(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert result.name == "feature-one"


def test_archive_moves_spec_md(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert (result / "spec.md").exists()


def test_archive_moves_tasks_yaml(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert (result / "tasks.yaml").exists()


def test_archive_moves_all_files(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    assert (result / "context.md").exists()
    assert (result / "validation-checklist.md").exists()


def test_archive_updates_status_to_archived(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    frontmatter = read_frontmatter(result)
    assert frontmatter["status"] == "Archived"


def test_archive_preserves_other_frontmatter_fields(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    frontmatter = read_frontmatter(result)
    assert frontmatter["code"] == "FO"
    assert frontmatter["issue_type"] == "Feature"


def test_archive_with_custom_archive_base(active_spec: Path, tmp_path: Path) -> None:
    custom_archive = tmp_path / "custom-archive"
    custom_archive.mkdir()
    result = archive(active_spec, archive_base=custom_archive)
    assert result.parent == custom_archive
    assert result.exists()


def test_archive_infers_archive_base_from_spec_path(active_spec: Path, specs_base: Path) -> None:
    result = archive(active_spec)
    expected_parent = specs_base / "archive"
    assert result.parent == expected_parent


# archive() tests - error cases


def test_archive_raises_for_nonexistent_spec(tmp_path: Path) -> None:
    nonexistent = tmp_path / "active" / "nonexistent"
    with pytest.raises(SpecNotFoundError):
        archive(nonexistent)


def test_archive_error_contains_path(tmp_path: Path) -> None:
    nonexistent = tmp_path / "active" / "nonexistent"
    with pytest.raises(SpecNotFoundError) as exc_info:
        archive(nonexistent)
    assert exc_info.value.path == nonexistent


def test_archive_raises_for_already_archived_spec(archived_spec: Path) -> None:
    with pytest.raises(ValueError):
        archive(archived_spec)


# restore() tests - happy path


def test_restore_returns_path(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    assert isinstance(result, Path)


def test_restore_returns_active_location(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    assert "active" in result.parts


def test_restore_moves_spec_directory(archived_spec: Path, specs_base: Path) -> None:
    restore(archived_spec)
    assert not archived_spec.exists()


def test_restore_creates_spec_in_active(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    assert result.exists()


def test_restore_preserves_spec_name(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    assert result.name == "old-feature"


def test_restore_moves_spec_md(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    assert (result / "spec.md").exists()


def test_restore_moves_tasks_yaml(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    assert (result / "tasks.yaml").exists()


def test_restore_updates_status_to_active(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    frontmatter = read_frontmatter(result)
    assert frontmatter["status"] == "Active"


def test_restore_preserves_other_frontmatter_fields(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    frontmatter = read_frontmatter(result)
    assert frontmatter["code"] == "OF"
    assert frontmatter["issue_type"] == "Feature"


def test_restore_with_custom_active_base(archived_spec: Path, tmp_path: Path) -> None:
    custom_active = tmp_path / "custom-active"
    custom_active.mkdir()
    result = restore(archived_spec, active_base=custom_active)
    assert result.parent == custom_active
    assert result.exists()


def test_restore_infers_active_base_from_spec_path(archived_spec: Path, specs_base: Path) -> None:
    result = restore(archived_spec)
    expected_parent = specs_base / "active"
    assert result.parent == expected_parent


# restore() tests - error cases


def test_restore_raises_for_nonexistent_spec(tmp_path: Path) -> None:
    nonexistent = tmp_path / "archive" / "nonexistent"
    with pytest.raises(SpecNotFoundError):
        restore(nonexistent)


def test_restore_error_contains_path(tmp_path: Path) -> None:
    nonexistent = tmp_path / "archive" / "nonexistent"
    with pytest.raises(SpecNotFoundError) as exc_info:
        restore(nonexistent)
    assert exc_info.value.path == nonexistent


def test_restore_raises_for_already_active_spec(active_spec: Path) -> None:
    with pytest.raises(ValueError):
        restore(active_spec)


# set_status() tests - happy path


def test_set_status_updates_status(active_spec: Path) -> None:
    set_status(active_spec, "In Review")
    frontmatter = read_frontmatter(active_spec)
    assert frontmatter["status"] == "In Review"


def test_set_status_preserves_code(active_spec: Path) -> None:
    set_status(active_spec, "In Review")
    frontmatter = read_frontmatter(active_spec)
    assert frontmatter["code"] == "FO"


def test_set_status_preserves_issue_type(active_spec: Path) -> None:
    set_status(active_spec, "In Review")
    frontmatter = read_frontmatter(active_spec)
    assert frontmatter["issue_type"] == "Feature"


def test_set_status_preserves_created_date(active_spec: Path) -> None:
    set_status(active_spec, "In Review")
    frontmatter = read_frontmatter(active_spec)
    assert frontmatter["created"] == date(2025, 12, 17)


def test_set_status_preserves_body_content(active_spec: Path) -> None:
    original_content = (active_spec / "spec.md").read_text()
    set_status(active_spec, "In Review")
    new_content = (active_spec / "spec.md").read_text()
    assert "# Spec: feature-one" in new_content
    assert "## Overview" in new_content


def test_set_status_to_archived(active_spec: Path) -> None:
    set_status(active_spec, "Archived")
    frontmatter = read_frontmatter(active_spec)
    assert frontmatter["status"] == "Archived"


def test_set_status_to_active(archived_spec: Path) -> None:
    set_status(archived_spec, "Active")
    frontmatter = read_frontmatter(archived_spec)
    assert frontmatter["status"] == "Active"


def test_set_status_custom_value(active_spec: Path) -> None:
    set_status(active_spec, "On Hold")
    frontmatter = read_frontmatter(active_spec)
    assert frontmatter["status"] == "On Hold"


def test_set_status_returns_none(active_spec: Path) -> None:
    result = set_status(active_spec, "In Review")
    assert result is None


# set_status() tests - error cases


def test_set_status_raises_for_nonexistent_spec(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent"
    with pytest.raises(SpecNotFoundError):
        set_status(nonexistent, "Active")


def test_set_status_error_contains_path(tmp_path: Path) -> None:
    nonexistent = tmp_path / "nonexistent"
    with pytest.raises(SpecNotFoundError) as exc_info:
        set_status(nonexistent, "Active")
    assert exc_info.value.path == nonexistent


def test_set_status_raises_for_missing_spec_md(tmp_path: Path) -> None:
    spec_dir = tmp_path / "no-spec-md"
    spec_dir.mkdir()
    with pytest.raises(SpecNotFoundError):
        set_status(spec_dir, "Active")


# Integration tests - archive and restore round trip


def test_archive_then_restore_round_trip(active_spec: Path, specs_base: Path) -> None:
    original_name = active_spec.name
    archived = archive(active_spec)
    restored = restore(archived)
    assert restored.name == original_name
    assert restored.exists()


def test_archive_then_restore_preserves_files(active_spec: Path, specs_base: Path) -> None:
    archived = archive(active_spec)
    restored = restore(archived)
    assert (restored / "spec.md").exists()
    assert (restored / "tasks.yaml").exists()
    assert (restored / "context.md").exists()
    assert (restored / "validation-checklist.md").exists()


def test_archive_then_restore_updates_status_back_to_active(
    active_spec: Path,
    specs_base: Path,
) -> None:
    frontmatter_before = read_frontmatter(active_spec)
    archived = archive(active_spec)
    frontmatter_archived = read_frontmatter(archived)
    restored = restore(archived)
    frontmatter_restored = read_frontmatter(restored)

    assert frontmatter_before["status"] == "Active"
    assert frontmatter_archived["status"] == "Archived"
    assert frontmatter_restored["status"] == "Active"


def test_multiple_archive_restore_cycles(active_spec: Path, specs_base: Path) -> None:
    archived = archive(active_spec)
    restored = restore(archived)
    archived_again = archive(restored)
    restored_again = restore(archived_again)
    assert restored_again.exists()
    assert (restored_again / "spec.md").exists()


# Edge cases


def test_archive_spec_with_nested_directory(specs_base: Path) -> None:
    spec_dir = specs_base / "active" / "nested-spec"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "NS", "Feature", date(2025, 12, 17), "Active")
    subdir = spec_dir / "attachments"
    subdir.mkdir()
    (subdir / "file.txt").write_text("attachment content")

    result = archive(spec_dir)
    assert (result / "attachments" / "file.txt").exists()
    assert (result / "attachments" / "file.txt").read_text() == "attachment content"


def test_restore_spec_with_nested_directory(specs_base: Path) -> None:
    spec_dir = specs_base / "archive" / "nested-archived"
    spec_dir.mkdir()
    create_spec_md(spec_dir, "NA", "Feature", date(2025, 12, 17), "Archived")
    subdir = spec_dir / "docs"
    subdir.mkdir()
    (subdir / "notes.md").write_text("# Notes")

    result = restore(spec_dir)
    assert (result / "docs" / "notes.md").exists()


def test_set_status_with_multiline_frontmatter(tmp_path: Path) -> None:
    spec_dir = tmp_path / "multiline"
    spec_dir.mkdir()
    content = """---
code: ML
issue_type: Feature
created: 2025-12-17
status: Active
description: |
  This is a multiline
  description field
tags:
  - feature
  - important
---

# Spec: multiline

## Overview

Content here.
"""
    (spec_dir / "spec.md").write_text(content)

    set_status(spec_dir, "Completed")
    frontmatter = read_frontmatter(spec_dir)

    assert frontmatter["status"] == "Completed"
    assert "multiline" in frontmatter.get("description", "")
    assert "feature" in frontmatter.get("tags", [])
