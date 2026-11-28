---
name: "Entity Platforms"
description: "Where entities live in this project: the base entity, the platform packages, entity_utils, and the write helper"
applyTo: "custom_components/**/alarm_control_panel/**/*.py, custom_components/**/binary_sensor/**/*.py, custom_components/**/button/**/*.py, custom_components/**/camera/**/*.py, custom_components/**/climate/**/*.py, custom_components/**/cover/**/*.py, custom_components/**/date/**/*.py, custom_components/**/datetime/**/*.py, custom_components/**/device_tracker/**/*.py, custom_components/**/event/**/*.py, custom_components/**/fan/**/*.py, custom_components/**/humidifier/**/*.py, custom_components/**/image/**/*.py, custom_components/**/lawn_mower/**/*.py, custom_components/**/light/**/*.py, custom_components/**/lock/**/*.py, custom_components/**/media_player/**/*.py, custom_components/**/notify/**/*.py, custom_components/**/number/**/*.py, custom_components/**/scene/**/*.py, custom_components/**/select/**/*.py, custom_components/**/sensor/**/*.py, custom_components/**/siren/**/*.py, custom_components/**/switch/**/*.py, custom_components/**/text/**/*.py, custom_components/**/time/**/*.py, custom_components/**/todo/**/*.py, custom_components/**/update/**/*.py, custom_components/**/vacuum/**/*.py, custom_components/**/valve/**/*.py, custom_components/**/water_heater/**/*.py, custom_components/**/entity/**/*.py, custom_components/**/entity_utils/**/*.py"
paths:
  - "custom_components/**/alarm_control_panel/**/*.py"
  - "custom_components/**/binary_sensor/**/*.py"
  - "custom_components/**/button/**/*.py"
  - "custom_components/**/camera/**/*.py"
  - "custom_components/**/climate/**/*.py"
  - "custom_components/**/cover/**/*.py"
  - "custom_components/**/date/**/*.py"
  - "custom_components/**/datetime/**/*.py"
  - "custom_components/**/device_tracker/**/*.py"
  - "custom_components/**/event/**/*.py"
  - "custom_components/**/fan/**/*.py"
  - "custom_components/**/humidifier/**/*.py"
  - "custom_components/**/image/**/*.py"
  - "custom_components/**/lawn_mower/**/*.py"
  - "custom_components/**/light/**/*.py"
  - "custom_components/**/lock/**/*.py"
  - "custom_components/**/media_player/**/*.py"
  - "custom_components/**/notify/**/*.py"
  - "custom_components/**/number/**/*.py"
  - "custom_components/**/scene/**/*.py"
  - "custom_components/**/select/**/*.py"
  - "custom_components/**/sensor/**/*.py"
  - "custom_components/**/siren/**/*.py"
  - "custom_components/**/switch/**/*.py"
  - "custom_components/**/text/**/*.py"
  - "custom_components/**/time/**/*.py"
  - "custom_components/**/todo/**/*.py"
  - "custom_components/**/update/**/*.py"
  - "custom_components/**/vacuum/**/*.py"
  - "custom_components/**/valve/**/*.py"
  - "custom_components/**/water_heater/**/*.py"
  - "custom_components/**/entity/**/*.py"
  - "custom_components/**/entity_utils/**/*.py"
---

# Entity Platform Instructions

**Procedure:** `haci-entity-platform` (plugin `haci-build`) — load it before adding a platform or an entity. The Home
Assistant rules for entity platforms, base entities and entity utilities are `haci.entities`, which loads with this
file; what follows is only what this project adds.

## Layout

- **`entity/`** — the base entity class, `{ClassPrefix}Entity` in `entity/base.py`. **`coordinator/`** fetches the
  data; entities never call the API directly.
- Each platform is a package, one entity class per file:

  ```text
  custom_components/<domain>/<platform>/
  ├── __init__.py        # async_setup_entry, PARALLEL_UPDATES + aggregated ENTITY_DESCRIPTIONS
  └── <group>.py         # ENTITY_DESCRIPTIONS + entity class for one logical group
  ```

  Once a `value_fn` description carries the lookup, the single entity class gets its own module and the group files
  hold descriptions only — this is what `sensor/` does:

  ```text
  custom_components/<domain>/sensor/
  ├── __init__.py        # async_setup_entry + aggregated ENTITY_DESCRIPTIONS
  ├── entity.py          # the description subclass and the single entity class
  ├── air_quality.py     # ENTITY_DESCRIPTIONS only
  └── diagnostic.py      # ENTITY_DESCRIPTIONS only
  ```

- Group files by purpose: `primary_entities.py`, `diagnostic.py`, `configuration.py`. A complex entity over ~100
  lines gets a file of its own.
- The closest sibling to read before a new sensor is `custom_components/<domain>/sensor/air_quality.py`.
- `PLATFORMS` in `custom_components/<domain>/__init__.py` stays alphabetical; `async_setup_entry` and
  `async_unload_entry` already forward and unload it (`async_unload_platforms_or_raise`), so a new platform needs no
  other change there.

## Base entity

- **Inherit `(PlatformEntity, {ClassPrefix}Entity)`** — platform class first. Image and camera entities therefore call
  both constructors explicitly (the skill's `other-platforms` reference).
- The base entity supplies the unique ID `{entry_id}_{description.key}`, `identifiers`, `name`, `manufacturer` and
  `model` of the device info, attribution and `_attr_has_entity_name = True`.
- **Constructor:** `super().__init__(coordinator, entity_description)` — the base handles the setup.
- **Imports:** `from homeassistant.components.<platform> import PlatformEntity, PlatformEntityDescription` and
  `from custom_components.<domain>.entity import {ClassPrefix}Entity` — absolute, because Ruff rejects a relative
  import that reaches into a parent package ([`blueprint.python`](blueprint.python.instructions.md)).
- **Descriptions** are a module-level `ENTITY_DESCRIPTIONS: tuple[PlatformEntityDescription, ...]`; the description
  subclass is `{ClassPrefix}<Platform>EntityDescription`.
- **Platform setup:** `async_add_entities(EntityClass(entry.runtime_data.coordinator, desc) for desc in DESCRIPTIONS)`,
  importing the entity classes and descriptions from the platform's submodules; one platform may combine several
  entity classes.
- **Writes** go through `self._async_write(lambda client: client.async_x(...), "translation_key")` on the base entity.
  It reaches the API client, turns a client error into a translated `HomeAssistantError` and then awaits
  `coordinator.async_request_refresh()`.

## Entity utilities

Add to `entity_utils/` what is used by three or more entity classes, complex logic that benefits from its own tests,
and device info customisation or state formatting. Import it absolutely:
`from custom_components.<domain>.entity_utils.module import function`.

## Translations and validation

- Entity names, states and attribute names go into `translations/en.json` only
  (`haci-translations`, plugin `haci-build`).
- After a change: `script/lint`, `script/type-check`, `script/hassfest`, `script/test`; then restart Home Assistant
  with `./script/develop` and confirm the entity appears
  (`haci-coordinator-debug`, plugin `haci-build`, when it does not).
