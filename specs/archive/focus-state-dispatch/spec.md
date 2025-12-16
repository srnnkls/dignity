# Spec: Focus State Dispatch

---
issue_type: Feature
created: 2025-12-13
status: Superseded
archived: 2025-12-16
archived_reason: Hook dispatch system replaced by cupcake
---

## Overview

Add generic state management to the declarative dispatch system, with focus tracking as the first use case. State enables rules to persist and query values across hook invocations.

## Context

**Current state:** The dispatch system supports triggers (ToolResult, TodoState, SkillInvoked, OutputMissing, FilesChanged) and actions (SuggestSkill, Remind, Block, InjectContext). All matching is stateless - rules cannot remember or query values from previous invocations.

**Target state:** Rules can set, clear, and query persistent state. Focus tracking demonstrates this by remembering which spec the user is working on and injecting context about it into prompts.

## Architectural Approach

### State Backend

Simple file-based storage following the todos pattern:
- Location: `~/.claude/state/{session_id}-{key}`
- Operations: `get`, `set`, `clear`, `exists`
- Fail loudly on permission/directory errors
- No locking (session-scoped files)

### Trigger Groups (AND/OR Logic)

TriggerSpec gains a list of trigger groups:
- Each group is a set of triggers that must ALL match (AND)
- Multiple groups are ORed (any group matching triggers the rule)
- Backwards compatible: existing rules work as single-group

### Regex Capture Groups

FilesChangedTrigger path patterns support named capture groups:
- Pattern: `specs/active/(?P<spec_id>[^/]+)/tasks\.md`
- Captured values available to actions via `captured.spec_id`

### New Types

**Triggers:**
- `StateExistsTrigger(key: str)` - fires when state key has a value

**Actions:**
- `SetStateAction(key, value_from)` - set state from captured value
- `ClearStateAction(key)` - remove state key

### Behavior Constraint

Focus requires explicit clear before set - if `focus` state exists, `SetStateAction` for `focus` fails/blocks. This prevents silent context switches.

## Success Criteria

1. State backend passes unit tests (get/set/clear/exists)
2. StateExistsTrigger matches correctly in dispatcher
3. SetStateAction/ClearStateAction execute correctly
4. Trigger groups with AND semantics work
5. Regex capture groups extract values from file paths
6. Focus rules work end-to-end:
   - `focus-set`: TodoWrite + Edit `specs/active/{id}/tasks.md` → sets focus
   - `focus-clear`: spec-archive skill → clears focus
   - `focus-inject`: UserPromptSubmit with focus → injects context

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| State file corruption | Simple text files, easy to debug/recover |
| Session ID unavailable | Hook input provides session context |
| Regex complexity | Use simple named groups, test thoroughly |
