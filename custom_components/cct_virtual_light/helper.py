from dataclasses import dataclass
from enum import StrEnum
import logging

from homeassistant.util.color import (
    color_temperature_kelvin_to_mired,
    rgbww_to_color_temperature,
)

_LOGGER = logging.getLogger(__name__)

# BRIGHTNESS_SCALE_FACTOR = 255 * 2
BRIGHTNESS_SOURCE_SCALE = (1, 255)
BRIGHTNESS_TARGET_SCALE = (1, 50)


class BrightnessTemperaturePreference(StrEnum):
    BRIGHTNESS = "Target the brightness, at the expense of the temperature"
    TEMPERATURE = "Target the temperature, at the expense of the brightness"
    MIXED = "Try to target a mix of both temperature and brightness"


@dataclass
class TurnOnSettings:
    entity_id: str
    data: dict[str, int] | None = None


@dataclass
class TemperatureCalculator:
    """Class for computing the temperature of two combined lights of different temperature"""

    warm_brightness: int
    """Brightness of the warm light in the range 1...255"""
    warm_temperature_kelvin: int
    """Temperature of the warm light in kelvin"""
    cold_brightness: int
    """Brightness of the cold light in the range 1...255"""
    cold_temperature_kelvin: int
    """Temperature of the cold light in kelvin"""

    def current_temperature(self) -> int:
        """Compute the current combined temperature"""
        # _LOGGER.debug("Brightness: w: %d, c: %d", self.warm_brightness, self.cold_brightness)
        # _LOGGER.debug("Temperature: w: %d, c: %d", self.warm_temperature_kelvin, self.cold_temperature_kelvin)

        combined_temperature, _ = rgbww_to_color_temperature(
            (0, 0, 0, self.cold_brightness, self.warm_brightness),
            self.warm_temperature_kelvin,
            self.cold_temperature_kelvin,
        )
        # _LOGGER.debug("Computed temperature: %f K", combined_temperature)

        # Clamp the temperature betwween min and maximum supported temperatures
        return max(
            self.warm_temperature_kelvin,
            min(self.cold_temperature_kelvin, combined_temperature),
        )


@dataclass
class BrightnessCalculator:
    """Class that given a target temperature and target, computes the brightness of the two combined lights"""

    warm_temperature_kelvin: int
    """Temperature of the warm light in kelvin"""
    cold_temperature_kelvin: int
    """Temperature of the cold light in kelvin"""

    target_temperature_kelvin: int
    """Target temperature in kelvin to reach"""
    target_brightness: int
    """Target brightness to reach in the range 1...255"""

    preferred_style: BrightnessTemperaturePreference
    """TODO"""

    def required_brightnesses(self) -> tuple[int, int]:
        """Compute the warm and cold light brightness.

        Returns:
            (warm, cold) brightness in range 1-255

        """

        _LOGGER.debug(
            "Computing brightness for temp: %d, bright: %d",
            self.target_temperature_kelvin,
            self.target_brightness,
        )

        # Convert ot mired to operate on a linear temperature space
        target_temperature_mired = color_temperature_kelvin_to_mired(
            self.target_temperature_kelvin
        )
        warm_temperature_mired = color_temperature_kelvin_to_mired(
            self.warm_temperature_kelvin
        )
        cold_temperature_mired = color_temperature_kelvin_to_mired(
            self.cold_temperature_kelvin
        )

        # Compute the half-point between the range of possible temperatures
        half_temperature_mired = (warm_temperature_mired - cold_temperature_mired) / 2

        # Flag that takes into account if the taret temperature is in the first or second half of the temperature range
        is_target_temp_warmer = target_temperature_mired > half_temperature_mired

        # TODO: define these as helper function
        # These functions are obtained by inverting the one defined in the util function `rgbww_to_color_temperature()`
        cold_brightness = round(
            (2 * self.target_brightness)
            * (target_temperature_mired - warm_temperature_mired)
            / (cold_temperature_mired - warm_temperature_mired)
        )
        warm_brightness = round(
            (2 * self.target_brightness)
            * (cold_temperature_mired - target_temperature_mired)
            / (cold_temperature_mired - warm_temperature_mired)
        )

        _LOGGER.debug(
            "Computed brightness, c: %d, w: %d", cold_brightness, warm_brightness
        )

        if cold_brightness > 255:
            match self.preferred_style:
                case BrightnessTemperaturePreference.BRIGHTNESS:
                    pass
                case BrightnessTemperaturePreference.TEMPERATURE:
                    pass
                case BrightnessTemperaturePreference.MIXED:
                    pass

        # Clamp brightness to acceptable ranges
        warm_brightness = min(warm_brightness, 255)
        cold_brightness = min(cold_brightness, 255)
        return warm_brightness, cold_brightness
