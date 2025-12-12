"""Declarative hook dispatch system.

Provides rule-based activation for Claude Code hooks with configurable
triggers and actions.

Public API:
- dispatch: Main entry point for hook processing
- HookEvent: Literal type for hook event names
- Action: Union of all action types
- Rule: Complete rule configuration
- Match: Result of rule matching
"""

from dignity.hooks.dispatch.dispatcher import dispatch
from dignity.hooks.dispatch.types import (
    Action,
    HookEvent,
    Match,
    Rule,
)

__all__ = [
    "dispatch",
    "Action",
    "HookEvent",
    "Match",
    "Rule",
]
