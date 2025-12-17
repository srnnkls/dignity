"""Tests for markdown section manipulation.

Tests cover:
- get_section: Get content under a markdown heading
- set_section: Replace section content
- append_to_section: Append to existing section
- add_section: Add new section to file
- remove_section: Remove section entirely
- SectionNotFoundError: Exception for missing sections
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dignity.spec.sections import (
    SectionNotFoundError,
    add_section,
    append_to_section,
    get_section,
    remove_section,
    set_section,
)


# SectionNotFoundError tests


def test_section_not_found_error_is_exception() -> None:
    """SectionNotFoundError is an Exception subclass."""
    assert issubclass(SectionNotFoundError, Exception)


def test_section_not_found_error_can_be_raised_with_message() -> None:
    """SectionNotFoundError can be raised with a message."""
    with pytest.raises(SectionNotFoundError, match="Section 'Overview' not found"):
        raise SectionNotFoundError("Section 'Overview' not found")


# get_section tests


def test_get_section_returns_section_content(tmp_path: Path) -> None:
    """Returns content between heading and next heading of same level."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "# Title\n\n## Overview\n\nThis is overview content.\n\n## Context\n\nContext here.\n"
    )
    result = get_section(md_file, "Overview")
    assert result == "This is overview content."


def test_get_section_returns_none_for_missing_heading(tmp_path: Path) -> None:
    """Returns None when heading doesn't exist."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("# Title\n\n## Overview\n\nContent here.\n")
    result = get_section(md_file, "NonExistent")
    assert result is None


def test_get_section_handles_empty_file(tmp_path: Path) -> None:
    """Returns None for empty file."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("")
    result = get_section(md_file, "Overview")
    assert result is None


def test_get_section_preserves_frontmatter(tmp_path: Path) -> None:
    """Ignores YAML frontmatter when searching for section."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "---\ncode: FSD\nstatus: Active\n---\n\n# Title\n\n## Overview\n\nContent.\n"
    )
    result = get_section(md_file, "Overview")
    assert result == "Content."


def test_get_section_handles_file_with_only_frontmatter(tmp_path: Path) -> None:
    """Returns None for file with only frontmatter."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("---\ncode: FSD\n---\n")
    result = get_section(md_file, "Overview")
    assert result is None


def test_get_section_at_end_of_file(tmp_path: Path) -> None:
    """Returns content for section at end of file (no next heading)."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("# Title\n\n## Overview\n\nFirst section.\n\n## Final\n\nLast content.\n")
    result = get_section(md_file, "Final")
    assert result == "Last content."


def test_get_section_nested_heading_under_parent(tmp_path: Path) -> None:
    """Section content includes nested subheadings."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "## Overview\n\nIntro.\n\n### Details\n\nNested content.\n\n## Context\n\nNext section.\n"
    )
    result = get_section(md_file, "Overview")
    assert "Intro." in result
    assert "### Details" in result
    assert "Nested content." in result
    assert "## Context" not in result


def test_get_section_multiline_content(tmp_path: Path) -> None:
    """Returns all lines of multiline section content."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "## Overview\n\nLine one.\n\nLine two.\n\nLine three.\n\n## Next\n"
    )
    result = get_section(md_file, "Overview")
    assert "Line one." in result
    assert "Line two." in result
    assert "Line three." in result


def test_get_section_code_block_with_hash_chars(tmp_path: Path) -> None:
    """Code blocks with # characters don't break section detection."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "## Code Example\n\n```python\n# This is a comment\ndef foo(): pass\n```\n\n## Next\n\nAfter.\n"
    )
    result = get_section(md_file, "Code Example")
    assert "# This is a comment" in result
    assert "def foo():" in result
    assert "After." not in result


