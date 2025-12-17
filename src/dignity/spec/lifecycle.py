"""Spec lifecycle operations: archive, restore, and status management."""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from dignity.spec.query import SpecNotFoundError


def _parse_spec_md(spec_path: Path) -> tuple[dict, str]:
    """Parse spec.md into frontmatter dict and body content."""
    spec_md = spec_path / "spec.md"
    if not spec_md.exists():
        raise SpecNotFoundError(spec_path)

    content = spec_md.read_text()
    if not content.startswith("---"):
        return {}, content

    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}, content

    frontmatter_str = content[3:end_idx].strip()
    body = content[end_idx + 3:].lstrip("\n")
    frontmatter = yaml.safe_load(frontmatter_str) or {}
    return frontmatter, body


def _write_spec_md(spec_path: Path, frontmatter: dict, body: str) -> None:
    """Write frontmatter and body back to spec.md."""
    spec_md = spec_path / "spec.md"
    frontmatter_str = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    content = f"---\n{frontmatter_str}---\n{body}"
    spec_md.write_text(content)


def set_status(spec_path: Path, status: str) -> None:
    """Update the status field in spec.md frontmatter."""
    if not spec_path.exists():
        raise SpecNotFoundError(spec_path)

    frontmatter, body = _parse_spec_md(spec_path)
    frontmatter["status"] = status
    _write_spec_md(spec_path, frontmatter, body)


def archive(spec_path: Path, archive_base: Path | None = None) -> Path:
    """Move spec from active to archive directory."""
    if not spec_path.exists():
        raise SpecNotFoundError(spec_path)

    if "archive" in spec_path.parts:
        raise ValueError(f"Spec is already archived: {spec_path}")

    if archive_base is None:
        archive_base = spec_path.parent.parent / "archive"

    dest_path = archive_base / spec_path.name
    shutil.move(str(spec_path), str(dest_path))

    set_status(dest_path, "Archived")

    return dest_path


def restore(spec_path: Path, active_base: Path | None = None) -> Path:
    """Move spec from archive to active directory."""
    if not spec_path.exists():
        raise SpecNotFoundError(spec_path)

    if "active" in spec_path.parts:
        raise ValueError(f"Spec is already active: {spec_path}")

    if active_base is None:
        active_base = spec_path.parent.parent / "active"

    dest_path = active_base / spec_path.name
    shutil.move(str(spec_path), str(dest_path))

    set_status(dest_path, "Active")

    return dest_path
