---
name: "Tests"
description: "Test layout, the shared fixtures, warnings as errors, and the test commands"
applyTo: "tests/**/*.py"
paths:
  - "tests/**/*.py"
---

# Test Instructions

**Procedure:** `haci-testing`, from the `haci-quality` plugin — load it before writing or repairing a test. The Home
Assistant rules for a test are in `haci.tests.instructions.md` beside this file; this file adds what is particular to
this repository's `tests/`.

**Applies to:** `tests/` directory

## Layout

`tests/` mirrors `custom_components/<domain>/`, one `test_*.py` per module or feature:

```text
tests/
  conftest.py          # Shared fixtures
  fixtures/            # Recorded payloads, read with load_fixture(name)
  test_init.py         # Integration setup
  test_config_flow.py  # Config flow
  sensor/test_air_quality.py
  binary_sensor/test_filter.py
  snapshots/           # Syrupy .ambr files beside the tests they belong to
```

## Pytest markers

`--strict-markers` rejects any other:

- `@pytest.mark.unit` - Fast, isolated (no external dependencies)
- `@pytest.mark.integration` - With coordinator, time service, etc.

## Fixtures

**Defined in `tests/conftest.py`** — use these names, never a per-file variant:

- `config_entry` - `MockConfigEntry`, not yet added to `hass`; parametrize it indirectly to set its options
- `mock_api` - the mocked data source, patched where the integration imports it; in the template it patches the
  client's `_api_wrapper`, so the client's own payload handling stays under test
- `init_integration` - `config_entry` set up with `mock_api` active, returned loaded

A third-party library client is imported twice — by `__init__.py` for setup and by
`config_flow_handler/validators/credentials.py` for the config flow — so its `mock_api` patches both; the top-level
`config_flow.py` is only a discovery shim and imports no client.

## Warnings and deprecations

- `filterwarnings = ["error"]` in `pyproject.toml` fails the suite on any Python warning. Its ignores are only for
  warnings Home Assistant Core raises about a library it pins, each keyed to the exact message with a comment saying
  where it comes from.
- The autouse `fail_on_deprecation_report` fixture in `tests/conftest.py` fails a test whose `caplog` holds a
  deprecation Home Assistant logged for this integration. Fix the cause; never narrow the fixture.
- `asyncio_mode = "auto"`: async tests need no `@pytest.mark.asyncio`.

## Test Commands

```bash
script/test                    # All tests
script/test -v                 # Verbose
script/test --cov-html         # Coverage report (htmlcov/index.html)
script/test tests/sensor/      # Specific directory
script/test -k test_sensor     # Pattern matching
script/test -m unit            # Marker filtering
script/test --picked           # Only the test files changed in the working tree
script/test --snapshot-update  # Update snapshots
script/test -x                 # Stop at the first failure — the one to use while iterating
script/test --cov-report term-missing   # Coverage with the uncovered lines listed in the terminal
```

Never run `pytest` directly — `script/test` activates the venv and collects `script/tests/` beside `tests/`.
