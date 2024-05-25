"""Light temperature mixer used to mix two lights of different temperature a single light group within Home Assistant.

For more details about this integration, please refer to
https://github.com/mion00/cct-virtual-light
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_SOURCE, Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import _DOMAIN_SCHEMA, DOMAIN, LOGGER

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [_DOMAIN_SCHEMA])}, extra=vol.ALLOW_EXTRA
)
"""Validate the configuration for this integration"""

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML."""
    LOGGER.info("Setting up %s integration", DOMAIN)

    for entry in config.get(DOMAIN, []):
        LOGGER.debug("Forwarding setup to config entries")
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={CONF_SOURCE: SOURCE_IMPORT}, data=entry
            )
        )

    return True


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using the UI."""

    data = hass.data.setdefault(DOMAIN, {})
    data.setdefault(entry.entry_id, {})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
