---
name: "Home Assistant coordinator and API client"
description: "Three-layer architecture, sessions, timeouts, the API exception hierarchy, update intervals, pull versus push, and caching"
applyTo: "custom_components/**/coordinator/**/*.py, custom_components/**/api/**/*.py"
paths:
  - "custom_components/**/coordinator/**/*.py"
  - "custom_components/**/api/**/*.py"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-build/skills/haci-coordinator-debug/references/rules.md sha256:5918d9d864deda1e — written by script/haci-vendor, do not edit -->

# Coordinator and API client rules

Procedure: the `haci-coordinator-debug` skill (plugin `haci-build`) — the run loop for stale data, unavailable entities
and failed setups, how to read a running instance and its log, and the four coordinator failures no exception-mapping
table can express.

**Applies to:** the coordinator and the API client, wherever the project's layout puts them — Core's default is
`coordinator.py` beside the integration's `__init__.py`, and the client in a PyPI library. An integration that fetches
nothing has no API client; the layering below is unchanged either way.

## Three-layer architecture (critical)

**Entities → Coordinator → API client** — never skip a layer.

- **Entities:** read `coordinator.data` only, never call the API.
- **Coordinator:** calls the API, transforms the data, handles errors and timing.
- **API client:** HTTP communication, auth, exception translation.

✅ `self.coordinator.data.temperature` (in entity properties)

❌ `await self.api_client.get_data()` (never fetch directly in entities)

## API client

**Session management:**

- Accept an `aiohttp.ClientSession` parameter in `__init__`.
- Never create a session (`aiohttp.ClientSession()`) in the client.
- The session comes from `async_get_clientsession(hass)` in the integration's setup.

**Timeouts:** `asyncio.timeout()`, not `async_timeout`; a reasonable timeout per request (10–30 s typical).

**Return values:**

- Return raw API response data; let the coordinator transform it for entities.
- **Mirror the API's own structure**, even where it is badly designed or contains a typo. A client that "improves" the
  shape hides what the service actually returns, and the next reader cannot match it against the API docs.
- **Never convert units** (Celsius/Fahrenheit and friends). That decides precision and rounding on the caller's behalf;
  set `native_unit_of_measurement` on the entity and let Home Assistant convert.
- Implement pagination here — fetch all pages and hand the coordinator a complete dataset.

**A URL that points back at Home Assistant** — a webhook target, a device callback, a proxied image — comes from
`homeassistant.helpers.network.get_url(hass, ...)`. It knows about internal versus external, SSL, and Nabu Casa, none
of which can be reconstructed from `hass.config.internal_url`. It raises `NoURLAvailableError` when no suitable URL
exists; catch it rather than falling back to a guess.

**Webhooks** — the ID is the only secret a webhook has: generate it with `webhook.async_generate_id()`, never derive it
from the entry or device. Register with `local_only=True` whenever the caller is on the local network.

**Authentication:**

- The auth layer authenticates; it does not **store**. Persisting tokens is the config entry's job.
- Return tokens as JSON-serializable values (`str`, `int`, `float`, and dicts of those) so they survive being written
  into `entry.data`.
- With the OAuth2 helper, let its token errors (`OAuth2TokenRequestError` and subclasses,
  `ImplementationUnavailableError`) propagate — they already are `ConfigEntryNotReady` / `ConfigEntryAuthFailed`. Never
  wrap them in `UpdateFailed`, which would turn a reauth into an endless retry.
- A debug line that has to identify a key, token or account ID masks it with
  `homeassistant.helpers.redact.partial_redact()`.

**Do not** implement retry logic in the client, and do not catch `TimeoutError` / `aiohttp.ClientError` in the
coordinator — the coordinator base class already handles both.

## Exception hierarchy (required for an own client)

- `MyIntegrationApiClientError` (base)
- `MyIntegrationApiClientCommunicationError` (network, timeout, HTTP errors)
- `MyIntegrationApiClientAuthenticationError` (401, 403, invalid credentials)
- `MyIntegrationApiClientRateLimitError(retry_after)` (429), a subclass of the communication error, so code that only
  knows the base still catches it

**Mapping:** HTTP 401/403 → authentication, HTTP 429 → rate limit with the `Retry-After` seconds (a client default when
the header is missing or a date), timeout/`ClientError` → communication. A library client maps its own exceptions the
same way.

## Error handling in `_async_update_data()`

Translate API exceptions into Home Assistant ones here, and only here:

| API exception         | Raise                                       | Home Assistant behaviour    |
| --------------------- | ------------------------------------------- | --------------------------- |
| `AuthenticationError` | `ConfigEntryAuthFailed`                     | Triggers the reauth flow    |
| `RateLimitError`      | `UpdateFailed(retry_after=err.retry_after)` | Next poll waits that long   |
| `CommunicationError`  | `UpdateFailed("message")`                   | Retry at the usual interval |

A failure that will not resolve on its own — a closed account, unsupported firmware — raises `ConfigEntryError`, which
stops the retry loop.

