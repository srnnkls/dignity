"""Tests for dispatch pattern matching functions.

Tests cover:
- All basic matchers (word boundaries, regex, exact, substring)
- Extended trigger matchers for dispatch system
- Edge cases and error handling
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dignity.hooks.dispatch.matchers import (
    match_exact,
    match_file_content,
    match_file_paths,
    match_output_missing_trigger,
    match_regex,
    match_skill_invoked_trigger,
    match_todo_state_trigger,
    match_tool_result_trigger,
    match_trigger,
    match_trigger_group,
    match_word_boundaries,
)
from dignity.hooks.dispatch.types import (
    FilesChangedTrigger,
    HookContext,
    OutputMissingTrigger,
    SkillInvokedTrigger,
    TodoStateTrigger,
    ToolResultTrigger,
    TriggerGroup,
    TriggerSpec,
)


# --- Basic matcher tests ---


def test_match_word_boundaries_simple() -> None:
    """Match single keyword in text."""
    patterns = frozenset({"dataclass"})
    text = "create a dataclass"
    result = match_word_boundaries(text, patterns)
    assert result == frozenset({"dataclass"})


def test_match_word_boundaries_case_insensitive() -> None:
    """Keywords match case-insensitively."""
    patterns = frozenset({"dataclass"})
    text = "Create a DATACLASS"
    result = match_word_boundaries(text, patterns)
    assert result == frozenset({"dataclass"})


def test_match_word_boundaries_word_boundary() -> None:
    """Keywords respect word boundaries."""
    patterns = frozenset({"class"})
    text = "dataclass is not class"
    result = match_word_boundaries(text, patterns)
    assert result == frozenset({"class"})


def test_match_word_boundaries_multiple() -> None:
    """Match multiple keywords."""
    patterns = frozenset({"dataclass", "frozen", "type"})
    text = "create a frozen dataclass type"
    result = match_word_boundaries(text, patterns)
    assert result == frozenset({"dataclass", "frozen", "type"})


def test_match_word_boundaries_no_match() -> None:
    """Return empty set when no matches."""
    patterns = frozenset({"dataclass"})
    text = "create a function"
    result = match_word_boundaries(text, patterns)
    assert result == frozenset()


def test_match_word_boundaries_empty_input() -> None:
    """Handle empty text or patterns."""
    assert match_word_boundaries("", frozenset({"dataclass"})) == frozenset()
    assert match_word_boundaries("text", frozenset()) == frozenset()
    assert match_word_boundaries("", frozenset()) == frozenset()


def test_match_regex_simple() -> None:
    """Match simple regex pattern."""
    patterns = frozenset({"create.*dataclass"})
    text = "create a dataclass"
    result = match_regex(text, patterns)
    assert result == frozenset({"create.*dataclass"})


def test_match_regex_case_insensitive() -> None:
    """Patterns match case-insensitively."""
    patterns = frozenset({"create.*dataclass"})
    text = "CREATE A DATACLASS"
    result = match_regex(text, patterns)
    assert result == frozenset({"create.*dataclass"})


def test_match_regex_multiple() -> None:
    """Match multiple patterns."""
    patterns = frozenset({"create.*dataclass", "frozen.*True"})
    text = "create a frozen dataclass with frozen=True"
    result = match_regex(text, patterns)
    assert result == patterns


def test_match_regex_no_match() -> None:
    """Return empty set when no matches."""
    patterns = frozenset({"create.*dataclass"})
    text = "delete a function"
    result = match_regex(text, patterns)
    assert result == frozenset()


def test_match_regex_invalid_pattern() -> None:
    """Skip invalid regex patterns."""
    patterns = frozenset({"[invalid"})
    text = "some text"
    result = match_regex(text, patterns)
    assert result == frozenset()


def test_match_regex_empty_input() -> None:
    """Handle empty text or patterns."""
    assert match_regex("", frozenset({".*"})) == frozenset()
    assert match_regex("text", frozenset()) == frozenset()


def test_match_exact_simple() -> None:
    """Match exact string."""
    patterns = frozenset({"Read"})
    value = "Read"
    result = match_exact(value, patterns)
    assert result == frozenset({"Read"})


def test_match_exact_case_insensitive() -> None:
    """Exact match is case-insensitive."""
    patterns = frozenset({"Read"})
    value = "read"
    result = match_exact(value, patterns)
    assert result == frozenset({"Read"})


def test_match_exact_no_match() -> None:
    """Return empty set when no match."""
    patterns = frozenset({"Read"})
    value = "Write"
    result = match_exact(value, patterns)
    assert result == frozenset()


def test_match_exact_empty_input() -> None:
    """Handle empty value or patterns."""
    assert match_exact("", frozenset({"Read"})) == frozenset()
    assert match_exact("Read", frozenset()) == frozenset()


def test_match_file_paths_simple_glob() -> None:
    """Match simple glob pattern."""
    path = Path("src/types.py")
    patterns = frozenset({"src/*.py"})
    assert match_file_paths(path, patterns) is True


def test_match_file_paths_recursive_glob() -> None:
    """Match recursive glob pattern."""
    path = Path("src/feature_link/types.py")
    patterns = frozenset({"src/**/*.py"})
    assert match_file_paths(path, patterns) is True


def test_match_file_paths_no_match() -> None:
    """Return False when no match."""
    path = Path("tests/test_types.py")
    patterns = frozenset({"src/**/*.py"})
    assert match_file_paths(path, patterns) is False


def test_match_file_paths_multiple_patterns() -> None:
    """Match any of multiple patterns."""
    path = Path("src/types.py")
    patterns = frozenset({"src/*.py", "tests/*.py"})
    assert match_file_paths(path, patterns) is True


def test_match_file_paths_empty_patterns() -> None:
    """Return False for empty patterns."""
    path = Path("src/types.py")
    assert match_file_paths(path, frozenset()) is False


def test_match_file_content_simple(tmp_path: Path) -> None:
    """Match pattern in file content."""
    file = tmp_path / "test.py"
    file.write_text("@dataclass\nclass Foo:\n    pass")

    patterns = frozenset({"@dataclass"})
    result = match_file_content(file, patterns)
    assert result == frozenset({"@dataclass"})


def test_match_file_content_regex(tmp_path: Path) -> None:
    """Match regex pattern in file."""
    file = tmp_path / "test.py"
    file.write_text("class Foo(BaseClass):\n    pass")

    patterns = frozenset({r"class\s+\w+\("})
    result = match_file_content(file, patterns)
    assert result == frozenset({r"class\s+\w+\("})


def test_match_file_content_no_match(tmp_path: Path) -> None:
    """Return empty set when no match."""
    file = tmp_path / "test.py"
    file.write_text("def foo():\n    pass")

    patterns = frozenset({"@dataclass"})
    result = match_file_content(file, patterns)
    assert result == frozenset()


def test_match_file_content_nonexistent() -> None:
    """Handle nonexistent file gracefully."""
    file = Path("/nonexistent/file.py")
    patterns = frozenset({"@dataclass"})
    result = match_file_content(file, patterns)
    assert result == frozenset()


def test_match_file_content_max_bytes(tmp_path: Path) -> None:
    """Only read up to max_bytes."""
    file = tmp_path / "test.py"
    content = "x" * 20000 + "@dataclass"
    file.write_text(content)

    patterns = frozenset({"@dataclass"})
    result = match_file_content(file, patterns, max_bytes=10000)
    assert result == frozenset()


def test_match_file_content_empty_patterns(tmp_path: Path) -> None:
    """Return empty set for empty patterns."""
    file = tmp_path / "test.py"
    file.write_text("@dataclass\nclass Foo:\n    pass")

    result = match_file_content(file, frozenset())
    assert result == frozenset()


# --- Extended trigger matcher tests ---


def test_match_tool_result_trigger_tool_name_match() -> None:
    """Match when tool_name is in tool_results."""
    trigger = ToolResultTrigger(tool_name=frozenset({"Read", "Write"}))
    context: HookContext = {
        "tool_results": [
            {"tool_name": "Read"},
            {"tool_name": "Bash"},
        ],
    }
    result = match_tool_result_trigger(trigger, context)
    assert result == frozenset({"Read"})


def test_match_tool_result_trigger_tool_name_no_match() -> None:
    """Return empty when tool_name not in tool_results."""
    trigger = ToolResultTrigger(tool_name=frozenset({"SlashCommand"}))
    context: HookContext = {
        "tool_results": [
            {"tool_name": "Read"},
            {"tool_name": "Write"},
        ],
    }
    result = match_tool_result_trigger(trigger, context)
    assert result == frozenset()


def test_match_tool_result_trigger_parameter_patterns() -> None:
    """Match tool with parameter refinement."""
    trigger = ToolResultTrigger(
        tool_name=frozenset({"SlashCommand"}),
        parameter_patterns={
            "command": frozenset({r"/spec\..*"}),
        },
    )
    context: HookContext = {
        "tool_results": [
            {
                "tool_name": "SlashCommand",
                "parameters": {"command": "/spec.create"},
            }
        ],
    }
    result = match_tool_result_trigger(trigger, context)
    assert result == frozenset({"SlashCommand", r"/spec\..*"})


def test_match_tool_result_trigger_parameter_no_match() -> None:
    """Return empty when tool matches but parameter doesn't."""
    trigger = ToolResultTrigger(
        tool_name=frozenset({"SlashCommand"}),
        parameter_patterns={
            "command": frozenset({r"/spec\..*"}),
        },
    )
    context: HookContext = {
        "tool_results": [
            {
                "tool_name": "SlashCommand",
                "parameters": {"command": "/other.command"},
            }
        ],
    }
    result = match_tool_result_trigger(trigger, context)
    assert result == frozenset()


