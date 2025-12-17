"""Markdown section manipulation utilities.

Provides functions for reading, writing, and manipulating sections
in markdown documents identified by headings.
"""

from __future__ import annotations

import re
from pathlib import Path


class SectionNotFoundError(Exception):
    """Raised when a section heading is not found in a markdown file."""


def _parse_frontmatter(content: str) -> tuple[str | None, str]:
    """Parse YAML frontmatter from markdown content.

    Returns tuple of (frontmatter_block, remaining_content).
    frontmatter_block includes the --- delimiters.
    """
    if not content.startswith("---"):
        return None, content

    lines = content.split("\n")
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            frontmatter = "\n".join(lines[:i + 1])
            remaining = "\n".join(lines[i + 1:])
            return frontmatter, remaining.lstrip("\n")

    return None, content


def _find_section_bounds(
    lines: list[str], heading: str
) -> tuple[int, int, int, int] | None:
    """Find section start line, content start line, end line, and heading level.

    Returns (heading_line, content_start, section_end, level) or None if not found.
    section_end is the line after the last content line (exclusive).
    """
    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$")
    in_code_block = False
    found_heading_line: int | None = None
    found_level: int = 0

    for i, line in enumerate(lines):
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        match = heading_pattern.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()

            if found_heading_line is None and title == heading:
                found_heading_line = i
                found_level = level
            elif found_heading_line is not None and level <= found_level:
                return (found_heading_line, found_heading_line + 1, i, found_level)

    if found_heading_line is not None:
        return (found_heading_line, found_heading_line + 1, len(lines), found_level)

    return None


def _extract_section_content(lines: list[str], start: int, end: int) -> str:
    """Extract and clean section content from lines."""
    content_lines = lines[start:end]

    while content_lines and content_lines[0].strip() == "":
        content_lines.pop(0)
    while content_lines and content_lines[-1].strip() == "":
        content_lines.pop()

    return "\n".join(content_lines)


def get_section(file_path: Path, heading: str) -> str | None:
    """Get content under a markdown heading.

    Args:
        file_path: Path to the markdown file
        heading: The heading text to find (without # prefix)

    Returns:
        Section content as a string, or None if heading not found
    """
    content = file_path.read_text()
    if not content:
        return None

    _, body = _parse_frontmatter(content)
    if not body.strip():
        return None

    lines = body.split("\n")
    bounds = _find_section_bounds(lines, heading)

    if bounds is None:
        return None

    _, content_start, section_end, _ = bounds
    return _extract_section_content(lines, content_start, section_end)


def set_section(file_path: Path, heading: str, content: str) -> None:
    """Replace content under a markdown heading.

    Args:
        file_path: Path to the markdown file
        heading: The heading text to find (without # prefix)
        content: New content to set under the heading

    Raises:
        SectionNotFoundError: If heading doesn't exist
    """
    file_content = file_path.read_text()
    frontmatter, body = _parse_frontmatter(file_content)
    lines = body.split("\n")

    bounds = _find_section_bounds(lines, heading)
    if bounds is None:
        raise SectionNotFoundError(f"Section '{heading}' not found")

    heading_line, content_start, section_end, _ = bounds

    new_lines = (
        lines[:heading_line + 1]
        + ["", content, ""]
        + lines[section_end:]
    )

    new_body = "\n".join(new_lines)

    if frontmatter:
        new_content = frontmatter + "\n\n" + new_body
    else:
        new_content = new_body

    file_path.write_text(new_content)


def append_to_section(file_path: Path, heading: str, content: str) -> None:
    """Append content to an existing section.

    Args:
        file_path: Path to the markdown file
        heading: The heading text to find (without # prefix)
        content: Content to append to the section

    Raises:
        SectionNotFoundError: If heading doesn't exist
    """
    existing = get_section(file_path, heading)
    if existing is None:
        raise SectionNotFoundError(f"Section '{heading}' not found")

    if existing:
        new_content = existing + "\n\n" + content
    else:
        new_content = content

    set_section(file_path, heading, new_content)


def add_section(
    file_path: Path, heading: str, content: str, after: str | None = None
) -> None:
    """Add a new section to the markdown file.

    Args:
        file_path: Path to the markdown file
        heading: The heading text for the new section
        content: Content for the new section
        after: Optional heading after which to insert the new section.
               If None, adds at end of file.

    Raises:
        SectionNotFoundError: If after heading doesn't exist
    """
    file_content = file_path.read_text()
    frontmatter, body = _parse_frontmatter(file_content)

    heading_pattern = re.compile(r"^(#{1,6})\s+.+$")
    default_level = 2

    if not body.strip():
        new_section = f"{'#' * default_level} {heading}\n\n{content}\n"
        if frontmatter:
            new_content = frontmatter + "\n\n" + new_section
        else:
            new_content = new_section
        file_path.write_text(new_content)
        return

    lines = body.split("\n")

    if after is None:
        for line in lines:
            match = heading_pattern.match(line)
            if match:
                default_level = len(match.group(1))
                break
        new_section = f"{'#' * default_level} {heading}\n\n{content}\n"
        new_body = body.rstrip("\n") + "\n\n" + new_section
    else:
        bounds = _find_section_bounds(lines, after)
        if bounds is None:
            raise SectionNotFoundError(f"Section '{after}' not found")

        _, _, section_end, after_level = bounds
        new_section = f"{'#' * after_level} {heading}\n\n{content}\n"

        new_lines = lines[:section_end] + ["", new_section.rstrip("\n"), ""] + lines[section_end:]
        new_body = "\n".join(new_lines)

    if frontmatter:
        new_content = frontmatter + "\n\n" + new_body
    else:
        new_content = new_body

    file_path.write_text(new_content)


def remove_section(file_path: Path, heading: str) -> bool:
    """Remove a section and its content from the markdown file.

    Args:
        file_path: Path to the markdown file
        heading: The heading text to remove (without # prefix)

    Returns:
        True if section was removed, False if heading not found
    """
    file_content = file_path.read_text()
    frontmatter, body = _parse_frontmatter(file_content)
    lines = body.split("\n")

    bounds = _find_section_bounds(lines, heading)
    if bounds is None:
        return False

    heading_line, _, section_end, _ = bounds

    new_lines = lines[:heading_line] + lines[section_end:]

    while new_lines and new_lines[-1].strip() == "":
        new_lines.pop()
    while new_lines and new_lines[0].strip() == "":
        new_lines.pop(0)

    new_body = "\n".join(new_lines)

    if frontmatter:
        if new_body:
            new_content = frontmatter + "\n\n" + new_body + "\n"
        else:
            new_content = frontmatter + "\n"
    else:
        new_content = new_body + "\n" if new_body else ""

    file_path.write_text(new_content)
    return True
