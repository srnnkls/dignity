"""TDD Evidence: Stop Hook Implementation

Demonstrates RED -> GREEN workflow for Stop hook functionality.
Tests written FIRST, then implementation follows.
"""

from __future__ import annotations

import pytest

from dignity.hooks.dispatch.dispatcher import analyze_hook
from dignity.hooks.dispatch.extractors import extract_stop_context
from dignity.hooks.dispatch.types import (
    BlockAction,
    RemindAction,
    Rule,
    SuggestSkillAction,
    TodoStateTrigger,
    ToolResultTrigger,
    TriggerSpec,
)


class TestStopHookTDD:
    """RED -> GREEN: Stop hook implementation tests."""

    def test_stop_hook_extracts_tool_results(self) -> None:
        """GIVEN: Stop hook data with tool results
        WHEN: Extracting context
        THEN: tool_results are available in context
        """
        data = {
            "tool_results": [
                {"tool_name": "Read", "parameters": {}},
                {"tool_name": "Write", "parameters": {}},
            ]
        }
        context = extract_stop_context(data)
        assert "tool_results" in context
        assert len(context["tool_results"]) == 2

    def test_stop_hook_extracts_todo_state(self) -> None:
        """GIVEN: Stop hook with TodoWrite results
        WHEN: Extracting context
        THEN: todo_state shows completion status
        """
        data = {
            "tool_results": [
                {
                    "tool_name": "TodoWrite",
                    "parameters": {
                        "todos": [
                            {"status": "completed", "content": "task1"},
                            {"status": "pending", "content": "task2"},
                        ]
                    },
                }
            ]
        }
        context = extract_stop_context(data)
        assert "todo_state" in context
        assert context["todo_state"]["any_completed"] is True
        assert context["todo_state"]["all_completed"] is False

    def test_stop_hook_extracts_invoked_skills(self) -> None:
        """GIVEN: Stop hook with Skill tool results
        WHEN: Extracting context
        THEN: invoked_skills set contains skill names
        """
        data = {
            "tool_results": [
                {"tool_name": "Skill", "parameters": {"skill": "code-test"}},
                {"tool_name": "Skill", "parameters": {"skill": "code-debug"}},
            ]
        }
        context = extract_stop_context(data)
        assert "invoked_skills" in context
        assert "code-test" in context["invoked_skills"]
        assert "code-debug" in context["invoked_skills"]

    def test_stop_hook_rule_matching_tool_result(self) -> None:
        """GIVEN: Rule with ToolResultTrigger for Stop hook
        WHEN: Analyzing Stop hook event
        THEN: Rule matches when tool was used
        """
        rule = Rule(
            name="suggest-on-read",
            priority="medium",
            action=SuggestSkillAction(skill="code-debug", reason="Read tool used"),
            triggers={
                "Stop": TriggerSpec(
                    tool_result=ToolResultTrigger(tool_name=frozenset({"Read"}))
                )
            },
        )
        rules = {"suggest-on-read": rule}

        context = {
            "hook_event": "Stop",
            "tool_results": [{"tool_name": "Read"}],
        }

        matches = analyze_hook("Stop", context, rules)
        assert len(matches) == 1
        assert matches[0].rule_name == "suggest-on-read"

    def test_stop_hook_rule_matching_todo_state(self) -> None:
        """GIVEN: Rule with TodoStateTrigger for Stop hook
        WHEN: Analyzing Stop hook with completed todos
        THEN: Rule matches on any_completed
        """
        rule = Rule(
            name="remind-on-todo-progress",
            priority="high",
            action=RemindAction(message="Nice progress on todos!"),
            triggers={
                "Stop": TriggerSpec(
                    todo_state=TodoStateTrigger(any_completed=True)
                )
            },
        )
        rules = {"remind-on-todo-progress": rule}

        context = {
            "hook_event": "Stop",
            "todo_state": {
                "any_completed": True,
                "all_completed": False,
            },
        }

        matches = analyze_hook("Stop", context, rules)
        assert len(matches) == 1
        assert matches[0].rule_name == "remind-on-todo-progress"
        assert isinstance(matches[0].action, RemindAction)

    def test_stop_hook_no_match_when_conditions_unmet(self) -> None:
        """GIVEN: Rule with conditions not met
        WHEN: Analyzing Stop hook
        THEN: Rule does not match
        """
        rule = Rule(
            name="suggest-on-read",
            priority="medium",
            action=SuggestSkillAction(skill="code-debug"),
            triggers={
                "Stop": TriggerSpec(
                    tool_result=ToolResultTrigger(tool_name=frozenset({"Read"}))
                )
            },
        )
        rules = {"suggest-on-read": rule}

        context = {
            "hook_event": "Stop",
            "tool_results": [{"tool_name": "Write"}],  # Different tool
        }

        matches = analyze_hook("Stop", context, rules)
        assert len(matches) == 0

    def test_stop_hook_multiple_rules_matching(self) -> None:
        """GIVEN: Multiple rules that match
        WHEN: Analyzing Stop hook
        THEN: All matching rules are returned, sorted by priority
        """
        rule_high = Rule(
            name="high-priority",
            priority="high",
            action=RemindAction(message="High priority action"),
            triggers={
                "Stop": TriggerSpec(
                    tool_result=ToolResultTrigger(tool_name=frozenset({"Read"}))
                )
            },
        )
        rule_low = Rule(
            name="low-priority",
            priority="low",
            action=RemindAction(message="Low priority action"),
            triggers={
                "Stop": TriggerSpec(
                    tool_result=ToolResultTrigger(tool_name=frozenset({"Read"}))
                )
            },
        )
        rules = {"high": rule_high, "low": rule_low}

        context = {
            "hook_event": "Stop",
            "tool_results": [{"tool_name": "Read"}],
        }

        matches = analyze_hook("Stop", context, rules)
        assert len(matches) == 2
        # High priority should come first
        assert matches[0].priority == "high"
        assert matches[1].priority == "low"