def test_get_section_same_heading_name_different_levels(tmp_path: Path) -> None:
    """Finds first occurrence when same name exists at different levels."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "## Overview\n\nTop level overview.\n\n### Overview\n\nNested overview.\n\n## End\n"
    )
    result = get_section(md_file, "Overview")
    assert "Top level overview." in result


def test_get_section_heading_with_hash_prefix_levels(tmp_path: Path) -> None:
    """Matches heading regardless of hash prefix count."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("### Deeply Nested\n\nDeep content.\n")
    result = get_section(md_file, "Deeply Nested")
    assert result == "Deep content."


def test_get_section_empty_section(tmp_path: Path) -> None:
    """Returns empty string for section with no content."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Empty\n\n## Next\n\nContent.\n")
    result = get_section(md_file, "Empty")
    assert result == ""


# set_section tests


def test_set_section_replaces_section_content(tmp_path: Path) -> None:
    """Replaces content between heading and next heading."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nOld content.\n\n## Context\n\nKeep this.\n")
    set_section(md_file, "Overview", "New content.")
    content = md_file.read_text()
    assert "New content." in content
    assert "Old content." not in content
    assert "Keep this." in content


def test_set_section_raises_for_missing_heading(tmp_path: Path) -> None:
    """Raises SectionNotFoundError when heading doesn't exist."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nContent.\n")
    with pytest.raises(SectionNotFoundError, match="NonExistent"):
        set_section(md_file, "NonExistent", "New content.")


def test_set_section_preserves_heading(tmp_path: Path) -> None:
    """Preserves the heading line itself."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nOld.\n\n## Next\n")
    set_section(md_file, "Overview", "New.")
    content = md_file.read_text()
    assert "## Overview" in content


def test_set_section_preserves_frontmatter(tmp_path: Path) -> None:
    """Preserves YAML frontmatter."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("---\ncode: FSD\n---\n\n## Overview\n\nOld.\n")
    set_section(md_file, "Overview", "New.")
    content = md_file.read_text()
    assert content.startswith("---\ncode: FSD\n---")


def test_set_section_replaces_last_section(tmp_path: Path) -> None:
    """Replaces content in last section (no following heading)."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## First\n\nFirst content.\n\n## Last\n\nOld last.\n")
    set_section(md_file, "Last", "New last.")
    content = md_file.read_text()
    assert "New last." in content
    assert "Old last." not in content
    assert "First content." in content


def test_set_section_handles_nested_headings(tmp_path: Path) -> None:
    """Replaces parent section including nested headings."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "## Overview\n\nIntro.\n\n### Details\n\nNested.\n\n## Context\n"
    )
    set_section(md_file, "Overview", "Simple replacement.")
    content = md_file.read_text()
    assert "Simple replacement." in content
    assert "### Details" not in content
    assert "## Context" in content


def test_set_section_multiline_replacement(tmp_path: Path) -> None:
    """Allows multiline replacement content."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nOld.\n\n## Next\n")
    set_section(md_file, "Overview", "Line one.\n\nLine two.")
    content = md_file.read_text()
    assert "Line one." in content
    assert "Line two." in content


# append_to_section tests


def test_append_to_section_appends_to_existing_content(tmp_path: Path) -> None:
    """Appends content to existing section content."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nExisting.\n\n## Next\n")
    append_to_section(md_file, "Overview", "Appended.")
    content = md_file.read_text()
    assert "Existing." in content
    assert "Appended." in content
    result = get_section(md_file, "Overview")
    assert "Existing." in result
    assert "Appended." in result


def test_append_to_section_raises_for_missing_heading(tmp_path: Path) -> None:
    """Raises SectionNotFoundError when heading doesn't exist."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nContent.\n")
    with pytest.raises(SectionNotFoundError, match="NonExistent"):
        append_to_section(md_file, "NonExistent", "New content.")


