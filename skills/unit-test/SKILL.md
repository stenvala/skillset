---
name: test-python-unit
description: Create python unit tests
---

# CLI Unit Test Creation

Create pytest unit tests for CLI modules following project testing patterns.

## When to Use

- Writing tests after implementing CLI modules or utilities
- Adding test coverage to existing code
- Testing error scenarios, edge cases, and validation logic

## File Structure

Tests mirror source structure with one folder per source file and one test file per function:

```
tests/
├── <module_name>/               # One folder per source file
│   ├── __init__.py
│   ├── conftest.py              # Fixtures specific to this module
│   ├── test_<function_a>.py     # One file per function
│   └── test_<function_b>.py
└── conftest.py                  # Global fixtures
```

Example for this project:

```
tests/
├── conftest.py
├── discovery/
│   ├── test_find_skills.py
│   └── test_find_commands.py
├── paths/
│   ├── test_get_cache_dir.py
│   ├── test_abbrev.py
│   ├── test_require_project_dir.py
│   └── test_add_to_global_skillset.py
├── linking/
│   ├── conftest.py
│   ├── test_fuzzy_match.py
│   ├── test_is_managed_copy.py
│   ├── test_copy_dir.py
│   └── test_link_skills.py
├── manifest/
│   ├── test_load_manifest.py
│   ├── test_record_install.py
│   └── test_get_install_options.py
├── repo/
│   ├── test_parse_repo_spec.py
│   └── test_parse_github_url.py
└── settings/
    ├── test_load_settings.py
    ├── test_deep_merge.py
    ├── test_find_repo_permissions.py
    └── test_add_read_permission.py
```

## Test Approach

- **Pure functions**: Test directly with no mocking needed (parsers, matchers, merges)
- **Filesystem operations**: Use `tmp_path` fixture for isolation
- **Path-dependent code**: Use `monkeypatch` to redirect `Path.home()` and `get_git_root()`
- **No class wrappers**: Module-level pytest functions only

## Instructions

### 1. Create Test File

Create ONE test file at a time, following the naming pattern.

### 2. Run Test Immediately

```bash
uv run pytest <path/to/test_file.py> -v
```

### 3. Verify Zero Warnings

Fix any warnings before proceeding to next test.

### 4. Repeat

Only then create the next test file.

## Key Rules

1. **One folder per source file**: Each source module gets its own test folder
2. **One test file per function**: Each public function gets its own test file
3. **Module-level functions only**: No class wrappers — use pytest functions
4. **Mirror structure**: Test folders mirror source modules exactly
5. **Test immediately**: Create ONE file, run, validate, then proceed
6. **Zero warnings**: All tests must pass with zero warnings
7. **AAA pattern**: Arrange, Act, Assert structure

## Running Tests

```bash
uv run pytest <path/to/test_file.py> -v      # Single file
uv run pytest tests/<module>/ -v             # All tests for a module
uv run pytest -v                             # All tests
```
