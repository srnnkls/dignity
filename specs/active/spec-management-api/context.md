# Context: Spec Management API

## Native Plan

**Source:** `/Users/srnnkls/.claude/plans/cached-yawning-stonebraker.md`

- Goal: Programmatic spec management with TodoWrite-compatible interface
- Approach: 5 modules + CLI, spec-scoped task IDs
- Resolved: Full scope, explicit exceptions, no file locking, dual lookup

## Key Files

| File | Purpose | Changes |
|------|---------|---------|
| `src/dignity/spec/__init__.py` | Public API | Export new functions |
| `src/dignity/spec/create.py` | Spec creation | Use Task model |
| `src/dignity/spec/models.py` | Data models | NEW |
| `src/dignity/spec/tasks.py` | Task CRUD | NEW |
| `src/dignity/spec/sections.py` | Markdown ops | NEW |
| `src/dignity/spec/query.py` | Lookup | NEW |
| `src/dignity/spec/lifecycle.py` | Archive/restore | NEW |
| `src/dignity/spec/templates/tasks.yaml.jinja2` | Task template | Add next_id |
| `src/dignity/cli.py` | CLI commands | Add task/lifecycle/query subcommands |

## Key Types

| Type | Purpose | Location |
|------|---------|----------|
| `Task` | Task with id, content, status, active_form | models.py |
| `Status` | StrEnum: pending, in_progress, completed | models.py |
| `TasksFile` | tasks.yaml structure | models.py |
| `Spec` | Full spec metadata | models.py |

## Implementation Decisions

1. **Spec-scoped IDs** - `{CODE}-{NNN}` format, auto-incremented via `next_id` in tasks.yaml
2. **Explicit exceptions** - TaskNotFoundError, SectionNotFoundError, SpecNotFoundError
3. **No file locking** - Single-user CLI, simple read-modify-write
4. **Dual lookup** - Accept spec code OR name interchangeably
5. **Multiple in_progress** - No auto-clear, matches TodoWrite flexibility

## Dependencies

**Internal:**
- `dignity.spec.create` - Existing creation logic
- `dignity.spec.index` - Code → name mapping
- `dignity.spec.validation` - Name/code utilities

**External:**
- `pyyaml` - YAML parsing (already used)
- `typer` - CLI framework (already used)

## Open Questions

None - all clarified during validation.

## Gotchas & Learnings

(To be filled during implementation)