def test_append_to_section_appends_to_empty_section(tmp_path: Path) -> None:
    """Appends to section that has no existing content."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Empty\n\n## Next\n")
    append_to_section(md_file, "Empty", "Now has content.")
    result = get_section(md_file, "Empty")
    assert "Now has content." in result


def test_append_to_section_appends_to_last_section(tmp_path: Path) -> None:
    """Appends to last section in file."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Only\n\nExisting.\n")
    append_to_section(md_file, "Only", "More.")
    content = md_file.read_text()
    assert "Existing." in content
    assert "More." in content


def test_append_to_section_preserves_other_sections(tmp_path: Path) -> None:
    """Does not modify other sections."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## First\n\nOne.\n\n## Second\n\nTwo.\n\n## Third\n\nThree.\n")
    append_to_section(md_file, "Second", "Extra.")
    assert get_section(md_file, "First") == "One."
    assert get_section(md_file, "Third") == "Three."


# add_section tests


def test_add_section_adds_section_at_end(tmp_path: Path) -> None:
    """Adds new section at end of file by default."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Existing\n\nContent.\n")
    add_section(md_file, "New Section", "New content.")
    content = md_file.read_text()
    assert "## New Section" in content
    assert "New content." in content
    assert content.index("## Existing") < content.index("## New Section")


def test_add_section_adds_section_after_specified_heading(tmp_path: Path) -> None:
    """Adds new section after specified heading."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## First\n\nOne.\n\n## Third\n\nThree.\n")
    add_section(md_file, "Second", "Two.", after="First")
    content = md_file.read_text()
    first_pos = content.index("## First")
    second_pos = content.index("## Second")
    third_pos = content.index("## Third")
    assert first_pos < second_pos < third_pos


def test_add_section_raises_for_invalid_after_heading(tmp_path: Path) -> None:
    """Raises SectionNotFoundError if after heading doesn't exist."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nContent.\n")
    with pytest.raises(SectionNotFoundError, match="NonExistent"):
        add_section(md_file, "New", "Content.", after="NonExistent")


def test_add_section_adds_to_empty_file(tmp_path: Path) -> None:
    """Adds section to empty file."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("")
    add_section(md_file, "First", "Content.")
    content = md_file.read_text()
    assert "## First" in content
    assert "Content." in content


def test_add_section_adds_after_frontmatter(tmp_path: Path) -> None:
    """Adds section after frontmatter in file with only frontmatter."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("---\ncode: FSD\n---\n")
    add_section(md_file, "Overview", "Content.")
    content = md_file.read_text()
    assert content.startswith("---\ncode: FSD\n---")
    assert "## Overview" in content
    assert content.index("---") < content.index("## Overview")


def test_add_section_preserves_frontmatter(tmp_path: Path) -> None:
    """Preserves existing frontmatter when adding section."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("---\ncode: FSD\nstatus: Active\n---\n\n## Existing\n\nContent.\n")
    add_section(md_file, "New", "New content.")
    content = md_file.read_text()
    assert "code: FSD" in content
    assert "status: Active" in content


def test_add_section_uses_same_heading_level_as_siblings(tmp_path: Path) -> None:
    """New section uses same heading level as existing sections."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("### Existing\n\nContent.\n")
    add_section(md_file, "New", "Content.")
    content = md_file.read_text()
    assert "### New" in content or "## New" in content


# remove_section tests


def test_remove_section_removes_section_content_and_heading(tmp_path: Path) -> None:
    """Removes heading and all content until next section."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## First\n\nKeep.\n\n## Remove\n\nGone.\n\n## Third\n\nKeep also.\n")
    result = remove_section(md_file, "Remove")
    assert result is True
    content = md_file.read_text()
    assert "## Remove" not in content
    assert "Gone." not in content
    assert "Keep." in content
    assert "Keep also." in content


def test_remove_section_returns_false_for_missing_heading(tmp_path: Path) -> None:
    """Returns False when heading doesn't exist."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Overview\n\nContent.\n")
    result = remove_section(md_file, "NonExistent")
    assert result is False


