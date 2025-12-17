"""Tests for spec creation functionality.

Tests cover:
- create: Main function for creating new specs
- SpecCreateError: Exception raised on creation failures
- SpecConfig: Dataclass returned on successful creation
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from dignity.spec.create import SpecConfig, SpecCreateError, create


# SpecCreateError tests


def test_spec_create_error_exists() -> None:
    """SpecCreateError exception class exists and is an Exception."""
    assert issubclass(SpecCreateError, Exception)


def test_spec_create_error_with_message() -> None:
    """SpecCreateError can be raised with a message."""
    with pytest.raises(SpecCreateError, match="test message"):
        raise SpecCreateError("test message")


# SpecConfig tests


def test_spec_config_has_name_field() -> None:
    """SpecConfig has name field."""
    config = SpecConfig(
        name="test-spec",
        code="TS",
        issue_type="feature",
        created=date(2025, 12, 14),
    )
    assert config.name == "test-spec"


def test_spec_config_has_code_field() -> None:
    """SpecConfig has code field."""
    config = SpecConfig(
        name="test-spec",
        code="TS",
        issue_type="feature",
        created=date(2025, 12, 14),
    )
    assert config.code == "TS"


def test_spec_config_has_issue_type_field() -> None:
    """SpecConfig has issue_type field."""
    config = SpecConfig(
        name="test-spec",
        code="TS",
        issue_type="bug",
        created=date(2025, 12, 14),
    )
    assert config.issue_type == "bug"


def test_spec_config_has_created_field() -> None:
    """SpecConfig has created field."""
    config = SpecConfig(
        name="test-spec",
        code="TS",
        issue_type="feature",
        created=date(2025, 12, 14),
    )
    assert config.created == date(2025, 12, 14)


# create validation tests


def test_create_invalid_name_raises_spec_create_error(tmp_path: Path) -> None:
    """Non-kebab-case name raises SpecCreateError."""
    with pytest.raises(SpecCreateError, match="Invalid spec name"):
        create("InvalidName", base_dir=tmp_path)


def test_create_underscore_name_raises_spec_create_error(tmp_path: Path) -> None:
    """Underscore in name raises SpecCreateError."""
    with pytest.raises(SpecCreateError, match="Invalid spec name"):
        create("invalid_name", base_dir=tmp_path)


def test_create_space_in_name_raises_spec_create_error(tmp_path: Path) -> None:
    """Space in name raises SpecCreateError."""
    with pytest.raises(SpecCreateError, match="Invalid spec name"):
        create("invalid name", base_dir=tmp_path)


def test_create_empty_name_raises_spec_create_error(tmp_path: Path) -> None:
    """Empty name raises SpecCreateError."""
    with pytest.raises(SpecCreateError, match="Invalid spec name"):
        create("", base_dir=tmp_path)


def test_create_invalid_issue_type_raises_spec_create_error(tmp_path: Path) -> None:
    """Invalid issue_type raises SpecCreateError."""
    with pytest.raises(SpecCreateError, match="Invalid issue type"):
        create("valid-name", issue_type="invalid", base_dir=tmp_path)


def test_create_valid_issue_types_accepted(tmp_path: Path) -> None:
    """Valid issue types (feature, bug, chore) are accepted."""
    for issue_type in ("feature", "bug", "chore"):
        spec_name = f"test-{issue_type}"
        result = create(spec_name, issue_type=issue_type, base_dir=tmp_path, register=False)
        assert result.issue_type == issue_type


# create existing spec tests


def test_create_existing_spec_raises_spec_create_error(tmp_path: Path) -> None:
    """Creating spec that already exists raises SpecCreateError."""
    spec_dir = tmp_path / "specs" / "active" / "existing-spec"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text("# Existing")

    with pytest.raises(SpecCreateError, match="already exists"):
        create("existing-spec", base_dir=tmp_path)


# create code generation tests


def test_create_generates_code_from_name(tmp_path: Path) -> None:
    """Code is generated from spec name initials."""
    result = create("focus-state-dispatch", base_dir=tmp_path, register=False)
    assert result.code == "FSD"


def test_create_single_word_code(tmp_path: Path) -> None:
    """Single word name generates single letter code."""
    result = create("dispatch", base_dir=tmp_path, register=False)
    assert result.code == "D"


def test_create_two_word_code(tmp_path: Path) -> None:
    """Two word name generates two letter code."""
    result = create("hook-migration", base_dir=tmp_path, register=False)
    assert result.code == "HM"


# create directory bootstrap tests


def test_create_creates_specs_directory(tmp_path: Path) -> None:
    """Creates specs/ directory if it doesn't exist."""
    create("test-spec", base_dir=tmp_path, register=False)
    assert (tmp_path / "specs").is_dir()


