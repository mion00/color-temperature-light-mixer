---
name: "Home Assistant diagnostics"
description: "Redacting credentials and personal data from config entry and device diagnostics"
applyTo: "custom_components/**/diagnostics.py"
paths:
  - "custom_components/**/diagnostics.py"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-build/skills/haci-coordinator-debug/references/rules.diagnostics.md sha256:5fa758b83203f9d1 — written by script/haci-vendor, do not edit -->

# Diagnostics rules

Procedure: the `haci-coordinator-debug` skill (plugin `haci-build`) — reading the diagnostics of a running instance,
and checking a payload against them after a fix.

Upstream: [Integration diagnostics](https://contributors.home-assistant.io/core/integrations/diagnostics/).

## Always redact sensitive data

Run everything that holds user data through `async_redact_data()`:

```python
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.redact import async_redact_data

TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
    "api_key",
    "token",
    "refresh_token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MyIntegrationConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.coordinator

    return {
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "entry_options": async_redact_data(entry.options, TO_REDACT),
        "coordinator_data": async_redact_data(coordinator.data, TO_REDACT),
    }
```

**The coordinator data is redacted too.** An API payload usually holds more than the entities show — serials,
coordinates, account names — and users post this file in public issues. Read the real output once, not just the code.

A device or entity registry entry goes in through `device_entry_as_dict()` / `entity_entry_as_dict()` from
`homeassistant.components.diagnostics`, which leave out the registry's internal fields. Where an identifier has to stay
recognisable, `homeassistant.helpers.redact.partial_redact()` masks all but its first and last characters.

## Device-level diagnostics

A second, optional entry point, `async_get_device_diagnostics(hass, entry, device)`. Implement it when a single device's
data is worth downloading on its own; without it, the device page offers the config entry diagnostics instead. Either
function may exist on its own, or both together. Redaction rules are identical.

## Never expose

- Passwords
- API keys and tokens (`access_token`, `refresh_token`, `api_key`, …)
- OAuth credentials
- Location data (latitude/longitude)
- Personal information (email, phone, name)
- Device serial numbers, where they are sensitive
- MAC addresses (`format_mac` if one is needed for identification)

If you are unsure whether data is sensitive, **redact it**.

## Testing

Cover the output with a snapshot test, so every change to it shows up in review:
`get_diagnostics_for_config_entry` / `get_diagnostics_for_device` from
`pytest_homeassistant.components.diagnostics` return exactly what a user downloads. Read the snapshot for anything
that should have been redacted before committing it — procedure in `haci-testing` (plugin `haci-quality`).
