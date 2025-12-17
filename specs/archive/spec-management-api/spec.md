---
code: SMA
issue_type: Feature
created: 2025-12-17
completed: 2025-12-17
status: Complete
claude_plan: /Users/srnnkls/.claude/plans/cached-yawning-stonebraker.md
---

# Spec: Spec Management API

## Overview

Extend `src/dignity/spec/` with programmatic endpoints for managing specs after creation. Task interface aligns with Claude Code's native TodoWrite tool, using spec-scoped IDs (`FSD-001`).

## Context

The existing spec module provides creation via Jinja2 templates but lacks post-creation manipulation. This feature adds CRUD operations for tasks, markdown section manipulation, spec querying, and lifecycle management.

## Architectural Approach

**5 new modules:**

1. `models.py` - Task, Status, Spec, TasksFile dataclasses
2. `tasks.py` - Task CRUD with auto-incrementing IDs
3. `sections.py` - Markdown section manipulation
4. `query.py` - Spec lookup by code or name
5. `lifecycle.py` - Archive/restore operations

**Task ID format:** `{SPEC_CODE}-{NNN}` (e.g., `SMA-001`)

**Error handling:** Explicit exceptions (TaskNotFoundError, SectionNotFoundError, SpecNotFoundError)

## Success Criteria

1. Task operations work with spec-scoped IDs matching TodoWrite interface
2. Section manipulation preserves markdown structure
3. Lookup accepts both spec code and name
4. CLI commands expose all API operations
5. Existing spec creation continues to work

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing templates | tasks.yaml template updated to include `next_id` field |
| ID collisions | Auto-increment managed per-spec via `next_id` counter |
| Markdown parsing edge cases | Use heading-based section detection, preserve non-matched content |
