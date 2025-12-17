"""Tests for spec index management.

Tests cover:
- load_index: Load codes from specs/index.yaml
- save_index: Write codes dict to specs/index.yaml
- add_entry: Add new code -> name mapping
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dignity.spec.index import add_entry, load_index, save_index


# load_index tests


def test_load_index_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    """Missing index file returns empty dict."""
    index_path = tmp_path / "specs" / "index.yaml"
    result = load_index(index_path)
    assert result == {}


def test_load_index_empty_file_returns_empty_dict(tmp_path: Path) -> None:
    """Empty index file returns empty dict."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("")
    result = load_index(index_path)
    assert result == {}


def test_load_index_loads_single_entry(tmp_path: Path) -> None:
    """Loads single code -> name mapping."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("codes:\n  FSD: focus-state-dispatch\n")
    result = load_index(index_path)
    assert result == {"FSD": "focus-state-dispatch"}


def test_load_index_loads_multiple_entries(tmp_path: Path) -> None:
    """Loads multiple code -> name mappings."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        "codes:\n  FSD: focus-state-dispatch\n  HM: hook-migration\n"
    )
    result = load_index(index_path)
    assert result == {"FSD": "focus-state-dispatch", "HM": "hook-migration"}


def test_load_index_missing_codes_key_returns_empty_dict(tmp_path: Path) -> None:
    """File without 'codes' key returns empty dict."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("other_key: value\n")
    result = load_index(index_path)
    assert result == {}


# save_index tests


def test_save_index_saves_empty_dict(tmp_path: Path) -> None:
    """Saves empty codes dict."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    save_index(index_path, {})
    content = index_path.read_text()
    assert "codes:" in content or content == ""


def test_save_index_saves_single_entry(tmp_path: Path) -> None:
    """Saves single code -> name mapping."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    save_index(index_path, {"FSD": "focus-state-dispatch"})
    content = index_path.read_text()
    assert "codes:" in content
    assert "FSD:" in content
    assert "focus-state-dispatch" in content


def test_save_index_saves_multiple_entries(tmp_path: Path) -> None:
    """Saves multiple code -> name mappings."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    save_index(
        index_path, {"FSD": "focus-state-dispatch", "HM": "hook-migration"}
    )
    content = index_path.read_text()
    assert "FSD:" in content
    assert "HM:" in content


def test_save_index_creates_parent_directories(tmp_path: Path) -> None:
    """Creates parent directories if they don't exist."""
    index_path = tmp_path / "nested" / "specs" / "index.yaml"
    save_index(index_path, {"FSD": "focus-state-dispatch"})
    assert index_path.exists()
    content = index_path.read_text()
    assert "FSD:" in content


def test_save_index_overwrites_existing_file(tmp_path: Path) -> None:
    """Overwrites existing file content."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("codes:\n  OLD: old-spec\n")
    save_index(index_path, {"NEW": "new-spec"})
    content = index_path.read_text()
    assert "NEW:" in content
    assert "OLD:" not in content


# add_entry tests


def test_add_entry_creates_file_if_missing(tmp_path: Path) -> None:
    """Creates index file if it doesn't exist."""
    index_path = tmp_path / "specs" / "index.yaml"
    add_entry(index_path, "FSD", "focus-state-dispatch")
    assert index_path.exists()
    content = index_path.read_text()
    assert "FSD:" in content
    assert "focus-state-dispatch" in content


def test_add_entry_adds_to_empty_file(tmp_path: Path) -> None:
    """Adds entry to empty index file."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("")
    add_entry(index_path, "FSD", "focus-state-dispatch")
    result = load_index(index_path)
    assert result == {"FSD": "focus-state-dispatch"}


def test_add_entry_appends_to_existing_entries(tmp_path: Path) -> None:
    """Appends new entry to existing entries."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("codes:\n  HM: hook-migration\n")
    add_entry(index_path, "FSD", "focus-state-dispatch")
    result = load_index(index_path)
    assert result == {"HM": "hook-migration", "FSD": "focus-state-dispatch"}


def test_add_entry_overwrites_existing_code(tmp_path: Path) -> None:
    """Overwrites entry if code already exists."""
    index_path = tmp_path / "specs" / "index.yaml"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("codes:\n  FSD: old-name\n")
    add_entry(index_path, "FSD", "new-name")
    result = load_index(index_path)
    assert result == {"FSD": "new-name"}


def test_add_entry_creates_parent_directories(tmp_path: Path) -> None:
    """Creates parent directories if they don't exist."""
    index_path = tmp_path / "nested" / "specs" / "index.yaml"
    add_entry(index_path, "FSD", "focus-state-dispatch")
    assert index_path.exists()
