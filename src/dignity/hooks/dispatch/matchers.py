"""Pattern matching functions and matcher registry.

Provides matcher functions for different matching strategies
and a registry for looking up matchers by field name.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from pathlib import Path

from dignity.hooks.dispatch.types import (
    FilesChangedTrigger,
    HookContext,
    OutputMissingTrigger,
    SkillInvokedTrigger,
    StateExistsTrigger,
    TodoStateTrigger,
    ToolResultTrigger,
    TriggerGroup,
    TriggerSpec,
)

logger = logging.getLogger(__name__)

Matcher = Callable[[str, frozenset[str]], frozenset[str]]


def match_word_boundaries(value: str, patterns: frozenset[str]) -> frozenset[str]:
    """Match patterns as whole words (case-insensitive)."""
    if not value or not patterns:
        return frozenset()

    value_lower = value.lower()
    matched = set()

    for keyword in patterns:
        pattern = rf"\b{re.escape(keyword.lower())}\b"
        if re.search(pattern, value_lower):
            matched.add(keyword)

    return frozenset(matched)


def match_regex(value: str, patterns: frozenset[str]) -> frozenset[str]:
    """Match regex patterns (case-insensitive)."""
    if not value or not patterns:
        return frozenset()

    matched = set()

    for pattern in patterns:
        try:
            if re.search(pattern, value, re.IGNORECASE):
                matched.add(pattern)
        except re.error:
            continue

    return frozenset(matched)


def match_exact(value: str, patterns: frozenset[str]) -> frozenset[str]:
    """Match exact string (case-insensitive)."""
    if not value or not patterns:
        return frozenset()

    value_lower = value.lower()
    return frozenset(p for p in patterns if p.lower() == value_lower)


def match_substring(value: str, patterns: frozenset[str]) -> frozenset[str]:
    """Match substring (case-insensitive)."""
    if not value or not patterns:
        return frozenset()

    value_lower = value.lower()
    return frozenset(p for p in patterns if p.lower() in value_lower)


FIELD_MATCHERS: dict[str, Matcher] = {
    "keywords": match_word_boundaries,
    "intent_patterns": match_regex,
    "prompt": match_word_boundaries,
    "description_patterns": match_regex,
    "agent_types": match_exact,
    "subagent_type": match_exact,
    "output_patterns": match_regex,
    "content_patterns": match_regex,
    "path_patterns": match_regex,
}


def match_tool_result_trigger(
    trigger: ToolResultTrigger, context: HookContext
) -> frozenset[str]:
    """Match tool execution results.

    tool_name is required. parameter_patterns is optional refinement.
    """
    if not trigger.tool_name:
        return frozenset()

    tool_results = context.get("tool_results", [])
    matched = set()

    for result in tool_results:
        if not isinstance(result, dict):
            continue

        result_tool = result.get("tool_name", "")
        if result_tool not in trigger.tool_name:
            continue

        if not trigger.parameter_patterns:
            matched.add(result_tool)
        else:
            params = result.get("parameters", {})
            param_matched = set()
            for param_name, patterns in trigger.parameter_patterns.items():
                param_value = params.get(param_name, "")
                if param_value:
                    param_matched.update(match_regex(str(param_value), patterns))

            if param_matched:
                matched.add(result_tool)
                matched.update(param_matched)

    return frozenset(matched)


def match_todo_state_trigger(
    trigger: TodoStateTrigger, context: HookContext
) -> frozenset[str]:
    """Match todo completion state."""
    matched = set()
    todo_state = context.get("todo_state", {})

    if trigger.any_completed and todo_state.get("any_completed"):
        matched.add("any_completed")

    if trigger.all_completed and todo_state.get("all_completed"):
        matched.add("all_completed")

    return frozenset(matched)


def match_skill_invoked_trigger(
    trigger: SkillInvokedTrigger, context: HookContext
) -> frozenset[str]:
    """Match skill invocation."""
    invoked_skills = context.get("invoked_skills", set())

    if trigger.skill in invoked_skills:
        return frozenset({trigger.skill})

    return frozenset()


def match_output_missing_trigger(
    trigger: OutputMissingTrigger, context: HookContext
) -> frozenset[str]:
    """Match when required patterns are missing from output.

    Fires when ALL required patterns are absent (inverted logic for validation).
    """
    if not trigger.required_patterns:
        return frozenset()

    last_response = context.get("last_response", "")

    missing = set()
    for pattern in trigger.required_patterns:
        if pattern not in last_response:
            missing.add(pattern)

    if missing == trigger.required_patterns:
        return frozenset(missing)

    return frozenset()


def match_state_exists_trigger(
    trigger: StateExistsTrigger, context: HookContext
) -> frozenset[str]:
    """Match when a state key exists.

    Checks if the specified state key has a value set.
    Requires session_id in context.
    """
    if not trigger.key:
        return frozenset()

    session_id = context.get("session_id", "")
    if not session_id:
        return frozenset()

    from dignity import state

    if state.exists(session_id, trigger.key):
        return frozenset({trigger.key})

    return frozenset()


def match_patterns(
    patterns: dict[str, frozenset[str]], context: HookContext
) -> frozenset[str]:
    """Match pattern dictionary against hook context.

    Uses OR semantics: returns all matched patterns from any field.
    Only handles text-based fields; use specialized triggers for tools.
    """
    all_matched: set[str] = set()

    for field_name, field_patterns in patterns.items():
        if not field_patterns:
            continue

        matcher = FIELD_MATCHERS.get(field_name)
        if matcher is None:
            logger.warning("Unknown field '%s' in trigger, skipping", field_name)
            continue

        value = context.get(field_name, "")
        if not value:
            continue

        all_matched.update(matcher(str(value), field_patterns))

    return frozenset(all_matched)


def match_trigger(trigger: TriggerSpec, context: HookContext) -> frozenset[str]:
    """Match trigger patterns against hook context.

    Uses OR semantics: returns all matched patterns from any field.
    Only handles text-based fields; use specialized triggers for tools.

    DEPRECATED: Use match_trigger_group for AND/OR group semantics.
    """
    return match_patterns(trigger.patterns, context)


def match_trigger_group(
    group: TriggerGroup, context: HookContext
) -> tuple[frozenset[str], dict[str, str]] | None:
    """Match a trigger group with AND semantics.

    All active triggers in the group must match for the group to match.
    Returns (matched_patterns, captures) if ALL active triggers match, None otherwise.
    """
    all_matched: set[str] = set()
    all_captures: dict[str, str] = {}
    active_count = 0
    matched_count = 0

    # Check base patterns
    if group.patterns:
        active_count += 1
        matches = match_patterns(group.patterns, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)

    # Check specialized triggers
    if group.tool_result.is_active():
        active_count += 1
        matches = match_tool_result_trigger(group.tool_result, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)

    if group.todo_state.is_active():
        active_count += 1
        matches = match_todo_state_trigger(group.todo_state, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)

    if group.skill_invoked.is_active():
        active_count += 1
        matches = match_skill_invoked_trigger(group.skill_invoked, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)

    if group.output_missing.is_active():
        active_count += 1
        matches = match_output_missing_trigger(group.output_missing, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)

    if group.files_changed.is_active():
        active_count += 1
        matches, captures = match_files_changed_trigger(group.files_changed, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)
            all_captures.update(captures)

    if group.state_exists.is_active():
        active_count += 1
        matches = match_state_exists_trigger(group.state_exists, context)
        if matches:
            matched_count += 1
            all_matched.update(matches)

    # No active triggers means no match
    if active_count == 0:
        return None

    # AND semantics: all active triggers must match
    if matched_count == active_count:
        return frozenset(all_matched), all_captures

    return None


def match_file_paths(path: Path, patterns: frozenset[str]) -> bool:
    """Match file path against glob patterns."""
    if not patterns:
        return False

    for pattern in patterns:
        try:
            if path.match(pattern):
                return True
        except Exception:
            continue

    return False


def match_files_changed_trigger(
    trigger: FilesChangedTrigger, context: HookContext
) -> tuple[frozenset[str], dict[str, str]]:
    """Match files changed trigger with capture group support.

    Returns:
        Tuple of (matched patterns, captures dict).
        Captures are extracted from named groups in path patterns.
    """
    if not trigger.is_active():
        return frozenset(), {}

    changed_files = context.get("changed_files", [])
    if not changed_files:
        return frozenset(), {}

    matched: set[str] = set()
    captures: dict[str, str] = {}

    for file_path in changed_files:
        path_str = str(file_path) if isinstance(file_path, Path) else file_path

        # Match path patterns with capture groups
        for pattern in trigger.path_patterns:
            try:
                match = re.search(pattern, path_str)
                if match:
                    matched.add(pattern)
                    # Extract named capture groups
                    captures.update(match.groupdict())
            except re.error:
                # Fall back to glob-style matching
                if Path(path_str).match(pattern):
                    matched.add(pattern)

    # If path matched and content patterns exist, check content
    if matched and trigger.content_patterns:
        content_matched = False
        for file_path in changed_files:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            content_matches = match_file_content(path, trigger.content_patterns)
            if content_matches:
                matched.update(content_matches)
                content_matched = True
        # If no content matched, clear all matches
        if not content_matched:
            matched.clear()
            captures.clear()

    return frozenset(matched), captures


def match_file_content(
    path: Path,
    patterns: frozenset[str],
    *,
    max_bytes: int = 10_000,
) -> frozenset[str]:
    """Match regex patterns in file content."""
    if not patterns or not path.exists() or not path.is_file():
        return frozenset()

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
        return match_regex(content, patterns)
    except Exception:
        return frozenset()
