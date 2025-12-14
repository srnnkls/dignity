"""Spec name validation and code generation.

Operations:
- validate_spec_name: Validate kebab-case format
- generate_code: Extract initials from kebab-case name
- make_code_unique: Handle collisions with numeric suffixes
"""

from __future__ import annotations

import re
from collections.abc import Set

KEBAB_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def validate_spec_name(name: str) -> None:
    """Validate spec name is kebab-case.

    Pattern: ^[a-z][a-z0-9]*(-[a-z0-9]+)*$
    - Must start with lowercase letter
    - May contain lowercase letters, digits, and hyphens
    - Hyphen must be followed by at least one alphanumeric char
    - No leading/trailing hyphens, no double hyphens

    Args:
        name: Spec name to validate

    Raises:
        ValueError: If name is not valid kebab-case
    """
    if not KEBAB_CASE_PATTERN.match(name):
        raise ValueError(f"Invalid spec name '{name}': spec name must be kebab-case")


def generate_code(name: str) -> str:
    """Generate code from spec name by extracting initials.

    Takes first character of each hyphen-separated segment
    and returns uppercase.

    Args:
        name: Valid kebab-case spec name

    Returns:
        Uppercase code from initials (e.g., "focus-state-dispatch" -> "FSD")
    """
    segments = name.split("-")
    initials = "".join(segment[0] for segment in segments)
    return initials.upper()


def make_code_unique(code: str, existing: Set[str]) -> str:
    """Make code unique by appending numeric suffix if collision.

    Starts with 2 for first collision, increments until unique.

    Args:
        code: Base code to make unique
        existing: Set of existing codes to check against

    Returns:
        Unique code (original if no collision, or with numeric suffix)
    """
    if code not in existing:
        return code

    suffix = 2
    while f"{code}{suffix}" in existing:
        suffix += 1

    return f"{code}{suffix}"
