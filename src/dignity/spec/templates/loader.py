"""Spec template loading and rendering utilities.

Provides Jinja2 template loading from package data using importlib.resources.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from importlib import resources
from typing import Any

from jinja2 import BaseLoader, Environment, TemplateNotFound


class PackageLoader(BaseLoader):
    """Jinja2 loader that loads templates from package data using importlib.resources."""

    def __init__(self, package: str = "dignity.spec.templates") -> None:
        self.package = package

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str | None, Callable[[], bool] | None]:
        try:
            package_files = resources.files(self.package)
            template_file = package_files.joinpath(template)
            source = template_file.read_text(encoding="utf-8")
            filename = str(template_file)
            return source, filename, lambda: True
        except (FileNotFoundError, TypeError):
            raise TemplateNotFound(template)


def render_template(template_name: str, /, **variables: Any) -> str:
    """Load and render a template with the given variables.

    Args:
        template_name: Template filename (e.g., "spec.md.j2")
        **variables: Template variables to substitute

    Returns:
        Rendered template as a string

    Raises:
        TemplateNotFound: If the template does not exist
    """
    env = Environment(loader=PackageLoader())
    template = env.get_template(template_name)
    return template.render(**variables)


def validate_vars(required: Iterable[str], provided: Iterable[str]) -> None:
    """Validate that all required variables are provided.

    Args:
        required: Set of required variable names
        provided: Set of provided variable names

    Returns:
        None if all required variables are present

    Raises:
        ValueError: If any required variables are missing, with message listing them
    """
    required_set = set(required)
    provided_set = set(provided)
    missing = required_set - provided_set

    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required variables: {missing_list}")

    return None
