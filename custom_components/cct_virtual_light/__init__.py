"""
Virtual light integration to combine two lights as a single color changing tempereature (CCT) light within Home Assistant.

For more details about this integration, please refer to
https://github.com/mion00/cct-virtual-light
"""

from __future__ import annotations

import asyncio

import voluptuous as vol

from homeassistant.components.light import ATTR_COLOR_TEMP_KELVIN
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SOURCE,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_entity_registry_updated_event,
    async_track_state_added_domain,
    async_track_state_change_event,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import _DOMAIN_SCHEMA, DOMAIN, LOGGER
from .coordinator import BlueprintDataUpdateCoordinator

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [_DOMAIN_SCHEMA])}, extra=vol.ALLOW_EXTRA
)
"""Validate the configuration for this integration"""

PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the integration via YAML"""
    LOGGER.info("Setting up %s integration", DOMAIN)
    data = hass.data.setdefault(DOMAIN, {})

    for entry in config[DOMAIN]:
        LOGGER.debug("Forwarding setup to config entries")
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={CONF_SOURCE: SOURCE_IMPORT}, data=entry
            )
        )
        # hass.async_create_task(hass.helpers.discovery.async_load_platform(Platform.LIGHT, DOMAIN, light, config))
        # hass.async_create_task(hass.helpers.discovery.async_load_platform(Platform.SENSOR, DOMAIN, light, config))

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
