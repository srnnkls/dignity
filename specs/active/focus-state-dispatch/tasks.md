# Tasks: Focus State Dispatch

## Phase 1: State Backend

- [x] **Create `src/dignity/state.py`**
  - Files: `src/dignity/state.py`
  - Functions: `get(key) -> str | None`, `set(key, value)`, `clear(key)`, `exists(key) -> bool`
  - Path: `~/.claude/state/{session_id}-{key}`
  - Fail loudly on missing directory or permission errors
  - Completion: Module exists, functions implemented

- [x] **Add state backend tests**
  - Files: `tests/test_state.py`
  - Tests: get/set/clear/exists, missing directory error, permission handling
  - Completion: `pytest tests/test_state.py` passes

## Phase 2: Trigger Groups

- [x] **Add trigger groups to TriggerSpec**
  - Files: `src/dignity/hooks/dispatch/types.py`
  - Change: TriggerSpec gains `groups: list[TriggerGroup]` field
  - TriggerGroup: dataclass wrapping existing trigger fields
  - Backwards compat: Single group if no explicit groups
  - Completion: pyright passes, existing tests pass

- [x] **Update dispatcher for AND/OR matching**
  - Files: `src/dignity/hooks/dispatch/dispatcher.py`
  - Logic: Each group ANDed (all triggers must match), groups ORed
  - Completion: Unit tests for AND/OR semantics pass

- [x] **Update config loading for trigger groups**
  - Files: `src/dignity/hooks/dispatch/config.py`
  - Support both old format (single group) and new (explicit groups)
  - Completion: Config loads both formats correctly

## Phase 3: Regex Capture Groups

- [x] **Extend FilesChangedTrigger for capture groups**
  - Files: `src/dignity/hooks/dispatch/matchers.py`
  - Change: `match_files_changed_trigger` returns `(matches, captures: dict[str, str])`
  - Pattern: `(?P<name>...)` extracts to `captures["name"]`
  - Completion: Unit tests pass

- [x] **Pass captures to action context**
  - Files: `src/dignity/hooks/dispatch/dispatcher.py`
  - Change: Match result includes captured groups
  - Access: `captured.spec_id` in action `value_from`
  - Completion: End-to-end test extracts value

## Phase 4: State Triggers

- [x] **Add StateExistsTrigger type**
  - Files: `src/dignity/hooks/dispatch/types.py`
  - Fields: `key: str`, `is_active()` method
  - Add to TriggerSpec as optional field
  - Completion: pyright passes

- [x] **Add match_state_exists_trigger**
  - Files: `src/dignity/hooks/dispatch/matchers.py`
  - Import: `from dignity import state`
  - Logic: Return `frozenset({key})` if `state.exists(key)`
  - Completion: Unit tests pass

- [x] **Wire state trigger in dispatcher**
  - Files: `src/dignity/hooks/dispatch/dispatcher.py`
  - Add to `_match_rule()` alongside other triggers
  - Completion: Integration test passes

## Phase 5: State Actions

- [x] **Add SetStateAction and ClearStateAction types**
  - Files: `src/dignity/hooks/dispatch/types.py`
  - SetStateAction: `key`, `value_from` (e.g., "captured.spec_id")
  - ClearStateAction: `key`
  - Update Action union
  - Completion: pyright passes

- [x] **Add action execution in dispatcher**
  - Files: `src/dignity/hooks/dispatch/dispatcher.py`
  - New function: `_execute_actions(matches, context)`
  - SetStateAction: Check key doesn't exist, then set
  - ClearStateAction: Clear key
  - Call after formatting output
  - Completion: Unit tests pass

- [x] **Add value extraction for SetStateAction**
  - Files: `src/dignity/hooks/dispatch/dispatcher.py`
  - Parse `value_from`: "captured.spec_id" → `context["captured"]["spec_id"]`
  - Completion: Unit tests pass

## Phase 6: Template Interpolation

- [x] **Add state interpolation to InjectContextAction**
  - Files: `src/dignity/hooks/dispatch/actions.py`
  - Template: `{state.focus}` → current focus value
  - Completion: Unit test passes

## Phase 7: Integration

- [x] **Add focus rules to rules.json**
  - Files: Create example `resources/rules.json` or update docs
  - Rules: focus-set, focus-clear, focus-inject
  - Completion: Rules load and parse correctly

- [x] **End-to-end integration test**
  - Files: `tests/hooks/dispatch/test_focus_integration.py`
  - Test: Set focus via simulated hook → verify state → inject context
  - Completion: Integration test passes

## Quality Assurance

- [x] **Run full test suite**
  - Command: `pytest tests/`
  - Completion: All tests pass

- [x] **Type check**
  - Command: `pyright src/dignity/`
  - Completion: 0 errors

- [x] **Format and lint**
  - Command: `ruff check src/dignity/ && ruff format src/dignity/`
  - Completion: All checks pass
