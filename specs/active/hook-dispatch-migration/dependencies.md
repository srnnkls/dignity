# Task Dependencies

## Overview

Task dependency graph for parallel dispatch. Tasks marked `[P]` can run in parallel if they modify different files.

## Dependency Graph

```
Phase 1: [Setup]
    T001 (structure) → T002 (pydantic) → T003 (test dirs)
                              │
                              ▼
Phase 2: [Core Types]
    T004 (types.py) → T005 (test_types.py)
                              │
                              ▼
Phase 3: [Matchers]
    T006 (matchers.py) → T007 (test_matchers.py)
                              │
                              ▼
Phase 4: [Supporting]
    T008 ─┬─ [P] (extractors.py)
    T009 ─┘     (actions.py)
                              │
                              ▼
Phase 5: [Config]
    T010 (config.py with path resolution)
                              │
                              ▼
Phase 6: [Dispatcher]
    T011 (dispatcher.py) → T012 (__init__.py exports)
                              │
                              ▼
Phase 7: [CLI]
    T013 (dispatch command)
                              │
                              ▼
Phase 8: [Docs]
    T014 (README.md)
                              │
                              ▼
Phase 9: [QA]
    T015 (tests) → T016 (pyright) → T017 (ruff)
```

## Execution Batches

| Batch | Tasks | Type | Files |
|-------|-------|------|-------|
| 1 | T001, T002, T003 | Sequential | Setup |
| 2 | T004, T005 | Sequential | types.py, test_types.py |
| 3 | T006, T007 | Sequential | matchers.py, test_matchers.py |
| 4 | T008, T009 | Parallel | extractors.py, actions.py |
| 5 | T010 | Sequential | config.py |
| 6 | T011, T012 | Sequential | dispatcher.py, __init__.py |
| 7 | T013 | Sequential | src/dignity/__init__.py |
| 8 | T014 | Sequential | README.md |
| 9 | T015, T016, T017 | Sequential | QA checks |

## Phase Dependencies

- **Phase 1 → Phase 2:** Package structure must exist before adding modules
- **Phase 2 → Phase 3:** Types must exist before matchers (matchers import types)
- **Phase 3 → Phase 4:** Matchers before extractors/actions (extractors use types)
- **Phase 4 → Phase 5:** Supporting modules before config
- **Phase 5 → Phase 6:** Config before dispatcher (dispatcher imports all)
- **Phase 6 → Phase 7:** Public API before CLI integration
- **Phase 7 → Phase 8:** CLI working before documenting
- **Phase 8 → Phase 9:** All code complete before QA

## Parallel Safety Rules

Tasks can run in parallel (`[P]`) when:
- Same phase (shared prerequisites complete)
- Different file paths
- No import dependencies between them

**Parallelizable pairs:**
- T008 + T009: extractors.py and actions.py (both import types, don't depend on each other)

## Notes

- Phases 2-4 could potentially run in parallel but sequential is safer for this migration
- Config refactoring (T010) is a critical path item with new functionality
- QA phase must be strictly sequential (tests → types → lint)
