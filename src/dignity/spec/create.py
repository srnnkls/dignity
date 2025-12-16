"""Spec creation functionality.

Operations:
- create: Main function for creating new specs
- SpecCreateError: Exception raised on creation failures
- SpecConfig: Dataclass returned on successful creation
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dignity.spec.index import add_entry, load_index
from dignity.spec.templates import render_template
from dignity.spec.validation import generate_code, make_code_unique, validate_spec_name


class SpecCreateError(Exception):
    """Exception raised when spec creation fails."""

    pass


VALID_ISSUE_TYPES = frozenset({"feature", "bug", "chore"})


@dataclass
class SpecConfig:
    """Configuration for a created spec."""

    name: str
    code: str
    issue_type: str
    created: date


def _to_title_case(name: str) -> str:
    """Convert kebab-case name to Title Case.

    Args:
        name: Kebab-case name (e.g., "focus-state-dispatch")

    Returns:
        Title case string (e.g., "Focus State Dispatch")
    """
    return " ".join(word.capitalize() for word in name.split("-"))


def create(
    name: str,
    *,
    issue_type: str = "feature",
    register: bool = True,
    base_dir: Path | None = None,
) -> SpecConfig:
    """Create a new spec.

    Creates the spec directory structure and files using Jinja2 templates:
    - specs/active/{name}/spec.md - Spec document with YAML frontmatter
    - specs/active/{name}/context.md - Context and decisions
    - specs/active/{name}/tasks.yaml - Task tracking file
    - specs/active/{name}/dependencies.md - Task dependency graph
    - specs/active/{name}/validation-checklist.md - Validation tracking

    Content scales by issue_type: feature has full sections, bug/chore minimal.

    Optionally registers the spec in specs/index.yaml.

    Args:
        name: Spec name in kebab-case
        issue_type: Type of issue ("feature", "bug", or "chore")
        register: Whether to register in specs/index.yaml
        base_dir: Base directory (defaults to current directory)

    Returns:
        SpecConfig with spec details

    Raises:
        SpecCreateError: If name is invalid or spec already exists
    """
    if base_dir is None:
        base_dir = Path.cwd()

    try:
        validate_spec_name(name)
    except ValueError as e:
        raise SpecCreateError(f"Invalid spec name: {e}") from e

    if issue_type not in VALID_ISSUE_TYPES:
        raise SpecCreateError(
            f"Invalid issue type '{issue_type}': must be one of {', '.join(sorted(VALID_ISSUE_TYPES))}"
        )

    specs_dir = base_dir / "specs"
    active_dir = specs_dir / "active"
    spec_dir = active_dir / name

    if spec_dir.exists():
        raise SpecCreateError(f"Spec '{name}' already exists at {spec_dir}")

    index_path = specs_dir / "index.yaml"
    existing_codes = set(load_index(index_path).keys())

    base_code = generate_code(name)
    code = make_code_unique(base_code, existing_codes)
    created_date = date.today()

    spec_dir.mkdir(parents=True, exist_ok=True)

    title = _to_title_case(name)
    created_str = created_date.isoformat()
    template_vars = {
        "name": name,
        "code": code,
        "issue_type": issue_type,
        "created": created_str,
        "title": title,
    }

    files_to_create = [
        ("spec.md", "spec.md.jinja2"),
        ("context.md", "context.md.jinja2"),
        ("tasks.yaml", "tasks.yaml.jinja2"),
        ("dependencies.md", "dependencies.md.jinja2"),
        ("validation-checklist.md", "validation-checklist.md.jinja2"),
    ]

    for filename, template_name in files_to_create:
        content = render_template(template_name, **template_vars)
        (spec_dir / filename).write_text(content)

    if register:
        add_entry(index_path, code, name)

    return SpecConfig(
        name=name,
        code=code,
        issue_type=issue_type,
        created=created_date,
    )
