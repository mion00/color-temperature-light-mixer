"""Sensor platform for color_temperature_light_mixer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.color_temperature_light_mixer.const import PARALLEL_UPDATES as PARALLEL_UPDATES
from homeassistant.components.sensor import SensorEntityDescription

from .air_quality import ENTITY_DESCRIPTIONS as AIR_QUALITY_DESCRIPTIONS, ColorTemperatureMixerAirQualitySensor
from .diagnostic import ENTITY_DESCRIPTIONS as DIAGNOSTIC_DESCRIPTIONS, ColorTemperatureMixerDiagnosticSensor

if TYPE_CHECKING:
    from custom_components.color_temperature_light_mixer.data import ColorTemperatureMixerConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

# Combine all entity descriptions from different modules
ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    *AIR_QUALITY_DESCRIPTIONS,
    *DIAGNOSTIC_DESCRIPTIONS,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ColorTemperatureMixerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # Add air quality sensors
    async_add_entities(
        ColorTemperatureMixerAirQualitySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in AIR_QUALITY_DESCRIPTIONS
    )
    # Add diagnostic sensors
    async_add_entities(
        ColorTemperatureMixerDiagnosticSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in DIAGNOSTIC_DESCRIPTIONS
    )
