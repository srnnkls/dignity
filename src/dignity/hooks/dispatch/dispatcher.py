"""Unified dispatcher for all hook events.

Single entry point that:
1. Extracts context from hook input
2. Matches against rules
3. Executes appropriate actions
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

from dignity.hooks.dispatch.actions import (
    format_stop_output,
    format_subagent_stop_output,
    format_user_prompt_output,
)
from dignity.hooks.dispatch.config import load_rules
from dignity.hooks.dispatch.extractors import extract_context
from dignity.hooks.dispatch.matchers import (
    match_trigger_group,
)
from dignity.hooks.dispatch.types import (
    ClearStateAction,
    HookContext,
    HookEvent,
    Match,
    Rule,
    RuleSet,
    SetStateAction,
)

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _extract_value(value_from: str, captures: dict[str, str]) -> str | None:
    """Extract value from captures using a path expression.

    Supports "captured.{key}" format.
    """
    if value_from.startswith("captured."):
        key = value_from[9:]  # len("captured.") == 9
        return captures.get(key)
    return None


def _execute_actions(matches: list[Match], context: HookContext) -> None:
    """Execute state actions from matches.

    Processes SetStateAction and ClearStateAction.
    """
    from dignity import state

    session_id = context.get("session_id", "")
    if not session_id:
        logger.warning("No session_id in context, skipping state actions")
        return

    for match in matches:
        match match.action:
            case SetStateAction(key=key, value_from=value_from):
                if state.exists(session_id, key):
                    logger.warning(
                        "State key '%s' already exists, skipping set (use clear first)",
                        key,
                    )
                    continue

                value = _extract_value(value_from, match.captures)
                if value is None:
                    logger.warning(
                        "Could not extract value from '%s' for key '%s'",
                        value_from,
                        key,
                    )
                    continue

                state.set(session_id, key, value)
                logger.debug("Set state '%s' = '%s'", key, value)

            case ClearStateAction(key=key):
                state.clear(session_id, key)
                logger.debug("Cleared state '%s'", key)


def _match_rule(
    rule: Rule, hook_event: HookEvent, context: HookContext
) -> Match | None:
    """Match a single rule against context for a hook event.

    Uses trigger group semantics:
    - Within each group: AND (all active triggers must match)
    - Across groups: OR (any group matching triggers the rule)
    """
    match rule:
        case Rule(name=name, priority=priority, action=action, triggers=triggers):
            trigger_spec = triggers.get(hook_event)
            if not trigger_spec:
                return None

            # No groups means no match
            if not trigger_spec.groups:
                return None

            # OR across groups: try each group, return on first match
            for group in trigger_spec.groups:
                group_result = match_trigger_group(group, context)
                if group_result is not None:
                    matched_patterns, captures = group_result
                    return Match(
                        rule_name=name,
                        priority=priority,
                        action=action,
                        matched_patterns=matched_patterns,
                        captures=captures,
                    )

            return None


def analyze_hook(
    hook_event: HookEvent,
    context: HookContext,
    rules: RuleSet,
) -> list[Match]:
    """Analyze hook context and return matching rules.

    Main entry point for rule matching.
    """
    if not context or not rules:
        return []

    matches: list[Match] = []
    errors: list[str] = []

    for rule_name, rule in rules.items():
        try:
            match = _match_rule(rule, hook_event, context)
            if match:
                matches.append(match)
        except Exception as e:
            errors.append(f"Rule '{rule_name}': {e}")
            logger.warning("Error matching rule %s: %s", rule_name, e)

    if errors:
        logger.info("Aggregated %d rule matching errors", len(errors))

    return sorted(matches, key=lambda m: PRIORITY_ORDER[m.priority])


def dispatch(hook_event: HookEvent, data: dict[str, Any]) -> None:
    """Main dispatcher entry point.

    Args:
        hook_event: The hook event type.
        data: Raw JSON data from stdin.
    """
    try:
        context = extract_context(hook_event, data)
        logger.debug("Extracted context for %s", hook_event)

        rules = load_rules()
        matches = analyze_hook(hook_event, context, rules)
        logger.debug("Found %d matches for %s", len(matches), hook_event)

        if not matches:
            _output_empty(hook_event)
            return

        if hook_event == "UserPromptSubmit":
            output = format_user_prompt_output(matches, context)
            json.dump(output, sys.stdout)

        elif hook_event == "Stop":
            output = format_stop_output(matches)
            if output:
                print(output, file=sys.stdout)

        elif hook_event == "SubagentStop":
            output = format_subagent_stop_output(matches)
            if output:
                print(json.dumps(output))

        sys.stdout.flush()
        _execute_actions(matches, context)

    except Exception as e:
        logger.error("Dispatch error for %s: %s", hook_event, e, exc_info=True)
        _output_empty(hook_event)


def _output_empty(hook_event: HookEvent) -> None:
    """Output empty/safe response for hook type."""
    if hook_event == "UserPromptSubmit":
        json.dump({}, sys.stdout)
        sys.stdout.flush()
