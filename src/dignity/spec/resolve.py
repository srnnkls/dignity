"""Spec name resolution."""

from __future__ import annotations

from pathlib import Path

from dignity.settings import Settings, get_settings
from dignity.spec.query import SpecNotFoundError


def resolve_spec(name: str, *, settings: Settings | None = None) -> Path:
    """Resolve spec name to its directory path.

    Searches active directory first, then archive.
    Raises SpecNotFoundError if not found in either location.
    """
    if settings is None:
        settings = get_settings()

    active_path = settings.active_dir / name
    if active_path.exists():
        return active_path

    archive_path = settings.archive_dir / name
    if archive_path.exists():
        return archive_path

    raise SpecNotFoundError(active_path)