def test_match_tool_result_trigger_empty_trigger() -> None:
    """Return empty for empty trigger."""
    trigger = ToolResultTrigger()
    context: HookContext = {
        "tool_names": {"Read"},
        "tool_results": [],
    }
    result = match_tool_result_trigger(trigger, context)
    assert result == frozenset()


def test_match_todo_state_trigger_any_completed() -> None:
    """Match when any todo is completed."""
    trigger = TodoStateTrigger(any_completed=True)
    context: HookContext = {
        "todo_state": {
            "any_completed": True,
            "all_completed": False,
        }
    }
    result = match_todo_state_trigger(trigger, context)
    assert result == frozenset({"any_completed"})


def test_match_todo_state_trigger_all_completed() -> None:
    """Match when all todos are completed."""
    trigger = TodoStateTrigger(all_completed=True)
    context: HookContext = {
        "todo_state": {
            "any_completed": True,
            "all_completed": True,
        }
    }
    result = match_todo_state_trigger(trigger, context)
    assert result == frozenset({"all_completed"})


def test_match_todo_state_trigger_both() -> None:
    """Match both conditions."""
    trigger = TodoStateTrigger(any_completed=True, all_completed=True)
    context: HookContext = {
        "todo_state": {
            "any_completed": True,
            "all_completed": True,
        }
    }
    result = match_todo_state_trigger(trigger, context)
    assert result == frozenset({"any_completed", "all_completed"})


