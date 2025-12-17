"""Tests for spec name resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from dignity.spec.query import SpecNotFoundError


@pytest.fixture
def specs_dirs(tmp_path: Path) -> Path:
    """Create specs directory structure with active and archive subdirectories."""
    active = tmp_path / "specs" / "active"
    archive = tmp_path / "specs" / "archive"
    active.mkdir(parents=True)
    archive.mkdir(parents=True)
    return tmp_path


def test_resolve_spec_finds_active_spec(tmp_path: Path) -> None:
    """resolve_spec should find a spec in the active directory."""
    from dignity.settings import Settings
    from dignity.spec.resolve import resolve_spec

    active_dir = tmp_path / "specs" / "active"
    active_dir.mkdir(parents=True)
    (tmp_path / "specs" / "archive").mkdir(parents=True)

    spec_dir = active_dir / "my-feature"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text("# My Feature")

    settings = Settings(specs_dir=tmp_path / "specs")
    result = resolve_spec("my-feature", settings=settings)

    assert result == spec_dir


def test_resolve_spec_finds_archived_spec(tmp_path: Path) -> None:
    """resolve_spec should find a spec in the archive directory."""
    from dignity.settings import Settings
    from dignity.spec.resolve import resolve_spec

    (tmp_path / "specs" / "active").mkdir(parents=True)
    archive_dir = tmp_path / "specs" / "archive"
    archive_dir.mkdir(parents=True)

    spec_dir = archive_dir / "old-feature"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text("# Old Feature")

    settings = Settings(specs_dir=tmp_path / "specs")
    result = resolve_spec("old-feature", settings=settings)

    assert result == spec_dir


def test_resolve_spec_prefers_active_over_archive(tmp_path: Path) -> None:
    """resolve_spec should return active spec when both active and archive exist."""
    from dignity.settings import Settings
    from dignity.spec.resolve import resolve_spec

    active_dir = tmp_path / "specs" / "active"
    archive_dir = tmp_path / "specs" / "archive"
    active_dir.mkdir(parents=True)
    archive_dir.mkdir(parents=True)

    active_spec = active_dir / "my-feature"
    active_spec.mkdir()
    (active_spec / "spec.md").write_text("# Active version")

    archive_spec = archive_dir / "my-feature"
    archive_spec.mkdir()
    (archive_spec / "spec.md").write_text("# Archived version")

    settings = Settings(specs_dir=tmp_path / "specs")
    result = resolve_spec("my-feature", settings=settings)

    assert result == active_spec


def test_resolve_spec_raises_for_nonexistent(tmp_path: Path) -> None:
    """resolve_spec should raise SpecNotFoundError for nonexistent spec."""
    from dignity.settings import Settings
    from dignity.spec.resolve import resolve_spec

    (tmp_path / "specs" / "active").mkdir(parents=True)
    (tmp_path / "specs" / "archive").mkdir(parents=True)

    settings = Settings(specs_dir=tmp_path / "specs")

    with pytest.raises(SpecNotFoundError):
        resolve_spec("nonexistent-spec", settings=settings)


def test_resolve_spec_uses_custom_settings(tmp_path: Path) -> None:
    """resolve_spec should use provided settings instead of defaults."""
    from dignity.settings import Settings
    from dignity.spec.resolve import resolve_spec

    custom_specs = tmp_path / "custom" / "location"
    active_dir = custom_specs / "active"
    active_dir.mkdir(parents=True)
    (custom_specs / "archive").mkdir(parents=True)

    spec_dir = active_dir / "custom-spec"
    spec_dir.mkdir()
    (spec_dir / "spec.md").write_text("# Custom Spec")

    settings = Settings(specs_dir=custom_specs)
    result = resolve_spec("custom-spec", settings=settings)

    assert result == spec_dir
