---
name: "Service Action Implementation"
description: "Where actions are registered and implemented in this project's layout"
applyTo: "custom_components/**/service_actions/**/*.py"
paths:
  - "custom_components/**/service_actions/**/*.py"
---

# Service Actions Instructions

**Procedure:** `haci-service-action` (plugin `haci-build`) — load it before adding, changing or removing an action. The
Home Assistant rules for action implementation files are `haci.service-actions`, which loads with this file; what
follows is only what this project adds.

- Actions are registered in `service_actions/__init__.py`, in `async_setup_services(hass)`; the handler bodies go in
  one module per logical group under `service_actions/`.
- `async_setup_services(hass)` is already called from `async_setup()` in `__init__.py` — do not add a second call in
  `async_setup_entry()`.
- Handlers take `(hass, entry, call)`, with `entry` typed as `{ClassPrefix}ConfigEntry`; the wrapper in
  `service_actions/__init__.py` resolves the entry before calling the handler.
- Client failures are the `{ClassPrefix}ApiClient…Error` classes from `api/`; each is wrapped in a translated
  `HomeAssistantError`, with the key in `translations/en.json` only
  (`haci-translations`).
