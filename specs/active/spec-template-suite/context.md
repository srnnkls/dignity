# Context: Spec Template Suite

## Native Plan

**Source:** `/Users/srnnkls/.claude/plans/elegant-moseying-crescent.md`

- Goal: Extend spec create to generate 5 files with Jinja2 templates
- Approach: Package resources via importlib.resources, conditionals for scaling
- Validated: Issue type, template organization, error handling, templating engine

## Key Files

| File | Purpose | Changes |
|------|---------|---------|
| `src/dignity/spec/create.py:50-140` | Main create function | Replace inline templates with render calls |
| `src/dignity/spec/templates/__init__.py` | New | Template loader and renderer |
| `src/dignity/spec/templates/*.j2` | New | 5 Jinja2 template files |
| `tests/spec/test_create.py` | Test suite | Update for new files, remove tasks.yaml tests |
| `pyproject.toml` | Dependencies | Add jinja2>=3.0 |

## Key Types

| Type | Purpose | Location |
|------|---------|----------|
| `SpecConfig` | Return value from create() | `src/dignity/spec/create.py:28` |
| `SpecCreateError` | Custom exception | `src/dignity/spec/create.py:19` |
| `Environment` | Jinja2 template environment | jinja2 package |

## Implementation Decisions

### 2025-12-14: Jinja2 over string.Template

**Context:** Need conditionals for content scaling by issue_type
**Decision:** Use Jinja2 instead of string.Template or custom parser
**Alternatives:** string.Template (no conditionals), custom markers (reinventing wheel)
**Impact:** Adds external dependency but provides proven templating solution

### 2025-12-14: Single templates with conditionals

**Context:** Templates need different content for feature vs bug/chore
**Decision:** One template per output file with `{% if %}` blocks
**Alternatives:** Separate directories per issue_type (duplication), base+overrides (complexity)
**Impact:** Simpler maintenance, all variations visible in one file

### 2025-12-14: Validate before render

**Context:** Missing template variables cause confusing errors
**Decision:** Check required variables exist before rendering
**Alternatives:** Let Jinja2 fail (cryptic errors), partial rendering (broken output)
**Impact:** Clear error messages, fail-fast behavior

## Dependencies

**Internal:**
- `dignity.spec.validation` - Name validation, code generation
- `dignity.spec.index` - Index file operations

**External:**
- `jinja2>=3.0` - Template engine (new dependency)
- `importlib.resources` - Standard library, package resource loading

## Open Questions

None - all clarified during validation.

## Gotchas & Learnings

*Updated during implementation*
