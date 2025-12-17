# Task Dependencies: Spec Management API

## Overview

Task dependency graph for parallel dispatch. Tasks marked `[P]` can run in parallel if they modify different files.

## Dependency Graph

```
Phase 1: [Foundation]
    models.py ─────────────────────────────────────┐
                                                   │
Phase 2: [Task Operations]                         │
    tasks.py ──────────────────────────────────────┤
      └─ depends on: models.py                     │
                                                   │
Phase 3: [Section Operations]                      │
    sections.py [P] ───────────────────────────────┤
      └─ no dependencies on Phase 2                │
                                                   │
Phase 4: [Query & Lifecycle]                       │
    query.py [P] ──────────────────────────────────┤
      └─ depends on: models.py                     │
    lifecycle.py [P] ──────────────────────────────┤
      └─ depends on: models.py, query.py           │
                                                   │
Phase 5: [Integration]                             │
    __init__.py ───────────────────────────────────┤
      └─ depends on: all modules                   │
    templates update ──────────────────────────────┤
    create.py update ──────────────────────────────┤
                                                   │
Phase 6: [CLI]                                     │
    cli.py ────────────────────────────────────────┘
      └─ depends on: all API functions
```

## Execution Batches

| Batch | Tasks | Type | Files |
|-------|-------|------|-------|
| 1 | models.py | Sequential | src/dignity/spec/models.py |
| 2 | tasks.py | Sequential | src/dignity/spec/tasks.py |
| 3 | sections.py, query.py | Parallel | src/dignity/spec/sections.py, query.py |
| 4 | lifecycle.py | Sequential | src/dignity/spec/lifecycle.py |
| 5 | Integration | Sequential | __init__.py, templates, create.py |
| 6 | CLI | Sequential | src/dignity/cli.py |

## Phase Dependencies

- Phase 2 requires Phase 1 complete
- Phase 3 can start after Phase 1 (parallel with Phase 2)
- Phase 4 requires Phase 1, query.py before lifecycle.py
- Phase 5 requires Phases 2-4 complete
- Phase 6 requires Phase 5 complete

## Parallel Safety Rules

Tasks can run in parallel (`[P]`) when:
- Same phase (shared prerequisites complete)
- Different file paths
- No data dependencies between them

## Notes

- sections.py has no dependency on tasks.py - can parallelize
- query.py and lifecycle.py share models.py dependency but lifecycle needs query
