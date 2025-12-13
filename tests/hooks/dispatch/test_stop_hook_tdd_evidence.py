"""TDD Evidence: Stop Hook - RED Phase Tests

These tests demonstrate the TDD workflow:
1. Write failing tests FIRST (RED phase)
2. Implement code to pass tests (GREEN phase)
3. Verify all tests pass

This file contains tests for Stop hook functionality.
"""

from __future__ import annotations

import pytest

from dignity.hooks.dispatch.extractors import extract_stop_context
from dignity.hooks.dispatch.matchers import (
    match_skill_invoked_trigger,
    match_todo_state_trigger,
    match_tool_result_trigger,
)
from dignity.hooks.dispatch.types import (
    HookContext,
    SkillInvokedTrigger,
    TodoStateTrigger,
    ToolResultTrigger,
)


class TestStopHookExtraction:
    """Stop hook context extraction tests."""

    def test_extract_stop_context_returns_dict(self) -> None:
        """Stop hook context extraction returns a dictionary."""
        data: dict = {}
        context = extract_stop_context(data)
        assert isinstance(context, dict)

    def test_extract_stop_context_includes_hook_event(self) -> None:
        """Extracted context includes hook_event = 'Stop'."""
        data: dict = {}
        context = extract_stop_context(data)
        assert context.get("hook_event") == "Stop"

    def test_extract_stop_context_includes_tool_results(self) -> None:
        """Extracted context includes tool_results from input."""
        data = {
            "tool_results": [
                {"tool_name": "Read", "parameters": {}},
            ]
        }
        context = extract_stop_context(data)
        assert "tool_results" in context
        assert len(context["tool_results"]) == 1

    def test_extract_stop_context_includes_todo_state(self) -> None:
        """Extracted context includes todo_state dict."""
        data: dict = {}
        context = extract_stop_context(data)
        assert "todo_state" in context
        assert isinstance(context["todo_state"], dict)

    def test_extract_stop_context_includes_invoked_skills(self) -> None:
        """Extracted context includes invoked_skills set."""
        data: dict = {}
        context = extract_stop_context(data)
        assert "invoked_skills" in context
        assert isinstance(context["invoked_skills"], set)


class TestToolResultTrigger:
    """Tool result trigger matching tests."""

    def test_match_tool_result_with_matching_tool(self) -> None:
        """Tool result trigger matches when tool is in results."""
        trigger = ToolResultTrigger(tool_name=frozenset({"Read"}))
        context: HookContext = {
            "tool_results": [
                {"tool_name": "Read"},
            ]
        }
        result = match_tool_result_trigger(trigger, context)
        assert "Read" in result

    def test_match_tool_result_with_nonmatching_tool(self) -> None:
        """Tool result trigger returns empty when tool doesn't match."""
        trigger = ToolResultTrigger(tool_name=frozenset({"Read"}))
        context: HookContext = {
            "tool_results": [
                {"tool_name": "Write"},
            ]
        }
        result = match_tool_result_trigger(trigger, context)
        assert len(result) == 0

    def test_match_tool_result_with_parameter_patterns(self) -> None:
        """Tool result trigger matches parameter patterns."""
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
            ]
        }
        result = match_tool_result_trigger(trigger, context)
        assert "SlashCommand" in result or len(result) > 0

    def test_match_tool_result_empty_trigger(self) -> None:
        """Empty tool result trigger returns empty result."""
        trigger = ToolResultTrigger()
        context: HookContext = {
            "tool_results": [
                {"tool_name": "Read"},
            ]
        }
        result = match_tool_result_trigger(trigger, context)
        assert len(result) == 0


class TestTodoStateTrigger:
    """Todo state trigger matching tests."""

    def test_match_todo_state_any_completed(self) -> None:
        """Todo state trigger matches when any todo is completed."""
        trigger = TodoStateTrigger(any_completed=True)
        context: HookContext = {
            "todo_state": {
                "any_completed": True,
                "all_completed": False,
            }
        }
        result = match_todo_state_trigger(trigger, context)
        assert "any_completed" in result

    def test_match_todo_state_all_completed(self) -> None:
        """Todo state trigger matches when all todos are completed."""
        trigger = TodoStateTrigger(all_completed=True)
        context: HookContext = {
            "todo_state": {
                "any_completed": True,
                "all_completed": True,
            }
        }
        result = match_todo_state_trigger(trigger, context)
        assert "all_completed" in result

    def test_match_todo_state_no_match(self) -> None:
        """Todo state trigger returns empty when condition not met."""
        trigger = TodoStateTrigger(all_completed=True)
        context: HookContext = {
            "todo_state": {
                "any_completed": True,
                "all_completed": False,
            }
        }
        result = match_todo_state_trigger(trigger, context)
        assert len(result) == 0

    def test_match_todo_state_missing_context(self) -> None:
        """Todo state trigger handles missing context gracefully."""
        trigger = TodoStateTrigger(any_completed=True)
        context: HookContext = {}
        result = match_todo_state_trigger(trigger, context)
        assert isinstance(result, frozenset)


class TestSkillInvokedTrigger:
    """Skill invoked trigger matching tests."""

    def test_match_skill_invoked_matching(self) -> None:
        """Skill invoked trigger matches when skill is invoked."""
        trigger = SkillInvokedTrigger(skill="code-test")
        context: HookContext = {
            "invoked_skills": {"code-test", "code-debug"},
        }
        result = match_skill_invoked_trigger(trigger, context)
        assert "code-test" in result

    def test_match_skill_invoked_nonmatching(self) -> None:
        """Skill invoked trigger returns empty when skill not invoked."""
        trigger = SkillInvokedTrigger(skill="code-test")
        context: HookContext = {
            "invoked_skills": {"code-debug"},
        }
        result = match_skill_invoked_trigger(trigger, context)
        assert len(result) == 0

    def test_match_skill_invoked_missing_context(self) -> None:
        """Skill invoked trigger handles missing context gracefully."""
        trigger = SkillInvokedTrigger(skill="code-test")
        context: HookContext = {}
        result = match_skill_invoked_trigger(trigger, context)
        assert isinstance(result, frozenset)
