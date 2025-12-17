"""Spec lookup and querying."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from dignity.spec.tasks import load_tasks
from dignity.spec.types import Spec, Status


class SpecNotFoundError(Exception):
    """Raised when a spec is not found."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Spec not found: {path}")


def _parse_frontmatter(spec_md_path: Path) -> dict:
    """Parse YAML frontmatter from spec.md file."""
    content = spec_md_path.read_text()
    if not content.startswith("---"):
        return {}

    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}

    frontmatter = content[3:end_idx].strip()
    return yaml.safe_load(frontmatter) or {}


def get_spec(spec_path: Path) -> Spec:
    """Load Spec from directory."""
    if not spec_path.exists():
        raise SpecNotFoundError(spec_path)

    spec_md = spec_path / "spec.md"
    if not spec_md.exists():
        raise SpecNotFoundError(spec_path)

    frontmatter = _parse_frontmatter(spec_md)

    created_value = frontmatter.get("created")
    if isinstance(created_value, date):
        created = created_value
    elif created_value is not None:
        created = date.fromisoformat(created_value)
    else:
        created = date.today()

    return Spec(
        name=spec_path.name,
        code=frontmatter.get("code", ""),
        issue_type=frontmatter.get("issue_type", ""),
        created=created,
        status=frontmatter.get("status", ""),
        path=spec_path,
    )


def list_specs(base_path: Path, status: str | None = None) -> list[Spec]:
    """List all specs, optionally filtered by status."""
    specs: list[Spec] = []

    for subdir in ["active", "archive"]:
        dir_path = base_path / subdir
        if not dir_path.exists():
            continue

        for entry in dir_path.iterdir():
            if not entry.is_dir():
                continue
            spec_md = entry / "spec.md"
            if not spec_md.exists():
                continue

            try:
                spec = get_spec(entry)
                if status is None or spec.status == status:
                    specs.append(spec)
            except SpecNotFoundError:
                continue

    return specs


def find_by_code(base_path: Path, code: str) -> Spec | None:
    """Find spec by code, returns None if not found."""
    specs = list_specs(base_path)
    for spec in specs:
        if spec.code == code:
            return spec
    return None


def get_progress(spec_path: Path) -> dict:
    """Get completion stats for a spec."""
    if not spec_path.exists():
        raise SpecNotFoundError(spec_path)

    spec_md = spec_path / "spec.md"
    if not spec_md.exists():
        raise SpecNotFoundError(spec_path)

    try:
        tasks_file = load_tasks(spec_path)
        tasks = tasks_file.tasks
    except FileNotFoundError:
        tasks = []

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == Status.COMPLETED)
    in_progress = sum(1 for t in tasks if t.status == Status.IN_PROGRESS)
    pending = sum(1 for t in tasks if t.status == Status.PENDING)

    if total == 0:
        percent_complete = 0.0
    else:
        percent_complete = (completed / total) * 100

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
        "percent_complete": percent_complete,
    }
