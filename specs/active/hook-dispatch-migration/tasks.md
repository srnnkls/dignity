# Tasks: Hook Dispatch Migration

Granular work checklist for the migration.

---

## Phase 1: Setup

- [x] **Create package structure**
  - Files: `src/dignity/hooks/__init__.py`, `src/dignity/hooks/dispatch/__init__.py`
  - Completion: Directories exist, empty `__init__.py` files created

- [x] **Add pydantic dependency**
  - Files: `pyproject.toml`
  - Completion: `pydantic>=2.0` in dependencies, `uv sync` succeeds

- [x] **Create test directories**
  - Files: `tests/hooks/__init__.py`, `tests/hooks/dispatch/__init__.py`
  - Completion: Test directories exist

---

## Phase 2: Core Types Migration

- [ ] **Migrate types.py**
  - Source: `resources/.claude/hooks/dispatch/types.py`
  - Target: `src/dignity/hooks/dispatch/types.py`
  - Refactor: Verify all dataclasses use `kw_only=True`, check for any @staticmethod
  - Completion: pyright passes, imports work

- [ ] **Migrate test_types.py**
  - Source: `resources/.claude/hooks/dispatch/test_types.py`
  - Target: `tests/hooks/dispatch/test_types.py`
  - Update: Imports to `dignity.hooks.dispatch.types`
  - Completion: `pytest tests/hooks/dispatch/test_types.py` passes

---

## Phase 3: Matchers Migration

- [ ] **Migrate matchers.py**
  - Source: `resources/.claude/hooks/dispatch/matchers.py`
  - Target: `src/dignity/hooks/dispatch/matchers.py`
  - Update: Import from `.types`
  - Refactor: Check for @staticmethod, ensure type hints complete
  - Completion: pyright passes

- [ ] **Migrate test_matchers.py**
  - Source: `resources/.claude/hooks/dispatch/test_matchers.py`
  - Target: `tests/hooks/dispatch/test_matchers.py`
  - Update: Imports to `dignity.hooks.dispatch`
  - Completion: `pytest tests/hooks/dispatch/test_matchers.py` passes

---

## Phase 4: Supporting Modules

- [ ] **Migrate extractors.py**
  - Source: `resources/.claude/hooks/dispatch/extractors.py`
  - Target: `src/dignity/hooks/dispatch/extractors.py`
  - Update: Import from `.types`
  - Completion: pyright passes

- [ ] **Migrate actions.py**
  - Source: `resources/.claude/hooks/dispatch/actions.py`
  - Target: `src/dignity/hooks/dispatch/actions.py`
  - Update: Import from `.types`
  - Completion: pyright passes

---

## Phase 5: Config Migration

- [ ] **Migrate and refactor config.py**
  - Source: `resources/.claude/hooks/dispatch/config.py`
  - Target: `src/dignity/hooks/dispatch/config.py`
  - Refactor:
    - Add path resolution chain (project → global → env)
    - Add `DIGNITY_RULES_PATH` env var support
    - Update `RULES_PATH` logic to search multiple locations
  - Completion: Config loads from correct paths, pyright passes

---

## Phase 6: Dispatcher Integration

- [ ] **Migrate dispatcher.py**
  - Source: `resources/.claude/hooks/dispatch/dispatcher.py`
  - Target: `src/dignity/hooks/dispatch/dispatcher.py`
  - Update: All imports to use `.` relative imports
  - Completion: pyright passes

- [ ] **Create public API in __init__.py**
  - File: `src/dignity/hooks/dispatch/__init__.py`
  - Exports: `dispatch`, `HookEvent`, `Action`, `Rule`, `Match`
  - Completion: `from dignity.hooks.dispatch import dispatch` works

---

## Phase 7: CLI Integration

- [ ] **Add dispatch command to CLI**
  - File: `src/dignity/__init__.py`
  - Add: `@app.command() def dispatch(hook_event: HookEvent)` that reads stdin JSON
  - Completion: `echo '{"prompt":"test"}' | dignity dispatch UserPromptSubmit` works

---

## Phase 8: Documentation

- [ ] **Create README.md**
  - File: `src/dignity/hooks/dispatch/README.md`
  - Content: Usage patterns, shell hook examples, config paths
  - Completion: README exists with usage documentation

---

## Phase 9: Quality Assurance

- [ ] **Run full test suite**
  - Command: `pytest tests/`
  - Completion: All tests pass

- [ ] **Type check**
  - Command: `pyright src/dignity/hooks/`
  - Completion: No errors

- [ ] **Format and lint**
  - Command: `ruff check src/dignity/hooks/ && ruff format src/dignity/hooks/`
  - Completion: No issues

---

## Completion Checklist

- [ ] All source files migrated to `src/dignity/hooks/dispatch/`
- [ ] All tests migrated to `tests/hooks/dispatch/`
- [ ] pyproject.toml updated with pydantic dependency
- [ ] CLI `dignity dispatch` command works
- [ ] Config loads from project → global → env path chain
- [ ] README.md documents usage
- [ ] All tests pass
- [ ] pyright passes
- [ ] ruff passes