def test_match_todo_state_trigger_no_match() -> None:
    """Return empty when conditions not met."""
    trigger = TodoStateTrigger(all_completed=True)
    context: HookContext = {
        "todo_state": {
            "any_completed": True,
            "all_completed": False,
        }
    }
    result = match_todo_state_trigger(trigger, context)
    assert result == frozenset()


def test_match_todo_state_trigger_missing_context() -> None:
    """Handle missing todo_state in context."""
    trigger = TodoStateTrigger(any_completed=True)
    context: HookContext = {}
    result = match_todo_state_trigger(trigger, context)
    assert result == frozenset()


def test_match_skill_invoked_trigger_match() -> None:
    """Match when skill was invoked."""
    trigger = SkillInvokedTrigger(skill="spec-create")
    context: HookContext = {
        "invoked_skills": {"spec-create", "code-test"},
    }
    result = match_skill_invoked_trigger(trigger, context)
    assert result == frozenset({"spec-create"})


def test_match_skill_invoked_trigger_no_match() -> None:
    """Return empty when skill not invoked."""
    trigger = SkillInvokedTrigger(skill="spec-create")
    context: HookContext = {
        "invoked_skills": {"code-test"},
    }
    result = match_skill_invoked_trigger(trigger, context)
    assert result == frozenset()


