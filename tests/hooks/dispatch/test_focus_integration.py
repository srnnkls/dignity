"""End-to-end integration tests for focus state dispatch.

Tests the complete workflow:
1. Set focus via Stop hook (TodoWrite on spec tasks.md)
2. Verify state persistence
3. Inject context via UserPromptSubmit when focus exists
4. Clear focus via spec-archive skill
"""

from __future__ import annotations

import pytest

from dignity import state
from dignity.hooks.dispatch.actions import format_user_prompt_output
from dignity.hooks.dispatch.dispatcher import _execute_actions, analyze_hook
from dignity.hooks.dispatch.types import (
    ClearStateAction,
    FilesChangedTrigger,
    InjectContextAction,
    Rule,
    SetStateAction,
    SkillInvokedTrigger,
    StateExistsTrigger,
    ToolResultTrigger,
    TriggerGroup,
    TriggerSpec,
)


@pytest.fixture
def session_id() -> str:
    return "test-focus-session"


@pytest.fixture
def focus_rules() -> dict[str, Rule]:
    """Focus rules matching resources/focus-rules.example.json."""
    return {
        "focus-set": Rule(
            name="focus-set",
            priority="high",
            action=SetStateAction(
                key="focus",
                value_from="captured.spec_id",
            ),
            triggers={
                "Stop": TriggerSpec(
                    groups=(
                        TriggerGroup(
                            tool_result=ToolResultTrigger(
                                tool_name=frozenset({"TodoWrite", "Edit"})
                            ),
                            files_changed=FilesChangedTrigger(
                                path_patterns=frozenset(
                                    {r"specs/active/(?P<spec_id>[^/]+)/tasks\.md"}
                                )
                            ),
                        ),
                    )
                )
            },
        ),
        "focus-clear": Rule(
            name="focus-clear",
            priority="high",
            action=ClearStateAction(key="focus"),
            triggers={
                "Stop": TriggerSpec(
                    skill_invoked=SkillInvokedTrigger(skill="spec-archive")
                )
            },
        ),
        "focus-inject": Rule(
            name="focus-inject",
            priority="medium",
            action=InjectContextAction(context="Current focus: {state.focus}"),
            triggers={
                "UserPromptSubmit": TriggerSpec(
                    state_exists=StateExistsTrigger(key="focus")
                )
            },
        ),
    }


@pytest.fixture(autouse=True)
def clean_state(session_id: str) -> None:
    """Ensure clean state before and after each test."""
    state.clear(session_id, "focus")
    yield
    state.clear(session_id, "focus")


# --- Focus Set Flow ---


def test_focus_set_on_todowrite_to_spec_tasks(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """Focus is set when TodoWrite modifies spec tasks.md."""
    context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "tool_results": [{"tool_name": "TodoWrite"}],
        "changed_files": ["specs/active/my-feature/tasks.md"],
    }

    matches = analyze_hook("Stop", context, focus_rules)

    assert len(matches) == 1
    assert matches[0].rule_name == "focus-set"
    assert matches[0].captures == {"spec_id": "my-feature"}


def test_focus_set_on_edit_to_spec_tasks(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """Focus is set when Edit modifies spec tasks.md."""
    context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "tool_results": [{"tool_name": "Edit"}],
        "changed_files": ["specs/active/another-spec/tasks.md"],
    }

    matches = analyze_hook("Stop", context, focus_rules)

    assert len(matches) == 1
    assert matches[0].rule_name == "focus-set"
    assert matches[0].captures == {"spec_id": "another-spec"}


def test_focus_not_set_without_both_triggers(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """Focus requires BOTH tool match AND file match (AND semantics)."""
    # Only tool, no file
    context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "tool_results": [{"tool_name": "TodoWrite"}],
        "changed_files": [],
    }
    matches = analyze_hook("Stop", context, focus_rules)
    focus_matches = [m for m in matches if m.rule_name == "focus-set"]
    assert len(focus_matches) == 0

    # Only file, wrong tool
    context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "tool_results": [{"tool_name": "Read"}],
        "changed_files": ["specs/active/test/tasks.md"],
    }
    matches = analyze_hook("Stop", context, focus_rules)
    focus_matches = [m for m in matches if m.rule_name == "focus-set"]
    assert len(focus_matches) == 0


# --- Focus Clear Flow ---


def test_focus_clear_on_spec_archive(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """Focus is cleared when spec-archive is invoked."""
    context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "invoked_skills": {"spec-archive"},
    }

    matches = analyze_hook("Stop", context, focus_rules)

    assert len(matches) == 1
    assert matches[0].rule_name == "focus-clear"


# --- Focus Inject Flow ---


def test_focus_inject_when_focus_exists(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """Context is injected when focus state exists."""
    state.set(session_id, "focus", "my-feature")

    context = {
        "session_id": session_id,
        "hook_event": "UserPromptSubmit",
    }

    matches = analyze_hook("UserPromptSubmit", context, focus_rules)

    assert len(matches) == 1
    assert matches[0].rule_name == "focus-inject"


def test_focus_not_injected_when_no_focus(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """No context injection when focus is not set."""
    context = {
        "session_id": session_id,
        "hook_event": "UserPromptSubmit",
    }

    matches = analyze_hook("UserPromptSubmit", context, focus_rules)
    focus_matches = [m for m in matches if m.rule_name == "focus-inject"]

    assert len(focus_matches) == 0


# --- End-to-End ---


def test_full_focus_lifecycle(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """Test complete set → inject → clear cycle."""
    # Step 1: Set focus via Stop hook
    stop_context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "tool_results": [{"tool_name": "TodoWrite"}],
        "changed_files": ["specs/active/lifecycle-test/tasks.md"],
    }
    matches = analyze_hook("Stop", stop_context, focus_rules)
    _execute_actions(matches, stop_context)

    assert state.get(session_id, "focus") == "lifecycle-test"

    # Step 2: Verify focus is injected on UserPromptSubmit
    prompt_context = {
        "session_id": session_id,
        "hook_event": "UserPromptSubmit",
    }
    matches = analyze_hook("UserPromptSubmit", prompt_context, focus_rules)
    output = format_user_prompt_output(matches, prompt_context)

    assert "additionalContext" in output.get("hookSpecificOutput", {})
    assert "lifecycle-test" in output["hookSpecificOutput"]["additionalContext"]

    # Step 3: Clear focus via spec-archive
    clear_context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "invoked_skills": {"spec-archive"},
    }
    matches = analyze_hook("Stop", clear_context, focus_rules)
    _execute_actions(matches, clear_context)

    assert state.get(session_id, "focus") is None

    # Step 4: Verify no injection after clear
    matches = analyze_hook("UserPromptSubmit", prompt_context, focus_rules)
    focus_matches = [m for m in matches if m.rule_name == "focus-inject"]

    assert len(focus_matches) == 0


def test_focus_not_overwritten_if_exists(
    session_id: str, focus_rules: dict[str, Rule]
) -> None:
    """SetStateAction should not overwrite existing focus."""
    state.set(session_id, "focus", "original-spec")

    stop_context = {
        "session_id": session_id,
        "hook_event": "Stop",
        "tool_results": [{"tool_name": "TodoWrite"}],
        "changed_files": ["specs/active/new-spec/tasks.md"],
    }
    matches = analyze_hook("Stop", stop_context, focus_rules)
    _execute_actions(matches, stop_context)

    # Original focus should be preserved
    assert state.get(session_id, "focus") == "original-spec"
