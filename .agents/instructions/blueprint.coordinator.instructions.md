---
name: "Coordinator and API Client"
description: "Where the coordinator, the API client and its exception hierarchy live in this layout, and the library decision"
applyTo: "custom_components/**/coordinator/**/*.py, custom_components/**/api/**/*.py"
paths:
  - "custom_components/**/coordinator/**/*.py"
  - "custom_components/**/api/**/*.py"
---

# Coordinator and API Client Instructions

**Procedure:** `haci-coordinator-debug` (plugin `haci-build`) — load it when data is stale, entities are unavailable or
setup fails. The Home Assistant rules for the coordinator and the API client are `haci.coordinator`, which loads with
this file; what follows is only what this project adds. Running and reading the development instance is
[`blueprint-dev-instance`](../skills/blueprint-dev-instance/SKILL.md).

- **Applies to** `custom_components/<domain>/coordinator/` and `custom_components/<domain>/api/`. An integration that
  fetches nothing has no `api/` package; the layering is unchanged.
- Entities in the `<platform>/` packages read `coordinator.data`; only `coordinator/` calls `api/`.
- The `aiohttp` session comes from `async_get_clientsession(hass)` in `__init__.py`, which also calls
  `async_config_entry_first_refresh()` in `async_setup_entry()`.
- The exception hierarchy is defined in `api/__init__.py`: `{ClassPrefix}ApiClientError`,
  `{ClassPrefix}ApiClientCommunicationError`, `{ClassPrefix}ApiClientAuthenticationError` and
  `{ClassPrefix}ApiClientRateLimitError(retry_after)`.
- A debug line that masks a key, token or account ID follows `partial_redact` in
  [`blueprint.python`](blueprint.python.instructions.md#error-handling).

## API client or PyPI library

The criteria are in `AGENTS.md` § Custom Integration Flexibility. The choice is expensive to reverse: record it in a
decision record in `docs/development/decisions/` (see [`blueprint-decisions`](../skills/blueprint-decisions/SKILL.md)).
Adding the dependency itself — `manifest.json` **and** `requirements.txt`, kept in sync — is covered by
[`blueprint-tooling`](../skills/blueprint-tooling/SKILL.md).

## Package organization

Split large modules (~200–400 lines per file):

- `coordinator/base.py` — core coordinator
- `coordinator/data_processing.py` — transform helpers
- `api/client.py` — main client
- `api/auth.py` — auth helpers (OAuth, token refresh)
- `api/endpoints/` — grouped endpoints (if many)
