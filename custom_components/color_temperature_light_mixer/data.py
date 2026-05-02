"""
Custom types for color_temperature_light_mixer.

This module defines the runtime data structure attached to each config entry.
Access pattern: entry.runtime_data.client / entry.runtime_data.coordinator

The ColorTemperatureMixerConfigEntry type alias is used throughout the integration
for type-safe access to the config entry's runtime data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import ColorTemperatureMixerApiClient
    from .coordinator import ColorTemperatureMixerDataUpdateCoordinator


type ColorTemperatureMixerConfigEntry = ConfigEntry[ColorTemperatureMixerData]


@dataclass
class ColorTemperatureMixerData:
    """Runtime data for color_temperature_light_mixer config entries.

    Stored as entry.runtime_data after successful setup.
    Provides typed access to the API client and coordinator instances.
    """

    client: ColorTemperatureMixerApiClient
    coordinator: ColorTemperatureMixerDataUpdateCoordinator
    integration: Integration
