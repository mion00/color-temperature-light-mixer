"""Binary sensor platform for color_temperature_light_mixer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.color_temperature_light_mixer.const import PARALLEL_UPDATES as PARALLEL_UPDATES
from homeassistant.components.binary_sensor import BinarySensorEntityDescription

from .connectivity import ENTITY_DESCRIPTIONS as CONNECTIVITY_DESCRIPTIONS, ColorTemperatureMixerConnectivitySensor
from .filter import ENTITY_DESCRIPTIONS as FILTER_DESCRIPTIONS, ColorTemperatureMixerFilterSensor

if TYPE_CHECKING:
    from custom_components.color_temperature_light_mixer.data import ColorTemperatureMixerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    *CONNECTIVITY_DESCRIPTIONS,
    *FILTER_DESCRIPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ColorTemperatureMixerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    # Create connectivity sensors
    connectivity_entities = [
        ColorTemperatureMixerConnectivitySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in CONNECTIVITY_DESCRIPTIONS
    ]

    # Create filter sensors
    filter_entities = [
        ColorTemperatureMixerFilterSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in FILTER_DESCRIPTIONS
    ]

    # Add all entities
    async_add_entities([*connectivity_entities, *filter_entities])
