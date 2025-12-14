---
issue_type: Feature
created: 2025-12-14
status: Active
claude_plan: /Users/srnnkls/.claude/plans/elegant-moseying-crescent.md
---

# Spec: Spec Template Suite

## Overview

Extend `dignity spec create` to generate all 5 spec documents using Jinja2 templates stored as package resources via `importlib.resources`. Templates scale content by issue_type (feature=full, bug/chore=minimal).

## Context

**Current state:** The `dignity spec create` command generates only `spec.md` and `tasks.yaml` using inline Python string templates with `.format()` substitution.

**Target state:** Command generates 5 files (`spec.md`, `context.md`, `tasks.md`, `dependencies.md`, `validation-checklist.md`) using Jinja2 templates with conditional blocks that scale content based on issue_type.

## Architectural Approach

### Template Engine

Use Jinja2 for templating:
- Supports `{% if %}` conditionals for content scaling
- Well-maintained, widely used
- Clean separation of template content from Python code

### Package Resources

Store templates in `src/dignity/spec/templates/` as package data:
- Use `importlib.resources` (standard library) for loading
- Templates have `.j2` extension to distinguish from output
- Works with installed packages, not just source trees

### Content Scaling

Templates use conditionals to scale by issue_type:
```jinja2
{% if issue_type == 'feature' %}
### Detailed Section
{% endif %}
```

- `feature`: Full content with all sections
- `bug`/`chore`: Minimal versions with essential sections only

### Variable Validation

Validate required template variables before rendering:
- Check all required vars are provided
- Fail loudly with clear error message listing missing vars
- Prevents partial/broken output

## Success Criteria

1. `dignity spec create` generates all 5 spec files
2. Templates load correctly from installed package
3. Content scales appropriately by issue_type
4. Missing variables produce clear error messages
5. All existing tests pass after migration
6. `tasks.yaml` removed, replaced by `tasks.md`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Jinja2 dependency adds complexity | Well-established library, minimal learning curve |
| Template syntax errors at runtime | Add template validation tests |
| Package data not included in install | Verify with `pip install -e .` during testing |
