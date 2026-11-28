---
name: "Home Assistant tests"
description: "Fixtures, writing a test, core interfaces, registry assertions, mocking and snapshots"
applyTo: "tests/**/*.py"
paths:
  - "tests/**/*.py"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-quality/skills/haci-testing/references/rules.md sha256:37bb7f5873cc89b5 — written by script/haci-vendor, do not edit -->

# Home Assistant test rules

**Procedure:** the `haci-testing` skill — load it before writing or repairing a test. This file is the rule set; the
skill is the scaffolding and the judgement calls.

**Official documentation:** [Testing](https://contributors.home-assistant.io/core/development/testing/) and
[Writing tests](https://contributors.home-assistant.io/core/development/tests/) — both describe the **Core** workflow.
A custom integration takes their patterns, not their commands or their `tests/components/` paths.

## Fixtures

**No `coordinator` fixture.** A test that builds or patches the coordinator couples itself to its constructor and
internals; mock the client and let setup build the coordinator, then assert through `hass.states`.

**From `pytest-homeassistant`** — never redefine: `hass` (loads custom integrations without a wrapper fixture),
`hass_client` (authenticated HTTP client, needed for diagnostics), `entity_registry`, `device_registry`,
`issue_registry`, `entity_registry_enabled_by_default`, `snapshot`, `caplog`. `freezer` comes from `pytest-freezer`;
advance it with `freezer.tick()` plus `async_fire_time_changed`, never `time.sleep`.

**On the older `pytest-homeassistant-custom-component`** the helpers live in
`pytest_homeassistant_custom_component.common` instead of `pytest_homeassistant.common`, and `hass` loads a custom
integration only with the `enable_custom_integrations` fixture — make it autouse in `conftest.py`.

## Snapshots

[Syrupy](https://github.com/syrupy-project/syrupy) snapshots are for large outputs: entity states, registry entries,
diagnostics, config flow results. Commit the `.ambr` files.

- The file is named after the test file and lives in `snapshots/` beside it — `test_sensor.py` →
  `snapshots/test_sensor.ambr`. Renaming a test file orphans its snapshot.
- They complement functional tests and do not replace them. A snapshot asserts "unchanged since I recorded it", which
  assumes the recording was right. To check that an entity goes unavailable on an API error, assert that specific
  state — do not snapshot the whole entity and hope.
- Pattern: `assert hass.states.get("sensor.x") == snapshot`

## Writing a test

- Type every parameter, fixtures included; a fixture used only for its side effect goes in
  `@pytest.mark.usefixtures(...)`, not in the signature
- No `if` in a test body — split the test, or parametrize with `pytest.param(..., id="...")` so a failure names its
  case
- No network — `pytest-homeassistant` blocks sockets except to `127.0.0.1`; a test that needs one is missing a mock
- Recorded payloads go in `tests/fixtures/`, loaded with `load_fixture(name)` or `load_json_object_fixture(name)` from a
  test file at any depth — never with a second argument, which points at Core's tree. Tests outside `<rootdir>/tests`
  need the `ha_test_root` ini option, or the loaders look in the wrong place

## Core interface testing

**Test through core interfaces, not integration internals.** The point is not purity — a test which reaches into the
integration has to be rewritten every time the integration is refactored, so it stops being a safety net exactly when
one is needed.

✅ `async_setup_component` or `hass.config_entries.async_setup`, `MockConfigEntry`, `hass.states`, `hass.services`,
`entry.state`, and the device and entity registries

❌ Direct entity instantiation, reading entity properties, reaching into `entry.runtime_data`

## Registry testing

- Device: `device_registry.async_get_device_by_identifier((DOMAIN, id), config_entry.entry_id)` — verify
  manufacturer, model, identifiers, and ownership by `config_entry_id`
- Entity: `entity_registry.async_get("sensor.x")` — verify unique_id, disabled state
- Lifecycle: `async_setup()` → `LOADED`, `async_unload()` → `NOT_LOADED`
- Multiple entries: when two entries expose the same identifier or connection, verify that each entry owns a separate
  device and that entry-scoped lookups return the correct one
- Subentries: verify that each subentry owns a separate device; never assert or depend on a device shared by subentries

**Never in new tests:** the deprecated unscoped `async_get_device()` lookup or the plural
`DeviceEntry.config_entries` / `DeviceEntry.config_entries_subentries` compatibility properties.

## Mocking

✅ **Mock:** external APIs, network calls, time-dependent operations — `patch.object()` with `return_value` for
success, `side_effect` for errors

❌ **Don't mock:** Home Assistant internals, the integration's own code

## Entity and config flow tests

- Entity: set up the entry → `await hass.async_block_till_done()` → `hass.states.get("<entity_id>")` → assert state and
  attributes
- Config flow: `hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})`, then
  `async_configure`; verify `result["type"]` (form, create_entry, abort), `result["step_id"]`, `result["errors"]`

## Coverage targets

Coordinator logic, config flow validation, error handling, entity state calculations.
[Home Assistant Core's own tests](https://github.com/home-assistant/core/tree/dev/tests/components) are the reference
for a pattern this file does not cover.
