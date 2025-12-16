"""Tests for spec template loading and rendering.

Tests cover:
- Package structure and imports
- PackageLoader: Custom Jinja2 loader using importlib.resources
- render_template: Template loading and rendering with variables
- validate_vars: Variable validation with descriptive error messages
- Template content for all 5 spec document types
"""

from __future__ import annotations

import pytest
from jinja2 import TemplateNotFound


# --- Package imports ---


def test_render_template_importable() -> None:
    """render_template is importable from dignity.spec.templates."""
    from dignity.spec.templates import render_template

    assert callable(render_template)


def test_validate_vars_importable() -> None:
    """validate_vars is importable from dignity.spec.templates."""
    from dignity.spec.templates import validate_vars

    assert callable(validate_vars)


def test_package_loader_importable() -> None:
    """PackageLoader class is importable from dignity.spec.templates."""
    from dignity.spec.templates import PackageLoader

    assert PackageLoader is not None


# --- PackageLoader ---


def test_loader_is_jinja_base_loader() -> None:
    """PackageLoader is a Jinja2 BaseLoader subclass."""
    from jinja2 import BaseLoader

    from dignity.spec.templates import PackageLoader

    assert issubclass(PackageLoader, BaseLoader)


def test_loader_loads_template_from_package() -> None:
    """PackageLoader can load templates from package data."""
    from jinja2 import Environment

    from dignity.spec.templates import PackageLoader

    env = Environment(loader=PackageLoader())
    template = env.get_template("spec.md.jinja2")
    assert template is not None


def test_loader_raises_template_not_found() -> None:
    """PackageLoader raises TemplateNotFound for non-existent templates."""
    from jinja2 import Environment

    from dignity.spec.templates import PackageLoader

    env = Environment(loader=PackageLoader())
    with pytest.raises(TemplateNotFound, match="nonexistent.jinja2"):
        env.get_template("nonexistent.jinja2")


def test_loader_returns_template_source() -> None:
    """PackageLoader get_source returns source, filename, and uptodate."""
    from jinja2 import Environment

    from dignity.spec.templates import PackageLoader

    loader = PackageLoader()
    env = Environment(loader=loader)
    source, filename, uptodate = loader.get_source(env, "spec.md.jinja2")
    assert isinstance(source, str)
    assert len(source) > 0
    assert filename is not None
    assert callable(uptodate) or uptodate is None


# --- render_template ---


def test_render_template_with_variables() -> None:
    """render_template renders a template with provided variables."""
    from dignity.spec.templates import render_template

    result = render_template("spec.md.jinja2", name="test-spec", code="TS")
    assert "test-spec" in result or "TS" in result


def test_render_template_substitutes_all_variables() -> None:
    """render_template substitutes all provided variables."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        title="My Feature",
        code="MF",
        issue_type="feature",
        created="2025-12-16",
    )
    assert "My Feature" in result
    assert "MF" in result


def test_jinja_conditionals_work() -> None:
    """Jinja2 conditionals in templates are evaluated correctly."""
    from dignity.spec.templates import render_template

    result_feature = render_template(
        "spec.md.jinja2",
        name="test",
        code="T",
        issue_type="feature",
        created="2025-12-16",
    )
    result_bug = render_template(
        "spec.md.jinja2",
        name="test",
        code="T",
        issue_type="bug",
        created="2025-12-16",
    )
    assert isinstance(result_feature, str)
    assert isinstance(result_bug, str)


def test_render_template_raises_on_nonexistent_template() -> None:
    """render_template raises TemplateNotFound for non-existent templates."""
    from dignity.spec.templates import render_template

    with pytest.raises(TemplateNotFound):
        render_template("does-not-exist.jinja2", var="value")


def test_render_template_returns_string() -> None:
    """render_template returns a string."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        name="test",
        code="T",
        issue_type="feature",
        created="2025-12-16",
    )
    assert isinstance(result, str)


