---
issue_type: Feature
created: 2025-12-12
status: Active
claude_plan: /Users/srnnkls/.claude/plans/eager-brewing-lagoon.md
---

# Hook Dispatch Migration

Migrate declarative hook activation system from `resources/.claude/hooks/dispatch/` to `src/dignity/hooks/dispatch/` with refactoring to follow Python guidelines.

## Context

### Current State
- Dispatch system exists in `resources/.claude/hooks/dispatch/` as standalone module
- Uses relative imports (`from dispatch.xxx`)
- Hardcoded rules.json path relative to module
- Working system with comprehensive tests

### Target State
- Integrated into dignity package at `src/dignity/hooks/dispatch/`
- Absolute imports using `dignity.hooks.dispatch`
- Configurable rules.json loading (project → global fallback, env override)
- CLI entry point `dignity dispatch <hook_event>`
- Refactored to follow Python guidelines from `code-implement` skill

## Approach

### Refactor During Migration

Apply Python guidelines while migrating:

1. **Remove behavioral inheritance** - Already clean (uses frozen dataclasses)
2. **Module functions over @staticmethod** - Check for any static methods
3. **Feature-based organization** - Keep dispatch as cohesive feature module
4. **Explicit kw_only** - Ensure all dataclasses use `kw_only=True`
5. **Protocol usage** - Consider protocols for matcher extensibility
6. **Parse at boundaries** - Pydantic at config loading, plain dataclasses internally

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Minimal public API | Export only `dispatch()` and core types in `__init__.py` |
| Config fallback chain | Project `.claude/rules.json` → Global `~/.claude/hooks/rules.json` → env `DIGNITY_RULES_PATH` |
| Keep resources/ | Source files remain for reference |
| README documentation | Document usage patterns for hook integration |

## Success Criteria

- [ ] All tests pass after migration
- [ ] `dignity dispatch UserPromptSubmit` works from CLI
- [ ] Rules.json loads from configurable paths
- [ ] pyright passes with no errors
- [ ] Code follows Python guidelines (no @staticmethod, proper kw_only, etc.)
