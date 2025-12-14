"""Spec index management.

Manages the specs/index.yaml file that maps short codes to spec names.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_index(path: Path) -> dict[str, str]:
    """Load codes from specs/index.yaml.

    Args:
        path: Path to the index.yaml file.

    Returns:
        Dictionary mapping codes to spec names.
        Empty dict if file missing or no "codes" key.
    """
    if not path.exists():
        return {}

    content = path.read_text()
    if not content.strip():
        return {}

    data = yaml.safe_load(content)
    if data is None or "codes" not in data:
        return {}

    return data["codes"]


def save_index(path: Path, codes: dict[str, str]) -> None:
    """Write codes dict to specs/index.yaml.

    Args:
        path: Path to the index.yaml file.
        codes: Dictionary mapping codes to spec names.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"codes": codes}
    path.write_text(yaml.dump(data, default_flow_style=False))


def add_entry(path: Path, code: str, name: str) -> None:
    """Add new code -> name mapping to index.

    Args:
        path: Path to the index.yaml file.
        code: Short code (e.g., "FSD").
        name: Spec name (e.g., "focus-state-dispatch").
    """
    codes = load_index(path)
    codes[code] = name
    save_index(path, codes)
