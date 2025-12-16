# Task Dependencies

## Overview

Task dependency graph for parallel dispatch. Tasks marked `[P]` can run in parallel if they modify different files.

## Dependency Graph

```
Phase 1: [State Backend]
    T001 (state.py) → T002 (tests)
               │
               ▼
Phase 2: [Trigger Groups]
    T003 (types) → T004 (dispatcher) → T005 (config)
               │
               ▼
Phase 3: [Regex Captures]
    T006 (matchers) → T007 (dispatcher)
               │
               ▼
Phase 4: [State Triggers]
    T008 ─┬─ [P] (types + matchers can parallel)
    T009 ─┘
          │
          ▼
    T010 (wire dispatcher)
               │
               ▼
Phase 5: [State Actions]
    T011 (types) → T012 (execution) → T013 (extraction)
               │
               ▼
Phase 6: [Template]
    T014 (interpolation)
               │
               ▼
Phase 7: [Integration]
    T015 (rules) ─┬─ [P]
    T016 (e2e)   ─┘
               │
               ▼
Phase 8: [QA]
    T017 (tests) → T018 (types) → T019 (lint)
```

## Execution Batches

| Batch | Tasks | Type | Files |
|-------|-------|------|-------|
| 1 | T001, T002 | Sequential | src/dignity/state.py, tests/test_state.py |
| 2 | T003, T004, T005 | Sequential | types.py → dispatcher.py → config.py |
| 3 | T006, T007 | Sequential | matchers.py → dispatcher.py |
| 4 | T008, T009 | Parallel | types.py, matchers.py (different functions) |
| 5 | T010 | Sequential | dispatcher.py |
| 6 | T011, T012, T013 | Sequential | types.py → dispatcher.py |
| 7 | T014 | Sequential | actions.py |
| 8 | T015, T016 | Parallel | rules.json, test file |
| 9 | T017, T018, T019 | Sequential | Full verification |

## Phase Dependencies

- **Phase 1 → Phase 2-5:** State backend required for all state features
- **Phase 2 → Phase 3:** Trigger groups before capture groups (both affect dispatcher)
- **Phase 3 → Phase 4:** Captures before state triggers (captures provide context)
- **Phase 4 → Phase 5:** State triggers before actions (triggers test state exists)
- **Phase 5 → Phase 6:** Actions before templates (actions set state for templates)
- **Phase 6 → Phase 7:** All features before integration

## Parallel Safety Rules

Tasks can run in parallel (`[P]`) when:
- Same phase (shared prerequisites complete)
- Different file paths or different functions in same file
- No data dependencies between them

Tasks must run sequentially when:
- Different phases
- Same file path with overlapping changes
- Data dependency exists

## Notes

- Phase 4 allows parallelism: types.py (StateExistsTrigger) and matchers.py (match function) are independent
- Phase 7 allows parallelism: rules.json and test file are independent
- Most phases are sequential due to dispatcher.py being the integration point
