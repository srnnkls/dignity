"""Action handlers for different action types.

Pure functions that format actions into appropriate output for each hook type.
"""

from __future__ import annotations

import re
from typing import Sequence

from dignity.hooks.dispatch.types import (
    BlockAction,
    HookContext,
    InjectContextAction,
    Match,
    SuggestSkillAction,
)


def _interpolate_state(template: str, context: HookContext) -> str:
    """Interpolate {state.key} placeholders with actual state values."""
    session_id = context.get("session_id", "")
    if not session_id:
        return template

    from dignity import state

    def replace_state(match: re.Match[str]) -> str:
        key = match.group(1)
        value = state.get(session_id, key)
        return value if value is not None else match.group(0)

    return re.sub(r"\{state\.([^}]+)\}", replace_state, template)


def format_skill_suggestions(matches: Sequence[Match]) -> str:
    """Format skill suggestions for prompt injection."""
    high: list[tuple[str, str]] = []
    medium: list[tuple[str, str]] = []
    low: list[tuple[str, str]] = []

    for m in matches:
        match (m.action, m.priority):
            case (SuggestSkillAction(skill=skill, reason=reason), "high"):
                high.append((skill, reason))
            case (SuggestSkillAction(skill=skill, reason=reason), "medium"):
                medium.append((skill, reason))
            case (SuggestSkillAction(skill=skill, reason=reason), "low"):
                low.append((skill, reason))

    if not (high or medium or low):
        return ""

    lines = ["SKILL ACTIVATION SUGGESTION", ""]

    if high:
        lines.append("HIGH PRIORITY:")
        for skill, reason in high:
            lines.append(f"  - {skill}")
            if reason:
                lines.append(f"    Reason: {reason}")

    if medium:
        if high:
            lines.append("")
        lines.append("MEDIUM PRIORITY:")
        for skill, reason in medium:
            lines.append(f"  - {skill}")
            if reason:
                lines.append(f"    Reason: {reason}")

    if low:
        if high or medium:
            lines.append("")
        lines.append("LOW PRIORITY:")
        for skill, _ in low:
            lines.append(f"  - {skill}")

    lines.append("")
    lines.append("Consider invoking relevant skills with the Skill tool.")

    return "\n".join(lines)


def format_reminder(matches: Sequence[Match]) -> str:
    """Format matches as gentle reminder (stdout for Stop hook)."""
    high: list[tuple[str, str]] = []
    others: list[tuple[str, str]] = []

    for m in matches:
        match (m.action, m.priority):
            case (SuggestSkillAction(skill=skill, reason=reason), "high"):
                high.append((skill, reason))
            case (SuggestSkillAction(skill=skill, reason=reason), _):
                others.append((skill, reason))

    if not (high or others):
        return ""

    lines = ["Skill Reminder", ""]
    lines.append("Consider:")

    if high:
        for skill, reason in high:
            display_reason = reason or f"Use {skill}"
            lines.append(f"  - {skill}: {display_reason}")
    else:
        for skill, _ in others[:2]:
            lines.append(f"  - {skill}")

    return "\n".join(lines)


def format_user_prompt_output(
    matches: Sequence[Match], context: HookContext | None = None
) -> dict:
    """Format output for UserPromptSubmit hook."""
    if not matches:
        return {}

    context_parts: list[str] = []

    skill_text = format_skill_suggestions(matches)
    if skill_text:
        context_parts.append(skill_text)

    for m in matches:
        match m.action:
            case InjectContextAction(context=str() as inject_prompt):
                if context:
                    inject_prompt = _interpolate_state(inject_prompt, context)
                context_parts.append(inject_prompt)

    if not context_parts:
        return {}

    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n\n".join(context_parts),
        }
    }


def format_stop_output(matches: Sequence[Match]) -> str:
    """Format output for Stop hook (stdout reminder)."""
    return format_reminder(matches)


def format_subagent_stop_output(matches: Sequence[Match]) -> dict | None:
    """Format output for SubagentStop hook.

    Returns:
        - dict with "decision": "block" for BlockAction
        - dict with hookSpecificOutput for other actions
        - None if no output needed
    """
    for m in matches:
        match m.action:
            case BlockAction(reason=reason):
                return {
                    "decision": "block",
                    "reason": reason,
                }

    skill_text = format_skill_suggestions(matches)
    if skill_text:
        return {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStop",
                "additionalContext": skill_text,
            }
        }

    return None