def test_create_creates_active_directory(tmp_path: Path) -> None:
    """Creates specs/active/ directory if it doesn't exist."""
    create("test-spec", base_dir=tmp_path, register=False)
    assert (tmp_path / "specs" / "active").is_dir()


def test_create_creates_spec_directory(tmp_path: Path) -> None:
    """Creates spec directory inside specs/active/."""
    create("my-new-spec", base_dir=tmp_path, register=False)
    assert (tmp_path / "specs" / "active" / "my-new-spec").is_dir()


def test_create_existing_specs_directory_preserved(tmp_path: Path) -> None:
    """Existing specs/ directory is preserved."""
    specs_dir = tmp_path / "specs" / "active" / "other-spec"
    specs_dir.mkdir(parents=True)
    (specs_dir / "spec.md").write_text("# Other")

    create("new-spec", base_dir=tmp_path, register=False)

    assert (specs_dir / "spec.md").read_text() == "# Other"


# create spec.md tests


def test_create_creates_spec_md_file(tmp_path: Path) -> None:
    """Creates spec.md file in spec directory."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    assert spec_file.is_file()


def test_create_spec_md_has_frontmatter(tmp_path: Path) -> None:
    """spec.md contains YAML frontmatter."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    assert content.startswith("---\n")
    assert "\n---\n" in content