def test_remove_section_removes_last_section(tmp_path: Path) -> None:
    """Removes last section in file."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## First\n\nKeep.\n\n## Last\n\nRemove this.\n")
    result = remove_section(md_file, "Last")
    assert result is True
    content = md_file.read_text()
    assert "## Last" not in content
    assert "Remove this." not in content
    assert "Keep." in content


def test_remove_section_removes_only_section(tmp_path: Path) -> None:
    """Removes the only section in file."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Only\n\nRemove all.\n")
    result = remove_section(md_file, "Only")
    assert result is True
    content = md_file.read_text()
    assert "## Only" not in content
    assert "Remove all." not in content


def test_remove_section_preserves_frontmatter(tmp_path: Path) -> None:
    """Preserves frontmatter when removing section."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("---\ncode: FSD\n---\n\n## Remove\n\nGone.\n")
    remove_section(md_file, "Remove")
    content = md_file.read_text()
    assert "---\ncode: FSD\n---" in content


def test_remove_section_removes_section_with_nested_headings(tmp_path: Path) -> None:
    """Removes section including its nested subheadings."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "## Remove\n\nParent.\n\n### Nested\n\nChild.\n\n## Keep\n\nStays.\n"
    )
    result = remove_section(md_file, "Remove")
    assert result is True
    content = md_file.read_text()
    assert "## Remove" not in content
    assert "### Nested" not in content
    assert "Parent." not in content
    assert "Child." not in content
    assert "Stays." in content


def test_remove_section_does_not_modify_file_if_heading_missing(tmp_path: Path) -> None:
    """File unchanged when heading doesn't exist."""
    md_file = tmp_path / "spec.md"
    original = "## Overview\n\nContent.\n"
    md_file.write_text(original)
    remove_section(md_file, "NonExistent")
    assert md_file.read_text() == original


# Integration tests


def test_get_set_roundtrip(tmp_path: Path) -> None:
    """Get then set preserves file structure."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        "---\ncode: FSD\n---\n\n# Title\n\n## Overview\n\nOriginal.\n\n## Context\n\nContext.\n"
    )
    original_context = get_section(md_file, "Context")
    set_section(md_file, "Overview", "Updated.")
    assert get_section(md_file, "Context") == original_context


def test_add_then_remove(tmp_path: Path) -> None:
    """Add then remove returns file to original state (minus whitespace)."""
    md_file = tmp_path / "spec.md"
    md_file.write_text("## Existing\n\nContent.\n")
    add_section(md_file, "Temp", "Temporary.")
    assert get_section(md_file, "Temp") is not None
    remove_section(md_file, "Temp")
    assert get_section(md_file, "Temp") is None
    assert get_section(md_file, "Existing") == "Content."


def test_complex_document_manipulation(tmp_path: Path) -> None:
    """Multiple operations on complex document."""
    md_file = tmp_path / "spec.md"
    md_file.write_text(
        """---
code: SMA
status: Active
---

# Spec: My Feature

## Overview

This is the overview content.
Multiple lines here.

## Context

Context information.

### Subsection

Nested content.

## Success Criteria

1. First criterion
2. Second criterion
"""
    )
    assert get_section(md_file, "Overview") is not None
    assert "Multiple lines" in get_section(md_file, "Overview")

    set_section(md_file, "Context", "Updated context.\n\n### New Subsection\n\nNew nested.")
    context = get_section(md_file, "Context")
    assert "Updated context." in context
    assert "New Subsection" in context

    append_to_section(md_file, "Success Criteria", "3. Third criterion")
    criteria = get_section(md_file, "Success Criteria")
    assert "First criterion" in criteria
    assert "Third criterion" in criteria

    add_section(md_file, "Notes", "Some notes.", after="Overview")
    content = md_file.read_text()
    overview_pos = content.index("## Overview")
    notes_pos = content.index("## Notes")
    context_pos = content.index("## Context")
    assert overview_pos < notes_pos < context_pos

    content = md_file.read_text()
    assert "code: SMA" in content
    assert "status: Active" in content
