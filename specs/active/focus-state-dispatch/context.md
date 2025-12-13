# Context: Focus State Dispatch

## Native Plan

**Source:** `/Users/srnnkls/.claude/plans/starry-puzzling-meerkat.md`

Original design covered:
- Goal: State management for focus tracking
- Approach: File-based state, new trigger/action types
- Resolved: AND trigger logic (trigger groups), regex capture extraction

## Key Files

### Core Implementation

- **`src/dignity/hooks/dispatch/types.py`** (lines 1-175)
  Domain types for dispatch. Add StateExistsTrigger, SetStateAction, ClearStateAction.
  Invariant: All types frozen with `kw_only=True`.

- **`src/dignity/hooks/dispatch/matchers.py`** (lines 1-237)
  Pattern matching functions. Add `match_state_exists_trigger()`.
  Uses registry pattern for field matchers.

- **`src/dignity/hooks/dispatch/dispatcher.py`** (lines 1-166)
  Main dispatch logic. Wire up state trigger matching and action execution.
  Entry point: `dispatch(hook_event, data)`.

- **`src/dignity/hooks/dispatch/config.py`** (lines 1-~180)
  Rule loading from JSON. Update schema for trigger groups.

### New Files

- **`src/dignity/state.py`** (new)
  State backend: `get`, `set`, `clear`, `exists`.
  Location: `~/.claude/state/{session_id}-{key}`.

### Tests

- **`tests/hooks/dispatch/test_types.py`**
- **`tests/hooks/dispatch/test_matchers.py`**
- **`tests/test_state.py`** (new)

## Key Types

| Type | Purpose | Location |
|------|---------|----------|
| `TriggerSpec` | Defines what triggers a rule | types.py:95 |
| `Action` | Union of action types | types.py:144 |
| `Match` | Result of rule matching | types.py:165 |
| `StateExistsTrigger` | Trigger on state key presence | types.py (new) |
| `SetStateAction` | Set state from captured value | types.py (new) |
| `ClearStateAction` | Clear state key | types.py (new) |

## Implementation Decisions Log

### 2025-12-13 - Trigger Groups for AND Logic

**Context:** Need AND semantics (TodoWrite AND file edit) for focus-set rule.

**Decision:** TriggerSpec has list of trigger groups. Each group is ANDed, groups are ORed.

**Alternatives:**
- Flat `trigger_mode` field: Less flexible, can't mix AND/OR
- Composite trigger type: Over-engineered

**Impact:** Backwards compatible - existing rules become single-group.

### 2025-12-13 - State File Scoping

**Context:** Need to prevent conflicts between concurrent sessions.

**Decision:** Follow todos pattern: `~/.claude/state/{session_id}-{key}`.

**Alternatives:**
- Subdirectories: More complex
- Single global state: Conflicts between sessions

**Impact:** Each session has isolated state.

### 2025-12-13 - Focus Requires Clear

**Context:** What happens when setting focus while one exists?

**Decision:** Require explicit clear before set. Prevents silent context switches.

**Alternatives:**
- Silent overwrite: User might not notice switch
- Warn and overwrite: Clutters output

**Impact:** SetStateAction fails if key already exists.

## Dependencies

**Internal:**
- `dignity.hooks.dispatch` - existing dispatch system

**External:**
- None (uses stdlib only)

## Open Questions

1. How does hook input provide session ID? Need to verify format.
2. Should state.set() return success/failure or raise?

## Gotchas & Learnings

(To be updated during implementation)
