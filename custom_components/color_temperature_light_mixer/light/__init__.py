"""Light platform for color_temperature_light_mixer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .color_temperature_mixer import ENTITY_DESCRIPTIONS, ColorTemperatureMixerLight

if TYPE_CHECKING:
    from custom_components.color_temperature_light_mixer.data import ColorTemperatureMixerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity import EntityDescription
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[EntityDescription, ...] = (*ENTITY_DESCRIPTIONS,)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ColorTemperatureMixerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light group platform."""
    async_add_entities(
        ColorTemperatureMixerLight(
            config_entry=entry,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )
