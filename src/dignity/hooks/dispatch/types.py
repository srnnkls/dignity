"""Domain types for declarative hook dispatch system.

All types are immutable (frozen dataclasses) following Python best practices.
Pydantic dataclasses used throughout for validation and discriminated unions.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field
from pydantic.dataclasses import dataclass

Priority = Literal["high", "medium", "low"]

HookEvent = Literal["UserPromptSubmit", "Stop", "SubagentStop"]

HookContext = dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class ToolResultTrigger:
    """Trigger matching tool execution results.

    Fires when a specific tool was used with matching parameters.
    Used in Stop hook to detect workflow transitions.
    """

    tool_name: frozenset[str] = Field(default=frozenset())
    parameter_patterns: dict[str, frozenset[str]] = Field(default_factory=dict)

    def is_active(self) -> bool:
        return bool(self.tool_name)


@dataclass(frozen=True, kw_only=True)
class TodoStateTrigger:
    """Trigger matching todo completion state.

    Fires based on whether any or all todos are completed.
    Used in Stop hook to detect workflow transitions.
    """

    any_completed: bool = False
    all_completed: bool = False

    def is_active(self) -> bool:
        return self.any_completed or self.all_completed


@dataclass(frozen=True, kw_only=True)
class SkillInvokedTrigger:
    """Trigger matching skill invocation.

    Fires when a specific skill was invoked.
    Used in Stop hook to suggest follow-up workflows.
    """

    skill: str = ""

    def is_active(self) -> bool:
        return bool(self.skill)


@dataclass(frozen=True, kw_only=True)
class OutputMissingTrigger:
    """Trigger when required patterns are missing from output.

    Fires when ALL required patterns are absent from the output.
    Used in SubagentStop hook for TDD verification.
    """

    required_patterns: frozenset[str] = Field(default=frozenset())

    def is_active(self) -> bool:
        return bool(self.required_patterns)


@dataclass(frozen=True, kw_only=True)
class FilesChangedTrigger:
    """Trigger matching file changes.

    Fires when files matching path patterns contain matching content patterns.
    Used for file-based activation rules.
    """

    path_patterns: frozenset[str] = Field(default=frozenset())
    content_patterns: frozenset[str] = Field(default=frozenset())

    def is_active(self) -> bool:
        return bool(self.path_patterns or self.content_patterns)


@dataclass(frozen=True, kw_only=True)
class StateExistsTrigger:
    """Trigger that fires when a state key exists.

    Used to check if state has been set before.
    For example, checking if focus is already set.
    """

    key: str = ""

    def is_active(self) -> bool:
        return bool(self.key)


@dataclass(frozen=True, kw_only=True)
class TriggerGroup:
    """A group of triggers that must ALL match (AND semantics).

    Used within TriggerSpec to enable AND/OR logic:
    - Within a group: all active triggers must match (AND)
    - Across groups: any group matching triggers the rule (OR)
    """

    patterns: dict[str, frozenset[str]] = Field(default_factory=dict)
    tool_result: ToolResultTrigger = Field(default_factory=ToolResultTrigger)
    todo_state: TodoStateTrigger = Field(default_factory=TodoStateTrigger)
    skill_invoked: SkillInvokedTrigger = Field(default_factory=SkillInvokedTrigger)
    output_missing: OutputMissingTrigger = Field(default_factory=OutputMissingTrigger)
    files_changed: FilesChangedTrigger = Field(default_factory=FilesChangedTrigger)
    state_exists: StateExistsTrigger = Field(default_factory=StateExistsTrigger)


def _make_default_groups(
    patterns: dict[str, frozenset[str]],
    tool_result: ToolResultTrigger,
    todo_state: TodoStateTrigger,
    skill_invoked: SkillInvokedTrigger,
    output_missing: OutputMissingTrigger,
    files_changed: FilesChangedTrigger,
    state_exists: StateExistsTrigger,
) -> tuple[TriggerGroup, ...]:
    """Create default groups tuple from legacy trigger fields.

    For backwards compatibility: if any trigger field is active,
    create a single-element tuple with one group containing all fields.
    """
    has_any_trigger = (
        patterns
        or tool_result.is_active()
        or todo_state.is_active()
        or skill_invoked.is_active()
        or output_missing.is_active()
        or files_changed.is_active()
        or state_exists.is_active()
    )
    if has_any_trigger:
        return (
            TriggerGroup(
                patterns=patterns,
                tool_result=tool_result,
                todo_state=todo_state,
                skill_invoked=skill_invoked,
                output_missing=output_missing,
                files_changed=files_changed,
                state_exists=state_exists,
            ),
        )
    return ()


@dataclass(frozen=True, kw_only=True)
class TriggerSpec:
    """Generic trigger spec with AND/OR trigger group logic.

    Supports two modes:
    1. Explicit groups: `groups=[TriggerGroup(...), TriggerGroup(...)]`
       - Groups are ORed (any group matching triggers the rule)
       - Within each group, all active triggers must match (AND)

    2. Legacy mode (backwards compatible): direct trigger fields
       - Automatically wrapped in a single group
       - `TriggerSpec(patterns=..., tool_result=...)` becomes single-group spec
    """

    # Legacy fields (for backwards compatibility)
    patterns: dict[str, frozenset[str]] = Field(default_factory=dict)
    tool_result: ToolResultTrigger = Field(default_factory=ToolResultTrigger)
    todo_state: TodoStateTrigger = Field(default_factory=TodoStateTrigger)
    skill_invoked: SkillInvokedTrigger = Field(default_factory=SkillInvokedTrigger)
    output_missing: OutputMissingTrigger = Field(default_factory=OutputMissingTrigger)
    files_changed: FilesChangedTrigger = Field(default_factory=FilesChangedTrigger)
    state_exists: StateExistsTrigger = Field(default_factory=StateExistsTrigger)

    # Explicit groups (for AND/OR logic)
    groups: tuple[TriggerGroup, ...] = Field(default=())

    def __post_init__(self) -> None:
        """Ensure backwards compatibility by creating implicit group from legacy fields."""
        if not self.groups:
            default_groups = _make_default_groups(
                self.patterns,
                self.tool_result,
                self.todo_state,
                self.skill_invoked,
                self.output_missing,
                self.files_changed,
                self.state_exists,
            )
            if default_groups:
                object.__setattr__(self, "groups", default_groups)


@dataclass(frozen=True, kw_only=True)
class SuggestSkillAction:
    """Action to suggest invoking a skill."""

    type: Literal["suggest_skill"] = "suggest_skill"
    skill: str = Field(min_length=1)
    reason: str = ""


@dataclass(frozen=True, kw_only=True)
class RemindAction:
    """Action to show a gentle reminder."""

    type: Literal["remind"] = "remind"
    message: str = Field(min_length=1)


@dataclass(frozen=True, kw_only=True)
class BlockAction:
    """Action to block completion with error."""

    type: Literal["block"] = "block"
    reason: str = Field(min_length=1)


@dataclass(frozen=True, kw_only=True)
class InjectContextAction:
    """Action to inject context into prompt."""

    type: Literal["inject_context"] = "inject_context"
    context: str = Field(min_length=1)


@dataclass(frozen=True, kw_only=True)
class SetStateAction:
    """Action to set a state value.

    Sets state key from a captured value (e.g., "captured.spec_id").
    Fails if key already exists (requires explicit clear first).
    """

    type: Literal["set_state"] = "set_state"
    key: str = Field(min_length=1)
    value_from: str = Field(min_length=1)


@dataclass(frozen=True, kw_only=True)
class ClearStateAction:
    """Action to clear a state key."""

    type: Literal["clear_state"] = "clear_state"
    key: str = Field(min_length=1)


Action = Annotated[
    SuggestSkillAction
    | RemindAction
    | BlockAction
    | InjectContextAction
    | SetStateAction
    | ClearStateAction,
    Field(discriminator="type"),
]


@dataclass(frozen=True, kw_only=True)
class Rule:
    """Complete configuration for a dispatch rule.

    Rules are organized by hook event, allowing the same action
    to be triggered by different hooks with different criteria.
    """

    name: str = Field(min_length=1)
    priority: Priority = "medium"
    action: Action
    triggers: dict[HookEvent, TriggerSpec] = Field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class Match:
    """Result of matching analysis indicating which rule matched and why."""

    rule_name: str
    priority: Priority
    action: Action
    matched_patterns: frozenset[str]
    captures: dict[str, str] = Field(default_factory=dict)


RuleSet = dict[str, Rule]
