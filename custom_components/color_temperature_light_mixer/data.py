"""
Custom types for color_temperature_light_mixer.

This module defines the runtime data structure attached to each config entry.
Access pattern: entry.runtime_data.client / entry.runtime_data.coordinator

The ColorTemperatureMixerConfigEntry type alias is used throughout the integration
for type-safe access to the config entry's runtime data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import TYPE_CHECKING, Any, Self

from homeassistant.helpers.restore_state import ExtraStoredData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration


type ColorTemperatureMixerConfigEntry = ConfigEntry[ColorTemperatureMixerData]


@dataclass
class ColorTemperatureMixerData:
    """Runtime data for color_temperature_light_mixer config entries.

    Stored as entry.runtime_data after successful setup.
    Provides typed access to the API client and coordinator instances.
    """

    integration: Integration


@dataclass
class ChildLightState:
    """Information about a light entity used as a child in the the light group."""

    entity_id: str
    color_temp_kelvin: int
    brightness: int


@dataclass
class TurnOnSettings:
    """Options to pass to the light to be turned on."""

    entity_id: str
    common_data: dict[str, int]
    brightness: int | None = None


class BrightnessTemperaturePriority(StrEnum):
    """Enum that indicates what to prefer in the computation of the target brightness required to (temperature, brightness) target tuple."""

    BRIGHTNESS = auto()
    """Maintain the target brightness, at the expense of the temperature"""
    TEMPERATURE = auto()
    """Maintain the target temperature, at the expense of the brightness"""
    MIXED = auto()
    """Try to target a mix of both temperature and brightness"""


@dataclass
class ColorTemperatureMixerLightExtraStoredData(ExtraStoredData):
    """Object to hold extra stored data, used to keep track of most recent turned on state."""

    brightness: int | None
    color_temperature: int | None

    def as_dict(self) -> dict[str, int]:
        """Return a dict representation of the data."""
        return asdict(self)

    @classmethod
    def from_dict(cls, restored: dict[str, Any]) -> Self | None:
        """Initialize the stored state from a dict."""
        try:
            return cls(
                restored["color_temp_kelvin"],
                restored["brightness"],
            )
        except KeyError:
            return None