def test_match_skill_invoked_trigger_missing_context() -> None:
    """Handle missing invoked_skills in context."""
    trigger = SkillInvokedTrigger(skill="spec-create")
    context: HookContext = {}
    result = match_skill_invoked_trigger(trigger, context)
    assert result == frozenset()


def test_match_output_missing_trigger_all_missing() -> None:
    """Fire when all required patterns are missing."""
    trigger = OutputMissingTrigger(
        required_patterns=frozenset({"tdd_evidence", "tests_written"})
    )
    context: HookContext = {
        "last_response": "This is a response without the required patterns.",
    }
    result = match_output_missing_trigger(trigger, context)
    assert result == frozenset({"tdd_evidence", "tests_written"})


def test_match_output_missing_trigger_one_present() -> None:
    """Don't fire when at least one pattern is present."""
    trigger = OutputMissingTrigger(
        required_patterns=frozenset({"tdd_evidence", "tests_written"})
    )
    context: HookContext = {
        "last_response": "Output contains tdd_evidence but not the other.",
    }
    result = match_output_missing_trigger(trigger, context)
    assert result == frozenset()


def test_match_output_missing_trigger_all_present() -> None:
    """Don't fire when all patterns are present."""
    trigger = OutputMissingTrigger(
        required_patterns=frozenset({"tdd_evidence", "tests_written"})
    )
    context: HookContext = {
        "last_response": "Output has tdd_evidence and tests_written included.",
    }
    result = match_output_missing_trigger(trigger, context)
    assert result == frozenset()


def test_match_output_missing_trigger_empty_patterns() -> None:
    """Return empty for empty patterns."""
    trigger = OutputMissingTrigger(required_patterns=frozenset())
    context: HookContext = {
        "last_response": "Some output",
    }
    result = match_output_missing_trigger(trigger, context)
    assert result == frozenset()


def test_match_output_missing_trigger_missing_context() -> None:
    """Handle missing last_response in context."""
    trigger = OutputMissingTrigger(required_patterns=frozenset({"tdd_evidence"}))
    context: HookContext = {}
    result = match_output_missing_trigger(trigger, context)
    assert result == frozenset({"tdd_evidence"})


# --- match_trigger integration tests ---


def test_match_trigger_field_patterns() -> None:
    """Match trigger with field patterns."""
    trigger = TriggerSpec(
        patterns={
            "keywords": frozenset({"test", "implement"}),
        }
    )
    context: HookContext = {
        "keywords": "please test the implementation",
    }
    result = match_trigger(trigger, context)
    assert result == frozenset({"test"})


def test_match_trigger_multiple_fields() -> None:
    """Match trigger with multiple text field patterns."""
    trigger = TriggerSpec(
        patterns={
            "keywords": frozenset({"test"}),
            "intent_patterns": frozenset({r"please.*this"}),
        }
    )
    context: HookContext = {
        "keywords": "please test this",
        "intent_patterns": "please test this",
    }
    result = match_trigger(trigger, context)
    assert result == frozenset({"test", r"please.*this"})


def test_match_trigger_no_match() -> None:
    """Return empty when no patterns match."""
    trigger = TriggerSpec(
        patterns={
            "keywords": frozenset({"missing"}),
        }
    )
    context: HookContext = {
        "keywords": "some other text",
    }
    result = match_trigger(trigger, context)
    assert result == frozenset()


def test_match_trigger_unknown_field() -> None:
    """Skip unknown field names."""
    trigger = TriggerSpec(
        patterns={
            "unknown_field": frozenset({"value"}),
        }
    )
    context: HookContext = {
        "unknown_field": "value",
    }
    result = match_trigger(trigger, context)
    assert result == frozenset()


