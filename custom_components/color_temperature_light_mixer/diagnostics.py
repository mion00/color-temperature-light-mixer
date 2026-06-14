"""Diagnostics support for color_temperature_light_mixer.

Learn more about diagnostics:
https://developers.home-assistant.io/docs/core/integration_diagnostics
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.redact import async_redact_data

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ColorTemperatureMixerConfigEntry

# Fields to redact from diagnostics - CRITICAL for security!
TO_REDACT = {
    CONF_PASSWORD,
    CONF_USERNAME,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ColorTemperatureMixerConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    integration = entry.runtime_data.integration

    # Get device and entity information
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    # Find all devices for this integration
    devices = dr.async_entries_for_config_entry(device_reg, entry.entry_id)
    device_info = []
    for device in devices:
        entities = er.async_entries_for_device(entity_reg, device.id)
        device_info.append(
            {
                "id": device.id,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "sw_version": device.sw_version,
                "entity_count": len(entities),
                "entities": [
                    {
                        "entity_id": entity.entity_id,
                        "platform": entity.platform,
                        "original_name": entity.original_name,
                        "disabled": entity.disabled,
                        "disabled_by": entity.disabled_by.value if entity.disabled_by else None,
                    }
                    for entity in entities
                ],
            }
        )

    # Integration information
    integration_info = {
        "name": integration.name,
        "version": integration.version,
        "domain": integration.domain,
        "documentation": integration.documentation,
        "issue_tracker": integration.issue_tracker,
    }

    # Config entry details (with redacted sensitive data)
    entry_info = {
        "entry_id": entry.entry_id,
        "version": entry.version,
        "minor_version": entry.minor_version,
        "domain": entry.domain,
        "title": entry.title,
        "state": str(entry.state),
        "unique_id": entry.unique_id,
        "disabled_by": entry.disabled_by.value if entry.disabled_by else None,
        "data": async_redact_data(entry.data, TO_REDACT),
        "options": async_redact_data(entry.options, TO_REDACT),
    }

    return {"entry": entry_info, "integration": integration_info, "devices": device_info}
