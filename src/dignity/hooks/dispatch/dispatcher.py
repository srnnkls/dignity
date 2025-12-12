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
    match_output_missing_trigger,
    match_skill_invoked_trigger,
    match_todo_state_trigger,
    match_tool_result_trigger,
    match_trigger,
)
from dignity.hooks.dispatch.types import (
    HookContext,
    HookEvent,
    Match,
    Rule,
    RuleSet,
)

logger = logging.getLogger(__name__)

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _match_rule(
    rule: Rule, hook_event: HookEvent, context: HookContext
) -> Match | None:
    """Match a single rule against context for a hook event."""
    match rule:
        case Rule(name=name, priority=priority, action=action, triggers=triggers):
            trigger = triggers.get(hook_event)
            if not trigger:
                return None

            all_matched: set[str] = set()

            # Match base trigger patterns
            base_matches = match_trigger(trigger, context)
            all_matched.update(base_matches)

            # Match specialized triggers
            if trigger.tool_result.is_active():
                tool_matches = match_tool_result_trigger(trigger.tool_result, context)
                all_matched.update(tool_matches)

            if trigger.todo_state.is_active():
                todo_matches = match_todo_state_trigger(trigger.todo_state, context)
                all_matched.update(todo_matches)

            if trigger.skill_invoked.is_active():
                skill_matches = match_skill_invoked_trigger(
                    trigger.skill_invoked, context
                )
                all_matched.update(skill_matches)

            if trigger.output_missing.is_active():
                output_matches = match_output_missing_trigger(
                    trigger.output_missing, context
                )
                all_matched.update(output_matches)

            if not all_matched:
                return None

            return Match(
                rule_name=name,
                priority=priority,
                action=action,
                matched_patterns=frozenset(all_matched),
            )


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
            output = format_user_prompt_output(matches)
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

    except Exception as e:
        logger.error("Dispatch error for %s: %s", hook_event, e, exc_info=True)
        _output_empty(hook_event)


def _output_empty(hook_event: HookEvent) -> None:
    """Output empty/safe response for hook type."""
    if hook_event == "UserPromptSubmit":
        json.dump({}, sys.stdout)
        sys.stdout.flush()