def test_match_trigger_empty_patterns() -> None:
    """Handle empty patterns."""
    trigger = TriggerSpec(patterns={})
    context: HookContext = {
        "keywords": "some text",
    }
    result = match_trigger(trigger, context)
    assert result == frozenset()


# --- match_trigger_group AND semantics tests ---


def test_match_trigger_group_single_trigger_match() -> None:
    """Match group with single active trigger."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"test"})},
    )
    context: HookContext = {"keywords": "please test this"}
    result = match_trigger_group(group, context)
    assert result is not None
    matched, captures = result
    assert matched == frozenset({"test"})
    assert captures == {}


def test_match_trigger_group_single_trigger_no_match() -> None:
    """Return None when single trigger doesn't match."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"missing"})},
    )
    context: HookContext = {"keywords": "some text"}
    result = match_trigger_group(group, context)
    assert result is None


def test_match_trigger_group_and_semantics_both_match() -> None:
    """Match group when ALL active triggers match (AND)."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"test"})},
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
    )
    context: HookContext = {
        "keywords": "please test this",
        "tool_results": [{"tool_name": "TodoWrite", "parameters": {}}],
    }
    result = match_trigger_group(group, context)
    assert result is not None
    matched, captures = result
    assert "test" in matched
    assert "TodoWrite" in matched


def test_match_trigger_group_and_semantics_one_fails() -> None:
    """Return None when one active trigger doesn't match (AND fails)."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"test"})},
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
    )
    context: HookContext = {
        "keywords": "please test this",  # This matches
        "tool_results": [{"tool_name": "Read", "parameters": {}}],  # This doesn't
    }
    result = match_trigger_group(group, context)
    assert result is None


def test_match_trigger_group_empty_no_match() -> None:
    """Return None for empty group (no active triggers)."""
    group = TriggerGroup()
    context: HookContext = {"keywords": "anything"}
    result = match_trigger_group(group, context)
    assert result is None


def test_match_trigger_group_three_triggers_all_match() -> None:
    """Match when all three active triggers match."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"test"})},
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
        skill_invoked=SkillInvokedTrigger(skill="code-test"),
    )
    context: HookContext = {
        "keywords": "please test",
        "tool_results": [{"tool_name": "TodoWrite", "parameters": {}}],
        "invoked_skills": {"code-test"},
    }
    result = match_trigger_group(group, context)
    assert result is not None
    matched, captures = result
    assert "test" in matched
    assert "TodoWrite" in matched
    assert "code-test" in matched


def test_match_trigger_group_three_triggers_one_fails() -> None:
    """Return None when one of three triggers doesn't match."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"test"})},
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
        skill_invoked=SkillInvokedTrigger(skill="code-test"),
    )
    context: HookContext = {
        "keywords": "please test",
        "tool_results": [{"tool_name": "TodoWrite", "parameters": {}}],
        "invoked_skills": {"other-skill"},  # Doesn't match
    }
    result = match_trigger_group(group, context)
    assert result is None


def test_match_trigger_group_files_changed_with_captures() -> None:
    """Match files_changed trigger and extract named capture groups."""
    group = TriggerGroup(
        files_changed=FilesChangedTrigger(
            path_patterns=frozenset({r"specs/active/(?P<spec_id>[^/]+)/tasks\.md"})
        ),
    )
    context: HookContext = {
        "changed_files": ["specs/active/my-feature/tasks.md"],
    }
    result = match_trigger_group(group, context)
    assert result is not None
    matched, captures = result
    assert len(matched) > 0
    assert captures.get("spec_id") == "my-feature"


def test_match_trigger_group_files_changed_no_captures() -> None:
    """Match files_changed trigger without capture groups."""
    group = TriggerGroup(
        files_changed=FilesChangedTrigger(
            path_patterns=frozenset({r"specs/active/.*/tasks\.md"})
        ),
    )
    context: HookContext = {
        "changed_files": ["specs/active/my-feature/tasks.md"],
    }
    result = match_trigger_group(group, context)
    assert result is not None
    matched, captures = result
    assert len(matched) > 0
    assert captures == {}
