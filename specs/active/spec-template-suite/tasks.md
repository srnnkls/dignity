# Tasks: Spec Template Suite

## Phase 1: Setup

- [ ] **Add Jinja2 dependency**
  - Files: `pyproject.toml`
  - Add `jinja2>=3.0` to dependencies
  - Run `uv sync` to install
  - Completion: Import works in Python

## Phase 2: Template Module

- [ ] **Create templates package directory**
  - Files: `src/dignity/spec/templates/__init__.py`
  - Create directory structure
  - Add `__init__.py` with loader/renderer functions
  - Completion: `from dignity.spec.templates import render_template` works

- [ ] **Implement PackageLoader for Jinja2**
  - Files: `src/dignity/spec/templates/__init__.py`
  - Custom BaseLoader using importlib.resources
  - Load templates from package data
  - Completion: Templates load from installed package

- [ ] **Implement variable validation**
  - Files: `src/dignity/spec/templates/__init__.py`
  - `validate_vars(required, provided)` function
  - Raise ValueError with missing var names
  - Completion: Clear error on missing vars

## Phase 3: Template Files

- [ ] **Create spec.md.j2 template**
  - Files: `src/dignity/spec/templates/spec.md.j2`
  - Frontmatter with variables
  - Sections with `{% if issue_type == 'feature' %}` conditionals
  - Completion: Renders correctly for all issue types

- [ ] **Create context.md.j2 template**
  - Files: `src/dignity/spec/templates/context.md.j2`
  - Key files, decisions, dependencies sections
  - Scale by issue_type
  - Completion: Renders correctly

- [ ] **Create tasks.md.j2 template**
  - Files: `src/dignity/spec/templates/tasks.md.j2`
  - Phase-based checklist with `- [ ]` items
  - Completion: Renders with proper checkbox format

- [ ] **Create dependencies.md.j2 template**
  - Files: `src/dignity/spec/templates/dependencies.md.j2`
  - DAG structure, batch table
  - Completion: Renders correctly

- [ ] **Create validation-checklist.md.j2 template**
  - Files: `src/dignity/spec/templates/validation-checklist.md.j2`
  - Taxonomy table, clarification log
  - Completion: Renders correctly

## Phase 4: Integration

- [ ] **Update create.py to use templates**
  - Files: `src/dignity/spec/create.py`
  - Import render_template
  - Remove inline template strings
  - Generate all 5 files
  - Remove tasks.yaml generation
  - Completion: All files generated correctly

- [ ] **Update CLI output messages**
  - Files: `src/dignity/cli.py`
  - Show all 5 files created
  - Remove tasks.yaml reference
  - Completion: CLI shows correct files

## Phase 5: Testing

- [ ] **Add template module tests**
  - Files: `tests/spec/test_templates.py`
  - Test loader, renderer, validation
  - Completion: All template functions tested

- [ ] **Update create tests for new files**
  - Files: `tests/spec/test_create.py`
  - Add tests for context.md, tasks.md, dependencies.md, validation-checklist.md
  - Remove tasks.yaml tests
  - Completion: Tests verify all 5 files

- [ ] **Run full test suite**
  - Verify all 256+ tests pass
  - Run type checker
  - Completion: CI-ready

## Phase 6: Documentation

- [ ] **Update spec package docstrings**
  - Files: `src/dignity/spec/__init__.py`, `src/dignity/spec/create.py`
  - Document new files generated
  - Completion: Help text accurate
