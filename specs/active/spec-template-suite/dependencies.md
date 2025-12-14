# Task Dependencies: Spec Template Suite

## Overview

Task dependency graph for parallel dispatch. Tasks marked `[P]` can run in parallel if they modify different files.

## Dependency Graph

```
Phase 1: [Setup]
    T001 (Add Jinja2 dependency)
               │
               ▼
Phase 2: [Template Module]
    T002 (Create templates package)
               │
               ▼
    T003 ─┬─ [P] (PackageLoader)
    T004 ─┘     (Variable validation)
               │
               ▼
Phase 3: [Template Files]
    T005 ─┬─ [P] (spec.md.j2)
    T006 ─┤     (context.md.j2)
    T007 ─┤     (tasks.md.j2)
    T008 ─┤     (dependencies.md.j2)
    T009 ─┘     (validation-checklist.md.j2)
               │
               ▼
Phase 4: [Integration]
    T010 (Update create.py)
               │
               ▼
    T011 (Update CLI output)
               │
               ▼
Phase 5: [Testing]
    T012 ─┬─ [P] (Template module tests)
    T013 ─┘     (Update create tests)
               │
               ▼
    T014 (Run full test suite)
               │
               ▼
Phase 6: [Documentation]
    T015 (Update docstrings)
```

## Execution Batches

| Batch | Tasks | Type | Files |
|-------|-------|------|-------|
| 1 | T001 | Sequential | pyproject.toml |
| 2 | T002 | Sequential | templates/__init__.py (create) |
| 3 | T003, T004 | Parallel | templates/__init__.py (different functions) |
| 4 | T005-T009 | Parallel | 5 different .j2 files |
| 5 | T010 | Sequential | create.py |
| 6 | T011 | Sequential | cli.py |
| 7 | T012, T013 | Parallel | Different test files |
| 8 | T014 | Sequential | Full suite verification |
| 9 | T015 | Sequential | Docstrings |

## Phase Dependencies

- **Phase 1 → Phase 2:** Jinja2 must be installed before template module
- **Phase 2 → Phase 3:** Template loader must exist before templates
- **Phase 3 → Phase 4:** Templates must exist before create.py can use them
- **Phase 4 → Phase 5:** Integration before testing
- **Phase 5 → Phase 6:** Tests pass before documentation

## Parallel Safety Rules

Tasks can run in parallel (`[P]`) when:
- Same phase (shared prerequisites complete)
- Different file paths
- No data dependencies between them

**Batch 3 (T003, T004):** Both add functions to same file but independent
**Batch 4 (T005-T009):** All template files are independent
**Batch 7 (T012, T013):** Different test files

## Notes

- Batch 4 is the main parallelization opportunity (5 templates)
- T010 (create.py update) is the integration bottleneck
- T014 should verify all previous work before documentation