def test_create_spec_md_frontmatter_has_code(tmp_path: Path) -> None:
    """spec.md frontmatter contains code field."""
    create("focus-state-dispatch", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "focus-state-dispatch" / "spec.md"
    content = spec_file.read_text()
    assert "code: FSD" in content


def test_create_spec_md_frontmatter_has_issue_type(tmp_path: Path) -> None:
    """spec.md frontmatter contains issue_type field."""
    create("test-spec", issue_type="bug", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    assert "issue_type: bug" in content


def test_create_spec_md_frontmatter_has_created_date(tmp_path: Path) -> None:
    """spec.md frontmatter contains created date."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    today = date.today().isoformat()
    assert f"created: {today}" in content


def test_create_spec_md_frontmatter_has_status_active(tmp_path: Path) -> None:
    """spec.md frontmatter contains status: Active."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    assert "status: Active" in content


def test_create_spec_md_has_title(tmp_path: Path) -> None:
    """spec.md contains title with spec name."""
    create("focus-state-dispatch", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "focus-state-dispatch" / "spec.md"
    content = spec_file.read_text()
    assert "# Spec: Focus State Dispatch" in content


def test_create_spec_md_has_overview_section(tmp_path: Path) -> None:
    """spec.md contains Overview section."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    assert "## Overview" in content


def test_create_spec_md_has_context_section(tmp_path: Path) -> None:
    """spec.md contains Context section."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    assert "## Context" in content


def test_create_spec_md_has_success_criteria_section(tmp_path: Path) -> None:
    """spec.md contains Success Criteria section."""
    create("test-spec", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "test-spec" / "spec.md"
    content = spec_file.read_text()
    assert "## Success Criteria" in content


# create index registration tests


def test_create_register_true_adds_to_index(tmp_path: Path) -> None:
    """register=True adds spec to specs/index.yaml."""
    create("test-spec", base_dir=tmp_path, register=True)
    index_file = tmp_path / "specs" / "index.yaml"
    assert index_file.is_file()
    content = index_file.read_text()
    assert "test-spec" in content


def test_create_register_false_does_not_create_index(tmp_path: Path) -> None:
    """register=False does not create index.yaml if it doesn't exist."""
    create("test-spec", base_dir=tmp_path, register=False)
    index_file = tmp_path / "specs" / "index.yaml"
    assert not index_file.exists()


def test_create_register_false_does_not_modify_existing_index(
    tmp_path: Path,
) -> None:
    """register=False does not modify existing index.yaml."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True)
    index_file = specs_dir / "index.yaml"
    index_file.write_text("specs:\n  - other-spec\n")

    create("test-spec", base_dir=tmp_path, register=False)

    content = index_file.read_text()
    assert "test-spec" not in content
    assert "other-spec" in content


def test_create_register_appends_to_existing_index(tmp_path: Path) -> None:
    """register=True appends to existing index.yaml."""
    specs_dir = tmp_path / "specs"
    specs_dir.mkdir(parents=True)
    index_file = specs_dir / "index.yaml"
    index_file.write_text("codes:\n  ES: existing-spec\n")

    create("new-spec", base_dir=tmp_path, register=True)

    content = index_file.read_text()
    assert "existing-spec" in content
    assert "new-spec" in content


# create return value tests


def test_create_returns_spec_config(tmp_path: Path) -> None:
    """create() returns a SpecConfig instance."""
    result = create("test-spec", base_dir=tmp_path, register=False)
    assert isinstance(result, SpecConfig)


def test_create_return_has_correct_name(tmp_path: Path) -> None:
    """Returned SpecConfig has correct name."""
    result = create("my-spec-name", base_dir=tmp_path, register=False)
    assert result.name == "my-spec-name"


def test_create_return_has_correct_code(tmp_path: Path) -> None:
    """Returned SpecConfig has correct code."""
    result = create("focus-state-dispatch", base_dir=tmp_path, register=False)
    assert result.code == "FSD"


def test_create_return_has_correct_issue_type(tmp_path: Path) -> None:
    """Returned SpecConfig has correct issue_type."""
    result = create("test-spec", issue_type="chore", base_dir=tmp_path, register=False)
    assert result.issue_type == "chore"


def test_create_return_has_correct_created_date(tmp_path: Path) -> None:
    """Returned SpecConfig has correct created date."""
    result = create("test-spec", base_dir=tmp_path, register=False)
    assert result.created == date.today()


def test_create_default_issue_type_is_feature(tmp_path: Path) -> None:
    """Default issue_type is 'feature'."""
    result = create("test-spec", base_dir=tmp_path, register=False)
    assert result.issue_type == "feature"


# create edge cases tests


def test_create_single_letter_spec_name(tmp_path: Path) -> None:
    """Single letter spec name works."""
    result = create("a", base_dir=tmp_path, register=False)
    assert result.name == "a"
    assert result.code == "A"


def test_create_long_spec_name(tmp_path: Path) -> None:
    """Long multi-word spec name works."""
    result = create(
        "this-is-a-very-long-spec-name", base_dir=tmp_path, register=False
    )
    assert result.name == "this-is-a-very-long-spec-name"
    assert result.code == "TIAVLSN"


def test_create_spec_name_with_numbers(tmp_path: Path) -> None:
    """Spec name with numbers works."""
    result = create("api2-client", base_dir=tmp_path, register=False)
    assert result.name == "api2-client"
    assert result.code == "AC"


# New file creation tests (target state: Jinja2 templates)


def test_creates_context_md_file(tmp_path: Path) -> None:
    """context.md is created in spec directory."""
    create("test-spec", base_dir=tmp_path, register=False)
    context_file = tmp_path / "specs" / "active" / "test-spec" / "context.md"
    assert context_file.is_file()


def test_creates_tasks_yaml_file(tmp_path: Path) -> None:
    """tasks.yaml is created in spec directory."""
    create("test-spec", base_dir=tmp_path, register=False)
    tasks_file = tmp_path / "specs" / "active" / "test-spec" / "tasks.yaml"
    assert tasks_file.is_file()


def test_creates_dependencies_md_file(tmp_path: Path) -> None:
    """dependencies.md is created in spec directory."""
    create("test-spec", base_dir=tmp_path, register=False)
    deps_file = tmp_path / "specs" / "active" / "test-spec" / "dependencies.md"
    assert deps_file.is_file()


def test_creates_validation_checklist_md_file(tmp_path: Path) -> None:
    """validation-checklist.md is created in spec directory."""
    create("test-spec", base_dir=tmp_path, register=False)
    checklist_file = tmp_path / "specs" / "active" / "test-spec" / "validation-checklist.md"
    assert checklist_file.is_file()


# Content scaling tests (issue_type affects template content)


def test_feature_spec_has_architectural_approach_section(tmp_path: Path) -> None:
    """Feature issue_type includes Architectural Approach section."""
    create("feature-spec", issue_type="feature", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "feature-spec" / "spec.md"
    content = spec_file.read_text()
    assert "## Architectural Approach" in content


def test_bug_spec_has_minimal_sections(tmp_path: Path) -> None:
    """Bug issue_type has minimal sections (no Architectural Approach)."""
    create("bug-spec", issue_type="bug", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "bug-spec" / "spec.md"
    content = spec_file.read_text()
    assert "## Architectural Approach" not in content


# Template variable tests


def test_spec_md_title_uses_title_case(tmp_path: Path) -> None:
    """spec.md title converts kebab-case to Title Case."""
    create("multi-word-spec-name", base_dir=tmp_path, register=False)
    spec_file = tmp_path / "specs" / "active" / "multi-word-spec-name" / "spec.md"
    content = spec_file.read_text()
    assert "# Spec: Multi Word Spec Name" in content


def test_context_md_has_title(tmp_path: Path) -> None:
    """context.md contains title with spec name in Title Case."""
    create("my-feature", base_dir=tmp_path, register=False)
    context_file = tmp_path / "specs" / "active" / "my-feature" / "context.md"
    content = context_file.read_text()
    assert "My Feature" in content


def test_tasks_yaml_has_spec_code(tmp_path: Path) -> None:
    """tasks.yaml references the spec code."""
    create("focus-state", base_dir=tmp_path, register=False)
    tasks_file = tmp_path / "specs" / "active" / "focus-state" / "tasks.yaml"
    content = tasks_file.read_text()
    assert "code: FS" in content
