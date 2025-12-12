"""Configuration loading for dispatch system.

Loads rules from rules.json with configurable path resolution:
1. DIGNITY_RULES_PATH environment variable (if set)
2. Project .claude/rules.json (if exists)
3. Global ~/.claude/hooks/rules.json (fallback)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from dignity.hooks.dispatch.types import (
    Action,
    FilesChangedTrigger,
    HookEvent,
    OutputMissingTrigger,
    Rule,
    RuleSet,
    SkillInvokedTrigger,
    TodoStateTrigger,
    ToolResultTrigger,
    TriggerSpec,
)

logger = logging.getLogger(__name__)

# Default paths for rules.json
PROJECT_RULES_PATH = Path(".claude/rules.json")
GLOBAL_RULES_PATH = Path.home() / ".claude" / "hooks" / "rules.json"
ENV_VAR_NAME = "DIGNITY_RULES_PATH"


def _find_rules_path() -> Path | None:
    """Find rules.json using path resolution chain.

    Resolution order:
    1. DIGNITY_RULES_PATH environment variable
    2. Project .claude/rules.json
    3. Global ~/.claude/hooks/rules.json
    """
    # Check environment variable first
    env_path = os.environ.get(ENV_VAR_NAME)
    if env_path:
        path = Path(env_path)
        if path.exists():
            logger.debug("Using rules from env var: %s", path)
            return path
        logger.warning("DIGNITY_RULES_PATH set but file not found: %s", env_path)

    # Check project-local path
    if PROJECT_RULES_PATH.exists():
        logger.debug("Using project rules: %s", PROJECT_RULES_PATH)
        return PROJECT_RULES_PATH

    # Fall back to global path
    if GLOBAL_RULES_PATH.exists():
        logger.debug("Using global rules: %s", GLOBAL_RULES_PATH)
        return GLOBAL_RULES_PATH

    logger.debug("No rules.json found in any location")
    return None


def configure_logging() -> None:
    """Configure logging from environment."""
    level_name = os.environ.get("DISPATCH_LOG_LEVEL", "ERROR")
    level = getattr(logging, level_name.upper(), logging.ERROR)

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(name)s: %(message)s",
        stream=sys.stderr,
    )


_action_adapter: TypeAdapter[Action] = TypeAdapter(Action)


def _parse_action(action_data: dict[str, Any]) -> Action:
    """Parse action from JSON data using discriminated union."""
    if "type" not in action_data:
        action_data = {**action_data, "type": "suggest_skill"}
    return _action_adapter.validate_python(action_data)


def _parse_trigger(trigger_data: dict[str, Any]) -> TriggerSpec:
    """Parse trigger spec from JSON data."""
    patterns: dict[str, frozenset[str]] = {}

    # Extract pattern fields
    for field in ["keywords", "intent_patterns", "description_patterns", "agent_types"]:
        if field in trigger_data:
            value = trigger_data[field]
            if isinstance(value, list):
                patterns[field] = frozenset(value)
            elif isinstance(value, str):
                patterns[field] = frozenset([value])

    # Parse specialized triggers
    tool_result = ToolResultTrigger()
    if "tool_result" in trigger_data:
        tr_data = trigger_data["tool_result"]
        tool_name = tr_data.get("tool_name", [])
        if isinstance(tool_name, str):
            tool_name = [tool_name]
        tool_result = ToolResultTrigger(
            tool_name=frozenset(tool_name),
            parameter_patterns={
                k: frozenset(v) if isinstance(v, list) else frozenset([v])
                for k, v in tr_data.get("parameter_patterns", {}).items()
            },
        )

    todo_state = TodoStateTrigger()
    if "todo_state" in trigger_data:
        ts_data = trigger_data["todo_state"]
        todo_state = TodoStateTrigger(
            any_completed=ts_data.get("any_completed", False),
            all_completed=ts_data.get("all_completed", False),
        )

    skill_invoked = SkillInvokedTrigger()
    if "skill_invoked" in trigger_data:
        si_data = trigger_data["skill_invoked"]
        skill_invoked = SkillInvokedTrigger(skill=si_data.get("skill", ""))

    output_missing = OutputMissingTrigger()
    if "output_missing" in trigger_data:
        om_data = trigger_data["output_missing"]
        required = om_data.get("required_patterns", [])
        if isinstance(required, str):
            required = [required]
        output_missing = OutputMissingTrigger(required_patterns=frozenset(required))

    files_changed = FilesChangedTrigger()
    if "files_changed" in trigger_data:
        fc_data = trigger_data["files_changed"]
        path_patterns = fc_data.get("path_patterns", [])
        content_patterns = fc_data.get("content_patterns", [])
        if isinstance(path_patterns, str):
            path_patterns = [path_patterns]
        if isinstance(content_patterns, str):
            content_patterns = [content_patterns]
        files_changed = FilesChangedTrigger(
            path_patterns=frozenset(path_patterns),
            content_patterns=frozenset(content_patterns),
        )

    return TriggerSpec(
        patterns=patterns,
        tool_result=tool_result,
        todo_state=todo_state,
        skill_invoked=skill_invoked,
        output_missing=output_missing,
        files_changed=files_changed,
    )


def _parse_rule(name: str, rule_data: dict[str, Any]) -> Rule:
    """Parse a single rule from JSON data."""
    action = _parse_action(rule_data.get("action", {}))

    triggers: dict[HookEvent, TriggerSpec] = {}
    for hook_event, trigger_data in rule_data.get("triggers", {}).items():
        if hook_event in ("UserPromptSubmit", "Stop", "SubagentStop"):
            triggers[hook_event] = _parse_trigger(trigger_data)

    return Rule(
        name=name,
        priority=rule_data.get("priority", "medium"),
        action=action,
        triggers=triggers,
    )


@lru_cache(maxsize=1)
def load_rules() -> RuleSet:
    """Load rules from rules.json.

    Uses path resolution chain to find rules file.
    Caches the result for performance.
    """
    rules_path = _find_rules_path()
    if rules_path is None:
        logger.warning("No rules.json found")
        return {}

    try:
        with open(rules_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse rules.json: %s", e)
        return {}

    rules_data = data.get("rules", {})
    rules: RuleSet = {}

    for name, rule_data in rules_data.items():
        try:
            rules[name] = _parse_rule(name, rule_data)
        except Exception as e:
            logger.error("Failed to parse rule %s: %s", name, e)

    logger.debug("Loaded %d rules from %s", len(rules), rules_path)
    return rules


def clear_rules_cache() -> None:
    """Clear the rules cache (useful for testing)."""
    load_rules.cache_clear()
