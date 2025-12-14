"""Tests for dispatch domain types.

Tests cover:
- Action types (discriminated union)
- Trigger types (tool result, todo state, skill invoked, output missing, files changed)
- Core types (Priority, HookEvent, Rule, Match, RuleSet)
- Trigger groups (AND/OR logic)
- Type immutability and validation
"""

from __future__ import annotations

import pytest

from dignity.hooks.dispatch.types import (
    BlockAction,
    FilesChangedTrigger,
    HookEvent,
    InjectContextAction,
    Match,
    OutputMissingTrigger,
    Priority,
    RemindAction,
    Rule,
    RuleSet,
    SkillInvokedTrigger,
    SuggestSkillAction,
    TodoStateTrigger,
    ToolResultTrigger,
    TriggerGroup,
    TriggerSpec,
)


# TriggerGroup tests (flat functions)


def test_trigger_group_creation() -> None:
    """TriggerGroup should hold all trigger fields."""
    group = TriggerGroup(
        patterns={"keywords": frozenset({"test"})},
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
        files_changed=FilesChangedTrigger(
            path_patterns=frozenset({"specs/active/**/tasks.md"})
        ),
    )
    assert "keywords" in group.patterns
    assert "TodoWrite" in group.tool_result.tool_name
    assert "specs/active/**/tasks.md" in group.files_changed.path_patterns


def test_trigger_group_immutable() -> None:
    """TriggerGroup should be immutable."""
    group = TriggerGroup()
    with pytest.raises(Exception):
        group.patterns = {}  # type: ignore[misc]


def test_trigger_group_defaults() -> None:
    """TriggerGroup should default to inactive triggers."""
    group = TriggerGroup()
    assert group.patterns == {}
    assert not group.tool_result.is_active()
    assert not group.todo_state.is_active()
    assert not group.skill_invoked.is_active()
    assert not group.output_missing.is_active()
    assert not group.files_changed.is_active()


def test_trigger_spec_with_explicit_groups() -> None:
    """TriggerSpec should support list of trigger groups."""
    group1 = TriggerGroup(
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
        files_changed=FilesChangedTrigger(
            path_patterns=frozenset({"specs/active/**/tasks.md"})
        ),
    )
    group2 = TriggerGroup(
        skill_invoked=SkillInvokedTrigger(skill="spec-create"),
    )
    spec = TriggerSpec(groups=(group1, group2))
    assert len(spec.groups) == 2


def test_trigger_spec_backwards_compat() -> None:
    """TriggerSpec without groups should work as single group."""
    spec = TriggerSpec(
        patterns={"keywords": frozenset({"test"})},
        tool_result=ToolResultTrigger(tool_name=frozenset({"TodoWrite"})),
    )
    assert len(spec.groups) == 1
    assert "keywords" in spec.groups[0].patterns
    assert "TodoWrite" in spec.groups[0].tool_result.tool_name


def test_trigger_spec_empty_has_no_groups() -> None:
    """TriggerSpec with no triggers should have no groups."""
    spec = TriggerSpec()
    assert len(spec.groups) == 0


def test_trigger_spec_explicit_empty_groups() -> None:
    """TriggerSpec with explicit empty groups tuple should have no groups."""
    spec = TriggerSpec(groups=())
    assert len(spec.groups) == 0


class TestActionTypes:
    """Test Action type hierarchy and discriminated union."""

    def test_suggest_skill_action_creation(self) -> None:
        """SuggestSkillAction should have type, skill, and reason."""
        action = SuggestSkillAction(
            skill="code-test",
            reason="Test pattern detected",
        )
        assert action.type == "suggest_skill"
        assert action.skill == "code-test"
        assert action.reason == "Test pattern detected"

    def test_suggest_skill_action_immutable(self) -> None:
        """SuggestSkillAction should be immutable."""
        action = SuggestSkillAction(skill="code-test", reason="test")
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            action.skill = "other"  # type: ignore[misc]

    def test_remind_action_creation(self) -> None:
        """RemindAction should have type and message."""
        action = RemindAction(message="Remember to run tests")
        assert action.type == "remind"
        assert action.message == "Remember to run tests"

    def test_block_action_creation(self) -> None:
        """BlockAction should have type and reason."""
        action = BlockAction(reason="Missing TDD evidence")
        assert action.type == "block"
        assert action.reason == "Missing TDD evidence"

    def test_inject_context_action_creation(self) -> None:
        """InjectContextAction should have type and context."""
        action = InjectContextAction(context="Additional information")
        assert action.type == "inject_context"
        assert action.context == "Additional information"


class TestTriggerTypes:
    """Test trigger type dataclasses."""

    def test_trigger_spec_basic(self) -> None:
        """TriggerSpec should hold arbitrary pattern dictionaries."""
        spec = TriggerSpec(
            patterns={
                "keywords": frozenset({"test", "implement"}),
                "intent_patterns": frozenset([r"add.*feature"]),
            }
        )
        assert "keywords" in spec.patterns
        assert "test" in spec.patterns["keywords"]

    def test_tool_result_trigger_creation(self) -> None:
        """ToolResultTrigger should match tool names and parameter patterns."""
        trigger = ToolResultTrigger(
            tool_name=frozenset({"SlashCommand", "Skill"}),
            parameter_patterns={
                "command": frozenset([r"/spec\.create"]),
            },
        )
        assert "SlashCommand" in trigger.tool_name
        assert "command" in trigger.parameter_patterns

    def test_todo_state_trigger_creation(self) -> None:
        """TodoStateTrigger should track completion states."""
        trigger = TodoStateTrigger(
            any_completed=True,
            all_completed=False,
        )
        assert trigger.any_completed is True
        assert trigger.all_completed is False

    def test_skill_invoked_trigger_creation(self) -> None:
        """SkillInvokedTrigger should match specific skill names."""
        trigger = SkillInvokedTrigger(skill="spec-create")
        assert trigger.skill == "spec-create"

    def test_output_missing_trigger_creation(self) -> None:
        """OutputMissingTrigger should track required patterns (fires when ALL missing)."""
        trigger = OutputMissingTrigger(
            required_patterns=frozenset(["tdd_evidence:", "red_output:"])
        )
        assert "tdd_evidence:" in trigger.required_patterns
        assert "red_output:" in trigger.required_patterns

    def test_files_changed_trigger_creation(self) -> None:
        """FilesChangedTrigger should match path and content patterns."""
        trigger = FilesChangedTrigger(
            path_patterns=frozenset({"src/**/types.py"}),
            content_patterns=frozenset({"@dataclass", "frozen=True"}),
        )
        assert "src/**/types.py" in trigger.path_patterns
        assert "@dataclass" in trigger.content_patterns


class TestCoreTypes:
    """Test core types: Priority, HookEvent, Rule, Match."""

    def test_priority_literal(self) -> None:
        """Priority should be a literal type with high/medium/low."""
        p1: Priority = "high"
        p2: Priority = "medium"
        p3: Priority = "low"
        assert p1 == "high"
        assert p2 == "medium"
        assert p3 == "low"

    def test_hook_event_literal(self) -> None:
        """HookEvent should include UserPromptSubmit, Stop, SubagentStop."""
        e1: HookEvent = "UserPromptSubmit"
        e2: HookEvent = "Stop"
        e3: HookEvent = "SubagentStop"
        assert e1 == "UserPromptSubmit"
        assert e2 == "Stop"
        assert e3 == "SubagentStop"

    def test_rule_creation(self) -> None:
        """Rule should contain name, priority, action, and triggers by hook."""
        rule = Rule(
            name="tdd-verification",
            priority="high",
            action=BlockAction(reason="Missing TDD evidence"),
            triggers={
                "SubagentStop": TriggerSpec(
                    patterns={
                        "agent_types": frozenset(["task-implementer"]),
                    }
                )
            },
        )
        assert rule.name == "tdd-verification"
        assert rule.priority == "high"
        assert isinstance(rule.action, BlockAction)
        assert "SubagentStop" in rule.triggers

    def test_rule_immutable(self) -> None:
        """Rule should be immutable."""
        rule = Rule(
            name="test",
            priority="medium",
            action=RemindAction(message="test"),
            triggers={},
        )
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            rule.priority = "high"  # type: ignore[misc]

    def test_match_creation(self) -> None:
        """Match should contain rule name, priority, action, and matched patterns."""
        match = Match(
            rule_name="tdd-verification",
            priority="high",
            action=BlockAction(reason="Missing evidence"),
            matched_patterns=frozenset({"task-implementer"}),
        )
        assert match.rule_name == "tdd-verification"
        assert match.priority == "high"
        assert isinstance(match.action, BlockAction)
        assert "task-implementer" in match.matched_patterns

    def test_ruleset_type_alias(self) -> None:
        """RuleSet should be a dict mapping rule names to Rules."""
        ruleset: RuleSet = {
            "rule1": Rule(
                name="rule1",
                priority="high",
                action=RemindAction(message="test"),
                triggers={},
            )
        }
        assert "rule1" in ruleset
        assert isinstance(ruleset["rule1"], Rule)


class TestTriggerDefaults:
    """Test default values for trigger types."""

    def test_trigger_spec_default_patterns(self) -> None:
        """TriggerSpec should default to empty patterns dict."""
        spec = TriggerSpec()
        assert spec.patterns == {}

    def test_tool_result_trigger_default_parameters(self) -> None:
        """ToolResultTrigger should default to empty parameter_patterns."""
        trigger = ToolResultTrigger(tool_name=frozenset({"Tool"}))
        assert trigger.parameter_patterns == {}

    def test_files_changed_trigger_defaults(self) -> None:
        """FilesChangedTrigger should default to empty frozensets."""
        trigger = FilesChangedTrigger()
        assert trigger.path_patterns == frozenset()
        assert trigger.content_patterns == frozenset()
