# Context: Hook Dispatch Migration

Implementation context and key files for the migration.

---

## Native Plan

**Source:** `/Users/srnnkls/.claude/plans/eager-brewing-lagoon.md`

Summary of the original design:
- Goal: Migrate dispatch system to dignity package
- Approach: Direct migration with refactoring
- Clarifications: External config, project→global fallback, env override, minimal API

---

## Key Files

### Source (resources/.claude/hooks/dispatch/)

| File | Purpose | Lines |
|------|---------|-------|
| `types.py` | Domain types - Actions, Triggers, Rules, Match | 252 |
| `dispatcher.py` | Main entry point - routing, matching, actions | 162 |
| `config.py` | Configuration loading from rules.json | 195 |
| `matchers.py` | Pattern matching functions | 244 |
| `extractors.py` | Context extractors per hook type | 168 |
| `actions.py` | Action formatters for hook outputs | 154 |
| `test_matchers.py` | Matcher tests | 547 |
| `test_types.py` | Type tests | 224 |

### Target (src/dignity/hooks/dispatch/)

```
src/dignity/
├── __init__.py          # Add dispatch CLI command
├── hooks/
│   ├── __init__.py      # Package marker
│   └── dispatch/
│       ├── __init__.py  # Public API: dispatch(), core types
│       ├── types.py
│       ├── dispatcher.py
│       ├── config.py
│       ├── matchers.py
│       ├── extractors.py
│       └── actions.py
tests/
└── hooks/
    └── dispatch/
        ├── test_matchers.py
        └── test_types.py
```

---

## Key Types

### Domain Types (types.py)

| Type | Purpose |
|------|---------|
| `Priority` | Literal["high", "medium", "low"] |
| `HookEvent` | Literal["UserPromptSubmit", "Stop", "SubagentStop"] |
| `Action` | Union of SuggestSkillAction, RemindAction, BlockAction, InjectContextAction |
| `TriggerSpec` | Generic trigger with pattern dict + specialized triggers |
| `Rule` | Complete rule config (name, priority, action, triggers) |
| `Match` | Result of matching (rule_name, priority, action, matched_patterns) |

### Specialized Triggers

| Trigger | Purpose |
|---------|---------|
| `ToolResultTrigger` | Match tool execution results |
| `TodoStateTrigger` | Match todo completion state |
| `SkillInvokedTrigger` | Match skill invocation |
| `OutputMissingTrigger` | Match missing patterns in output |
| `FilesChangedTrigger` | Match file changes |

---

## Implementation Decisions Log

### 2025-12-12 - Config Path Resolution

**Context:** Rules.json needs to be loadable from multiple locations.

**Decision:** Chain: project `.claude/rules.json` → global `~/.claude/hooks/rules.json` → env `DIGNITY_RULES_PATH`

**Rationale:** Allows project-specific overrides while providing sensible defaults.

### 2025-12-12 - Minimal Public API

**Context:** What to export from `dignity.hooks.dispatch`?

**Decision:** Export only `dispatch()` function and core types (Action, Rule, Match, HookEvent).

**Rationale:** Internal implementation details (matchers, extractors) shouldn't be public API. Users only need to call dispatch and possibly inspect results.

---

## Refactoring Notes

### Python Guidelines to Apply

1. **kw_only=True** - Verify all @dataclass and @pydantic_dataclass use this
2. **No @staticmethod** - Check for and convert to module functions
3. **Type hints** - Ensure all function signatures are annotated
4. **from __future__ import annotations** - Present in all files
5. **Protocols** - Consider if Matcher type alias should be a Protocol

### Patterns to Preserve

- Frozen dataclasses for immutability
- Pydantic at boundaries (Rule, TriggerSpec loading)
- Plain dataclasses internally (Match)
- Pattern matching in dispatcher

---

## Dependencies

### Internal
- `dignity.statusline` - Existing statusline module (sibling)
- `dignity.tokens` - Token metrics module (sibling)

### External
- `pydantic>=2.0` - Boundary validation (to add to pyproject.toml)
- `typer>=0.15.1` - CLI framework (existing)

---

## Open Questions

None remaining after validation.

---

## Gotchas & Learnings

(To be updated during implementation)
