"""Number platform for color_temperature_light_mixer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.color_temperature_light_mixer.const import PARALLEL_UPDATES as PARALLEL_UPDATES
from homeassistant.components.number import NumberEntityDescription

from .target_humidity import ENTITY_DESCRIPTIONS as HUMIDITY_DESCRIPTIONS, ColorTemperatureMixerHumidityNumber

if TYPE_CHECKING:
    from custom_components.color_temperature_light_mixer.data import ColorTemperatureMixerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[NumberEntityDescription, ...] = (*HUMIDITY_DESCRIPTIONS,)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ColorTemperatureMixerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    async_add_entities(
        ColorTemperatureMixerHumidityNumber(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in HUMIDITY_DESCRIPTIONS
    )