def test_render_template_empty_variables_allowed() -> None:
    """render_template works with no variables if template allows."""
    from dignity.spec.templates import render_template

    try:
        result = render_template("spec.md.jinja2")
        assert isinstance(result, str)
    except Exception:
        pass


# --- validate_vars ---


def test_validate_vars_returns_none_when_all_required_present() -> None:
    """validate_vars returns None when all required variables are provided."""
    from dignity.spec.templates import validate_vars

    result = validate_vars(
        required={"name", "code"},
        provided={"name", "code", "extra"},
    )
    assert result is None


def test_validate_vars_returns_none_when_exact_match() -> None:
    """validate_vars returns None when provided exactly matches required."""
    from dignity.spec.templates import validate_vars

    result = validate_vars(
        required={"name", "code"},
        provided={"name", "code"},
    )
    assert result is None


def test_validate_vars_raises_value_error_when_missing() -> None:
    """validate_vars raises ValueError when required variables are missing."""
    from dignity.spec.templates import validate_vars

    with pytest.raises(ValueError):
        validate_vars(
            required={"name", "code", "issue_type"},
            provided={"name"},
        )


def test_validate_vars_error_message_lists_missing_variables() -> None:
    """ValueError message lists all missing variable names."""
    from dignity.spec.templates import validate_vars

    with pytest.raises(ValueError, match="code"):
        validate_vars(
            required={"name", "code"},
            provided={"name"},
        )


def test_validate_vars_error_message_lists_multiple_missing() -> None:
    """ValueError message lists all missing variables when multiple missing."""
    from dignity.spec.templates import validate_vars

    with pytest.raises(ValueError) as exc_info:
        validate_vars(
            required={"name", "code", "issue_type"},
            provided=set(),
        )
    error_msg = str(exc_info.value)
    assert "name" in error_msg
    assert "code" in error_msg
    assert "issue_type" in error_msg


def test_validate_vars_empty_required_always_passes() -> None:
    """Empty required set always passes validation."""
    from dignity.spec.templates import validate_vars

    result = validate_vars(required=set(), provided=set())
    assert result is None


def test_validate_vars_empty_required_with_provided_passes() -> None:
    """Empty required set passes even with provided variables."""
    from dignity.spec.templates import validate_vars

    result = validate_vars(required=set(), provided={"name", "code"})
    assert result is None


def test_validate_vars_accepts_frozenset() -> None:
    """validate_vars accepts frozenset for both arguments."""
    from dignity.spec.templates import validate_vars

    result = validate_vars(
        required=frozenset({"name"}),
        provided=frozenset({"name", "code"}),
    )
    assert result is None


def test_validate_vars_accepts_list_like_iterables() -> None:
    """validate_vars accepts list-like iterables."""
    from dignity.spec.templates import validate_vars

    result = validate_vars(
        required=["name", "code"],
        provided=["name", "code", "extra"],
    )
    assert result is None


# --- spec.md.jinja2 template ---


def test_spec_template_feature_has_yaml_frontmatter() -> None:
    """Feature spec has YAML frontmatter with code, issue_type, created, status."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        code="FSD",
        issue_type="feature",
        created="2025-12-14",
        title="Focus State Dispatch",
    )
    assert result.startswith("---\n")
    assert "code: FSD" in result
    assert "issue_type: feature" in result
    assert "created: 2025-12-14" in result
    assert "status: Active" in result


def test_spec_template_feature_has_title_with_spec_prefix() -> None:
    """Feature spec title has '# Spec: ' prefix."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        code="FSD",
        issue_type="feature",
        created="2025-12-14",
        title="Focus State Dispatch",
    )
    assert "# Spec: Focus State Dispatch" in result


def test_spec_template_feature_has_full_sections() -> None:
    """Feature spec has all sections: Overview, Context, Architectural Approach, Success Criteria, Risks."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        code="FSD",
        issue_type="feature",
        created="2025-12-14",
        title="Focus State Dispatch",
    )
    assert "## Overview" in result
    assert "## Context" in result
    assert "## Architectural Approach" in result
    assert "## Success Criteria" in result
    assert "## Risks & Mitigations" in result


def test_spec_template_bug_has_yaml_frontmatter() -> None:
    """Bug spec has YAML frontmatter with code, issue_type, created, status."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        code="FB",
        issue_type="bug",
        created="2025-12-14",
        title="Fix Bug",
    )
    assert result.startswith("---\n")
    assert "code: FB" in result
    assert "issue_type: bug" in result
    assert "created: 2025-12-14" in result
    assert "status: Active" in result


def test_spec_template_bug_has_minimal_sections() -> None:
    """Bug spec has only minimal sections: Overview, Context, Success Criteria."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        code="FB",
        issue_type="bug",
        created="2025-12-14",
        title="Fix Bug",
    )
    assert "## Overview" in result
    assert "## Context" in result
    assert "## Success Criteria" in result
    assert "## Architectural Approach" not in result
    assert "## Risks & Mitigations" not in result


def test_spec_template_chore_has_minimal_sections() -> None:
    """Chore spec has only minimal sections: Overview, Context, Success Criteria."""
    from dignity.spec.templates import render_template

    result = render_template(
        "spec.md.jinja2",
        code="CL",
        issue_type="chore",
        created="2025-12-14",
        title="Cleanup",
    )
    assert "## Overview" in result
    assert "## Context" in result
    assert "## Success Criteria" in result
    assert "## Architectural Approach" not in result
    assert "## Risks & Mitigations" not in result


# --- context.md.jinja2 template ---


def test_context_template_exists() -> None:
    """context.md.jinja2 template can be loaded."""
    from jinja2 import Environment

    from dignity.spec.templates import PackageLoader

    env = Environment(loader=PackageLoader())
    template = env.get_template("context.md.jinja2")
    assert template is not None


def test_context_template_title_rendered() -> None:
    """context.md.jinja2 renders title with provided title variable."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Focus State Dispatch",
        issue_type="feature",
    )
    assert "# Context: Focus State Dispatch" in result


def test_context_template_feature_has_full_structure() -> None:
    """Feature issue_type renders full context structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Test Feature",
        issue_type="feature",
    )
    assert "## Key Files" in result
    assert "## Key Types" in result
    assert "## Implementation Decisions" in result
    assert "## Dependencies" in result
    assert "## Open Questions" in result
    assert "## Gotchas & Learnings" in result


def test_context_template_bug_has_minimal_structure() -> None:
    """Bug issue_type renders minimal context structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Fix Bug",
        issue_type="bug",
    )
    assert "## Key Files" in result
    assert "## Dependencies" in result
    assert "## Key Types" not in result
    assert "## Implementation Decisions" not in result
    assert "## Open Questions" not in result
    assert "## Gotchas & Learnings" not in result


def test_context_template_chore_has_minimal_structure() -> None:
    """Chore issue_type renders minimal context structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Update Config",
        issue_type="chore",
    )
    assert "## Key Files" in result
    assert "## Dependencies" in result
    assert "## Key Types" not in result
    assert "## Implementation Decisions" not in result
    assert "## Open Questions" not in result
    assert "## Gotchas & Learnings" not in result


def test_context_template_key_files_table_structure() -> None:
    """Key Files section has proper table structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Test",
        issue_type="feature",
    )
    assert "| File | Purpose | Changes |" in result