Catch `RateLimitError` before the communication error it subclasses; Home Assistant honours `retry_after` during
`async_config_entry_first_refresh()` too. A rate limit outside the coordinator during setup raises
`ConfigEntryNotReady(retry_after=seconds)` instead. Bound the wait before passing it on — at least a few seconds, at
most the update interval — so `Retry-After: 0` does not poll in a loop and a huge value does not stop polling.

Use `raise ... from err`. Pass the error message to the exception constructor and **do not log** setup or update
failures manually — Home Assistant does it, and manual logging buries the real error in repetition. Normal operation
logging (debug/info) is still appropriate.

See [Integration setup failures](https://contributors.home-assistant.io/core/integrations/setup-failures/).

## Data transformation

`_async_update_data()` fetches the raw API data and transforms it into a shape entities read by key: entities read
`coordinator.data["temperature"]`, not `coordinator.data["sensors"]["temp"]["value"]`.

## Update interval

`super().__init__(hass, LOGGER, config_entry=entry, name="...", update_interval=timedelta(seconds=30))`

**Always pass `config_entry=`.** Omitting it makes the coordinator fall back to a ContextVar, which for a custom
integration is set to ignore the problem — so it fails silently rather than loudly.

Environmental sensors 30–60 s, energy 10–30 s, status 60–300 s, slow data 5–15 min. The floor Home Assistant accepts is
5 seconds. The interval is fixed in code, never a user option.

## Pull versus push

**Prefer push whenever the device or service offers it** — WebSocket, webhook, MQTT — and fall back to polling when the
protocol is proprietary, undocumented, or not worth the implementation effort.

- **Pull:** the coordinator handles everything via `update_interval`.
- **Push:** set up the coordinator-level listener in `async_setup_entry()` and call
  `coordinator.async_set_updated_data(new_data)` on events. Set `update_interval=None`, or keep a long one as a
  fallback for offline detection. A subscription held by an **entity** goes in `async_added_to_hass()` instead and is
  released via `self.async_on_remove(...)` — a disabled entity is never added, so subscribing at setup leaks.
- `async_set_updated_data()` on a polling coordinator also resets the timer until the next poll.

See [Fetching data](https://contributors.home-assistant.io/core/integrations/fetching-data/).

## First refresh

In `async_setup_entry()`: `await coordinator.async_config_entry_first_refresh()`. If `_async_update_data()` raises
`UpdateFailed`, it raises `ConfigEntryNotReady` automatically.

**When setup should not be retried at all**, use `await coordinator.async_refresh()` instead — it does not raise, so the
entry loads with entities in an unavailable state rather than going into the retry loop.

See [During setup](https://contributors.home-assistant.io/core/integrations/setup-failures/#during-setup).

## `always_update`

`always_update=True` (default) notifies entities of every refresh; `always_update=False` only when the data changed,
which requires `__eq__` on the data class.

## Caching API data

### In memory, to fetch less often than entities update

When the API's rate limit is stricter than the update need (1 request per 5 min, entities every 30 s), hold the payload
and its timestamp on the coordinator and return the cached copy from `_async_update_data()` while the TTL holds.

### Persisted, so the integration works without a connection at startup

Home Assistant restarts without internet more often than one would think — after a power cut it is regularly up before
the router is. `async_config_entry_first_refresh()` raises `ConfigEntryNotReady` when that first fetch fails, and then
**no entity exists at all**: exactly when the user most wants to see the last known values, the integration shows
nothing.

**First decide whether the cached payload is still true:**

| The payload…                                                                           | On a cold start with no network            |
| -------------------------------------------------------------------------------------- | ------------------------------------------ |
| Covers a defined period — today's electricity prices, a published forecast, a schedule | Restore it. It is complete and still valid |
| Is a point-in-time reading — a temperature, a power draw, an online/offline flag       | Do **not** restore it. It is stale         |

For the first kind:

- Persist the payload with `homeassistant.helpers.storage.Store` when a fetch succeeds, and load it in
  `async_setup_entry` before the first refresh. **Never write files into the integration's own folder**: every update
  replaces that folder. `Store` (in `.storage/`) is the only place.
- **Return the cached payload from `_async_update_data()` instead of raising `UpdateFailed`**, as long as it is inside
  its validity window. `CoordinatorEntity.available` is exactly `coordinator.last_update_success`, so raising
  `UpdateFailed` and merely leaving `coordinator.data` populated makes every entity unavailable.
- Once the window has passed, raise `UpdateFailed` as normal. Serving yesterday's prices as today's is worse than going
  unavailable.
- Log the fallback once at `info` level, so "still on cached data" is visible without spamming every poll.

The Bronze `test-before-setup` rule is satisfied either way: setup still fails loudly when there is nothing valid to
fall back on.

**Values that change with the clock need a scheduler, not a shorter interval.** A "current price" sensor derived from a
daily payload changes on the hour; fetch once per validity window and recompute locally with
`async_track_point_in_utc_time` / `async_track_time_change` — not polling every minute so the value happens to flip in
time, which is also what makes `appropriate-polling` look violated.

Entity-level state restoration (`RestoreSensor`, `RestoreEntity`) is a different mechanism: use it for a value the
entity accumulates itself, and `Store` for the payload the coordinator hands out.
