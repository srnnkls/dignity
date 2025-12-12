"""Context extractors for hook dispatch system.

Transforms hook-specific stdin JSON into standardized HookContext dicts.
Each extractor handles one hook type and produces normalized context.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dignity.hooks.dispatch.types import HookContext

logger = logging.getLogger(__name__)


def extract_user_prompt_context(data: dict[str, Any]) -> HookContext:
    """Extract context from UserPromptSubmit hook."""
    prompt = data.get("prompt", "")
    return {
        "hook_event": "UserPromptSubmit",
        "prompt": prompt,
        "keywords": prompt,
        "intent_patterns": prompt,
    }


def _extract_file_paths(data: dict[str, Any]) -> list[Path]:
    """Extract file paths from tool results and files array."""
    paths: list[Path] = []

    tool_results = data.get("tool_results", [])
    for result in tool_results:
        if isinstance(result, dict) and "file_path" in result:
            try:
                paths.append(Path(result["file_path"]))
            except Exception as e:
                logger.warning("Failed to parse file_path: %s", e)

    files = data.get("files", [])
    for file_path in files:
        if isinstance(file_path, str):
            try:
                paths.append(Path(file_path))
            except Exception as e:
                logger.warning("Failed to parse file path: %s", e)

    return paths


def _extract_tool_names(data: dict[str, Any]) -> set[str]:
    """Extract tool names from tool results."""
    tool_names: set[str] = set()

    tool_results = data.get("tool_results", [])
    for result in tool_results:
        if isinstance(result, dict):
            tool_name = result.get("tool_name", "")
            if tool_name:
                tool_names.add(tool_name)

    return tool_names


def _extract_todo_state(data: dict[str, Any]) -> dict[str, bool]:
    """Extract todo completion state from TodoWrite results."""
    any_completed = False
    all_completed = False

    tool_results = data.get("tool_results", [])
    for result in tool_results:
        if not isinstance(result, dict):
            continue

        if result.get("tool_name") != "TodoWrite":
            continue

        params = result.get("parameters", {})
        if not isinstance(params, dict):
            continue

        todos = params.get("todos", [])
        if not isinstance(todos, list) or not todos:
            continue

        completed_count = sum(
            1
            for todo in todos
            if isinstance(todo, dict) and todo.get("status") == "completed"
        )

        if completed_count > 0:
            any_completed = True

        if completed_count == len(todos):
            all_completed = True

    return {
        "any_completed": any_completed,
        "all_completed": all_completed,
    }


def _extract_invoked_skills(data: dict[str, Any]) -> set[str]:
    """Extract invoked skill names from Skill tool results."""
    skills: set[str] = set()

    tool_results = data.get("tool_results", [])
    for result in tool_results:
        if not isinstance(result, dict):
            continue

        if result.get("tool_name") != "Skill":
            continue

        params = result.get("parameters", {})
        if not isinstance(params, dict):
            continue

        skill = params.get("skill", "")
        if skill:
            skills.add(skill)

    return skills


def extract_stop_context(data: dict[str, Any]) -> HookContext:
    """Extract context from Stop hook."""
    return {
        "hook_event": "Stop",
        "tool_names": _extract_tool_names(data),
        "file_paths": _extract_file_paths(data),
        "todo_state": _extract_todo_state(data),
        "invoked_skills": _extract_invoked_skills(data),
        "tool_results": data.get("tool_results", []),
    }


def extract_subagent_stop_context(data: dict[str, Any]) -> HookContext:
    """Extract context from SubagentStop hook."""
    description = data.get("description", "")
    agent_type = data.get("agent_type", "")

    return {
        "hook_event": "SubagentStop",
        "description": description,
        "description_patterns": description,
        "agent_type": agent_type,
        "agent_types": agent_type,
        "last_response": data.get("last_response", ""),
    }


EXTRACTORS: dict[str, Callable[[dict[str, Any]], HookContext]] = {
    "UserPromptSubmit": extract_user_prompt_context,
    "Stop": extract_stop_context,
    "SubagentStop": extract_subagent_stop_context,
}


def extract_context(hook_event: str, data: dict[str, Any]) -> HookContext:
    """Main entry point for context extraction."""
    extractor = EXTRACTORS.get(hook_event)
    if extractor:
        return extractor(data)
    logger.warning("Unknown hook event: %s", hook_event)
    return {"hook_event": hook_event}