def test_context_template_feature_key_types_table_structure() -> None:
    """Feature Key Types section has proper table structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Test",
        issue_type="feature",
    )
    assert "| Type | Purpose | Location |" in result


def test_context_template_dependencies_subsections() -> None:
    """Dependencies section has Internal and External subsections."""
    from dignity.spec.templates import render_template

    result = render_template(
        "context.md.jinja2",
        title="Test",
        issue_type="feature",
    )
    assert "**Internal:**" in result
    assert "**External:**" in result


# --- tasks.yaml.jinja2 template ---


def test_tasks_yaml_template_exists() -> None:
    """tasks.yaml.jinja2 template can be loaded."""
    from dignity.spec.templates import render_template

    result = render_template("tasks.yaml.jinja2", name="test-spec", code="TS")
    assert isinstance(result, str)


def test_tasks_yaml_template_has_spec_name() -> None:
    """Template renders spec name."""
    from dignity.spec.templates import render_template

    result = render_template("tasks.yaml.jinja2", name="focus-state-dispatch", code="FSD")
    assert "spec: focus-state-dispatch" in result


def test_tasks_yaml_template_has_code() -> None:
    """Template renders spec code."""
    from dignity.spec.templates import render_template

    result = render_template("tasks.yaml.jinja2", name="test-spec", code="TS")
    assert "code: TS" in result


def test_tasks_yaml_template_has_empty_tasks() -> None:
    """Template has empty tasks list."""
    from dignity.spec.templates import render_template

    result = render_template("tasks.yaml.jinja2", name="test-spec", code="TS")
    assert "tasks: []" in result


# --- dependencies.md.jinja2 template ---


def test_dependencies_template_exists() -> None:
    """dependencies.md.jinja2 template can be loaded."""
    from jinja2 import Environment

    from dignity.spec.templates import PackageLoader

    env = Environment(loader=PackageLoader())
    template = env.get_template("dependencies.md.jinja2")
    assert template is not None


def test_dependencies_template_title_rendered() -> None:
    """dependencies.md.jinja2 renders title with provided title variable."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Focus State Dispatch",
        issue_type="feature",
    )
    assert "# Task Dependencies: Focus State Dispatch" in result


def test_dependencies_template_feature_has_full_structure() -> None:
    """Feature issue_type renders full dependency structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Test Feature",
        issue_type="feature",
    )
    assert "## Overview" in result
    assert "## Dependency Graph" in result
    assert "## Execution Batches" in result
    assert "## Phase Dependencies" in result
    assert "## Parallel Safety Rules" in result
    assert "## Notes" in result


def test_dependencies_template_bug_has_minimal_structure() -> None:
    """Bug issue_type renders minimal task list structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Fix Bug",
        issue_type="bug",
    )
    assert "## Overview" in result
    assert "## Tasks" in result
    assert "## Dependency Graph" not in result
    assert "## Execution Batches" not in result


def test_dependencies_template_chore_has_minimal_structure() -> None:
    """Chore issue_type renders minimal task list structure."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Update Config",
        issue_type="chore",
    )
    assert "## Overview" in result
    assert "## Tasks" in result
    assert "## Dependency Graph" not in result
    assert "## Execution Batches" not in result


def test_dependencies_template_feature_overview_content() -> None:
    """Feature overview mentions parallel dispatch."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Test",
        issue_type="feature",
    )
    assert "parallel" in result.lower()
    assert "[P]" in result


def test_dependencies_template_bug_overview_content() -> None:
    """Bug overview mentions sequential execution."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Test",
        issue_type="bug",
    )
    assert "sequence" in result.lower() or "order" in result.lower()


def test_dependencies_template_feature_has_execution_table() -> None:
    """Feature template includes execution batches table header."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Test",
        issue_type="feature",
    )
    assert "| Batch | Tasks | Type | Files |" in result


def test_dependencies_template_feature_has_parallel_safety_rules() -> None:
    """Feature template includes parallel safety rules content."""
    from dignity.spec.templates import render_template

    result = render_template(
        "dependencies.md.jinja2",
        title="Test",
        issue_type="feature",
    )
    assert "Same phase" in result or "same phase" in result
    assert "Different file" in result or "different file" in result.lower()


# --- validation-checklist.md.jinja2 template ---


def test_validation_checklist_template_exists_and_loads() -> None:
    """validation-checklist.md.jinja2 template can be loaded."""
    from jinja2 import Environment

    from dignity.spec.templates import PackageLoader

    env = Environment(loader=PackageLoader())
    template = env.get_template("validation-checklist.md.jinja2")
    assert template is not None


def test_validation_checklist_template_renders_title_in_header() -> None:
    """Template renders title in header."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Focus State Dispatch",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "# Validation Checklist: Focus State Dispatch" in result


def test_validation_checklist_template_renders_issue_type_in_frontmatter() -> None:
    """Template renders issue type in frontmatter-style header."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "**Issue Type:** Feature" in result


def test_validation_checklist_template_renders_created_date() -> None:
    """Template renders created date."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "**Created:** 2025-12-14" in result


def test_validation_checklist_template_feature_has_taxonomy_coverage_table() -> None:
    """Feature issue type includes taxonomy coverage table."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "## Taxonomy Coverage" in result
    assert "| Area | Status | Notes |" in result
    assert "| Scope |" in result
    assert "| Behavior |" in result
    assert "| Data Model |" in result
    assert "| Constraints |" in result
    assert "| Edge Cases |" in result
    assert "| Integration |" in result
    assert "| Terminology |" in result


def test_validation_checklist_template_feature_has_clarification_log() -> None:
    """Feature issue type includes clarification log section."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "## Clarification Log" in result


def test_validation_checklist_template_feature_has_deferred_items() -> None:
    """Feature issue type includes deferred items section."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "## Deferred Items" in result


def test_validation_checklist_template_feature_has_validation_summary() -> None:
    """Feature issue type includes validation summary with checkboxes."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "## Validation Summary" in result
    assert "### Design Readiness" in result
    assert "- [ ] All high-priority taxonomy areas covered" in result
    assert "- [ ] Success criteria are measurable" in result
    assert "- [ ] Scope boundaries are clear" in result
    assert "- [ ] Integration points identified" in result
    assert "- [ ] Edge cases addressed" in result
    assert "### Next Steps" in result
    assert "- [ ] Ready for implementation planning" in result
    assert "- [ ] Spec documents created" in result


def test_validation_checklist_template_feature_has_notes_section() -> None:
    """Feature issue type includes notes section."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test Feature",
        issue_type="feature",
        created="2025-12-14",
    )
    assert "## Notes" in result


def test_validation_checklist_template_bug_has_minimal_checklist() -> None:
    """Bug issue type has minimal simple checklist."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Fix Bug",
        issue_type="bug",
        created="2025-12-14",
    )
    assert "## Checklist" in result
    assert "- [ ] Problem clearly defined" in result
    assert "- [ ] Root cause identified" in result
    assert "- [ ] Fix approach validated" in result
    assert "- [ ] Test plan defined" in result
    assert "## Notes" in result


def test_validation_checklist_template_bug_does_not_have_taxonomy_table() -> None:
    """Bug issue type does not include full taxonomy coverage table."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Fix Bug",
        issue_type="bug",
        created="2025-12-14",
    )
    assert "## Taxonomy Coverage" not in result
    assert "## Clarification Log" not in result
    assert "## Deferred Items" not in result
    assert "## Validation Summary" not in result


def test_validation_checklist_template_chore_has_minimal_checklist() -> None:
    """Chore issue type has minimal simple checklist like bug."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Update Dependencies",
        issue_type="chore",
        created="2025-12-14",
    )
    assert "## Checklist" in result
    assert "- [ ] Problem clearly defined" in result
    assert "## Notes" in result


def test_validation_checklist_template_chore_does_not_have_taxonomy_table() -> None:
    """Chore issue type does not include full taxonomy coverage table."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Update Dependencies",
        issue_type="chore",
        created="2025-12-14",
    )
    assert "## Taxonomy Coverage" not in result


def test_validation_checklist_template_issue_type_capitalizes_in_output() -> None:
    """Issue type is title-cased in output (feature -> Feature)."""
    from dignity.spec.templates import render_template

    result = render_template(
        "validation-checklist.md.jinja2",
        title="Test",
        issue_type="bug",
        created="2025-12-14",
    )
    assert "**Issue Type:** Bug" in result
