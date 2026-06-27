"""Light entity extending a light group to manage multiple light sources a single virtual one."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from typing import Any

from graphql import UndefinedType

from custom_components.color_temperature_light_mixer.const import (
    CONF_COLD_LIGHT,
    CONF_COLD_LIGHT_TEMPERATURE_KELVIN,
    CONF_WARM_LIGHT,
    CONF_WARM_LIGHT_TEMPERATURE_KELVIN,
    LOGGER,
)
from custom_components.color_temperature_light_mixer.data import (
    BrightnessTemperaturePriority,
    ChildLightState,
    ColorTemperatureMixerConfigEntry,
    ColorTemperatureMixerLightExtraStoredData,
    TurnOnSettings,
)
from custom_components.color_temperature_light_mixer.entity import ColorTemperatureMixerEntity
from custom_components.color_temperature_light_mixer.utils.calculator import BrightnessCalculator, TemperatureCalculator
from homeassistant.components.group.light import FORWARDED_ATTRIBUTES, LightGroup
from homeassistant.components.group.util import find_state_attributes
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN
from homeassistant.components.light.const import DOMAIN as DOMAIN_LIGHT, ColorMode
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON, STATE_ON
from homeassistant.core import State, callback
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.restore_state import RestoreEntity

ENTITY_DESCRIPTIONS = (
    EntityDescription(
        key="color_temperature_mixer",
        has_entity_name=True,
        name=None,  # This is the main feature of the device
    ),
)


class ColorTemperatureMixerLight(LightGroup, ColorTemperatureMixerEntity, RestoreEntity):
    """Light group that mixes a group of lights having different color temperatures."""

    # overridden in async_update_group_state()
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}

    __last_turned_on_brightness: int | None = None
    __last_turned_on_temperature: int | None = None

    def __init__(self, config_entry: ColorTemperatureMixerConfigEntry, entity_description: EntityDescription) -> None:
        """Initialize the CCT light group."""

        LightGroup.__init__(
            self,
            unique_id=config_entry.entry_id,
            name=None,  # pyright: ignore[reportArgumentType] Inherit device name, since it is the main feature of the device
            entity_ids=[config_entry.data[CONF_WARM_LIGHT], config_entry.data[CONF_COLD_LIGHT]],
            mode=False,
        )
        ColorTemperatureMixerEntity.__init__(
            self,
            config_entry=config_entry,
            entity_description=entity_description,
        )

        self._attr_min_color_temp_kelvin = config_entry.data[CONF_WARM_LIGHT_TEMPERATURE_KELVIN]
        self._attr_max_color_temp_kelvin = config_entry.data[CONF_COLD_LIGHT_TEMPERATURE_KELVIN]

        self.__warm_light: ChildLightState = ChildLightState(
            config_entry.data[CONF_WARM_LIGHT], config_entry.data[CONF_WARM_LIGHT_TEMPERATURE_KELVIN], 0
        )
        self.__cold_light: ChildLightState = ChildLightState(
            config_entry.data[CONF_COLD_LIGHT], config_entry.data[CONF_COLD_LIGHT_TEMPERATURE_KELVIN], 0
        )

    async def async_internal_added_to_hass(self) -> None:
        """
        Called when the CTML entity is added to hass.

        Read the previous turned on state from the restored state data, if available.
        """

        await super().async_internal_added_to_hass()

        if (
            (state := await self.async_get_last_state())
            and state.state is not None
            and (previous := await self.async_get_last_stored_data())
        ):
            LOGGER.debug("%s: restoring state data: %s", self._friendly_name(), previous)
            self.__last_turned_on_brightness = previous.brightness
            self.__last_turned_on_temperature = previous.color_temperature

        # Continue initialization of parent object
        await super().async_added_to_hass()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Given a combination of brightness or color_temp_kelvin, compute the required brightnesses for all the lights in the group."""
        LOGGER.debug("%s: turn on with params: %s", self._friendly_name(), kwargs)

        # Extract information about the target temperature and brightness passed as kwargs, if available.
        # Otherwise try to maintain the currently set temperature and brightness, restoring them from the dedicated sensor if unavailable locally
        target_brightness: int | None = kwargs.get(ATTR_BRIGHTNESS)
        target_temp_kelvin: int | None = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        # By default we prioritize both temp and brightness
        priority = BrightnessTemperaturePriority.MIXED
        if not any([target_brightness, target_temp_kelvin]):
            # If no brightness and temperature has been provided, fallback to their current value
            target_brightness = self.brightness
            target_temp_kelvin = self.color_temp_kelvin
        elif target_brightness is None:
            # If not provided in the service call, fallback to the current value of the light brightness and prioritize temperature
            target_brightness = self.brightness
            priority = BrightnessTemperaturePriority.TEMPERATURE
        elif target_temp_kelvin is None:
            # If not provided in the service call, fallback to the current value of the light temperature and prioritize brightness
            target_temp_kelvin = self.color_temp_kelvin
            priority = BrightnessTemperaturePriority.BRIGHTNESS

        # If one of the two parameter (brightness/temp) is undefined we cannot compute the target brightnesses for cold and warm child lights.
        # Try to read the missing value from our restored state, if available
        if target_brightness is None:  # and priority is not BrightnessTemperaturePriority.MIXED:
            target_brightness = self.__last_turned_on_brightness
            LOGGER.debug("%s: using last turned on brightness: %s", self._friendly_name(), target_brightness)
        if target_temp_kelvin is None:  # and priority is not BrightnessTemperaturePriority.MIXED:
            target_temp_kelvin = self.__last_turned_on_temperature
            LOGGER.debug("%s: using last turned on temperature: %s", self._friendly_name(), target_temp_kelvin)

        # Populate the base service data common to all the lights
        common_data = {key: value for key, value in kwargs.items() if key in FORWARDED_ATTRIBUTES}

        # If we are not able to identify both target_brightness and target_temp_kelvin,
        # we cannot properly compute the desired settings for each light, therefore do not alter the current brightness of each light
        if target_brightness is None or target_temp_kelvin is None:
            LOGGER.debug(
                "%s: cannot compute target state given target brightness: %d and temp: %d, turning on all lights without altering brightness",
                self._friendly_name(),
                target_brightness,
                target_temp_kelvin,
            )
            ww_settings = TurnOnSettings(self.__warm_light.entity_id, common_data)
            cw_settings = TurnOnSettings(self.__cold_light.entity_id, common_data)
            await self._turn_on_lights(ww_settings, cw_settings)
            return

        # Clamp between min and max possible temperatures
        target_temp_kelvin = min(
            self.__cold_light.color_temp_kelvin,
            max(target_temp_kelvin, self.__warm_light.color_temp_kelvin),
        )

        brightness_calculator = BrightnessCalculator(
            self.__warm_light.color_temp_kelvin,
            self.__cold_light.color_temp_kelvin,
            target_temp_kelvin,
            target_brightness,
            priority,
        )
        ww_brightness, cw_brightness = brightness_calculator.compute_brightnesses()

        # Personalize the service data with the light-specific brightness
        ww_settings = TurnOnSettings(self.__warm_light.entity_id, common_data.copy(), ww_brightness)
        cw_settings = TurnOnSettings(self.__cold_light.entity_id, common_data.copy(), cw_brightness)

        await self._turn_on_lights(ww=ww_settings, cw=cw_settings)

    async def _turn_on_lights(self, ww: TurnOnSettings, cw: TurnOnSettings) -> Awaitable:
        service_calls = []
        for light in (ww, cw):
            target = {ATTR_ENTITY_ID: light.entity_id}
            service_data = light.common_data

            if light.brightness is not None:
                service_data[ATTR_BRIGHTNESS] = light.brightness

            LOGGER.debug("%s: forwarding service turn_on call to: %s %s", self._friendly_name(), target, service_data)
            service_calls.append(
                self.hass.services.async_call(
                    DOMAIN_LIGHT,
                    SERVICE_TURN_ON,
                    target=target,
                    service_data=service_data,
                    blocking=False,
                    context=self._context,
                )
            )

        return asyncio.gather(*service_calls)

    @callback
    def async_update_group_state(self) -> None:
        """Customize method from parent class LightGroup to apply custom brightness and color temperature."""

        super().async_update_group_state()

        # Ensure COLOR_TEMP is always supported, since it is the main feature of the group
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}
        # Ensure COLOR_TEMP is always the current mode, since it is the main feature of the group
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_min_color_temp_kelvin = self.__warm_light.color_temp_kelvin
        self._attr_max_color_temp_kelvin = self.__cold_light.color_temp_kelvin
        states = [state for entity_id in self._entity_ids if (state := self.hass.states.get(entity_id)) is not None]
        on_states = [state for state in states if state.state == STATE_ON]

        brightnesses: list[int] = list(find_state_attributes(on_states, ATTR_BRIGHTNESS))

        self._attr_brightness = int(sum(brightnesses) / 2) if brightnesses else None
        self._attr_color_temp_kelvin = self._compute_color_temp_kelvin(on_states)

    def _compute_color_temp_kelvin(self, on_states: list[State]) -> int | None:
        """
        Compute the color temperature of the light group.

        Given the states containing the lights that are currently on,
        compute the combined temperature of the light group as a weighted average of the warm and cold lights temperatures.
        """

        # If no light is on, we are unable to compute the temperature
        if not on_states:
            return None

        def find_state(entity_id: str) -> State | None:
            return next(filter(lambda state: state.entity_id == entity_id, on_states), None)

        warm_light_state = find_state(self.__warm_light.entity_id)
        cold_light_state = find_state(self.__cold_light.entity_id)

        # Try to extract the brightness attribute if the light is on, otherwise fallback to 0
        self.__warm_light.brightness = (
            int(warm_light_state.attributes.get(ATTR_BRIGHTNESS, 0)) if warm_light_state is not None else 0
        )
        self.__cold_light.brightness = (
            int(cold_light_state.attributes.get(ATTR_BRIGHTNESS, 0)) if cold_light_state is not None else 0
        )

        temperature_calc = TemperatureCalculator(self.__warm_light, self.__cold_light)
        return temperature_calc.current_temperature()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Save the turned on state of each child light, and forward the turn_off command to all the lights in the light group."""
        # Save the current turned on state
        self._save_turned_on_state()

        LOGGER.debug("%s: invoking turn_off for the light group", self._friendly_name())
        await super().async_turn_off(**kwargs)

    def _save_turned_on_state(self):
        """Store the current turned on state in ad-hoc properties, so that it is possible to compute the temperature and brightness on the next turn request."""

        # Check that we have a value for both brightness and temperature before firing the signal
        if self.brightness is None or self.color_temp_kelvin is None:
            return

        # Store the state as a serialized JSON string
        LOGGER.debug(
            "%s: saving turned on state: bright: %d, temp: %d",
            self._friendly_name(),
            self.brightness,
            self.color_temp_kelvin,
        )

        self.__last_turned_on_brightness = self.brightness
        self.__last_turned_on_temperature = self.color_temp_kelvin

    async def async_get_last_stored_data(self) -> ColorTemperatureMixerLightExtraStoredData | None:
        """Restore CTML specific state date."""
        if (restored_last_extra_data := await self.async_get_last_extra_data()) is None:
            return None
        return ColorTemperatureMixerLightExtraStoredData.from_dict(restored_last_extra_data.as_dict())

    @property
    def extra_restore_state_data(self) -> ColorTemperatureMixerLightExtraStoredData:
        """Return integration specific state data to be restored."""
        return ColorTemperatureMixerLightExtraStoredData(
            self.__last_turned_on_brightness,
            self.__last_turned_on_temperature,
        )

    def _friendly_name(self) -> str:
        """Return the best available name to use in the log output."""

        return (
            self._cached_friendly_name[1]
            if self._cached_friendly_name and self._cached_friendly_name[1]
            else (
                self.name
                if self.name and type(self.name) is not UndefinedType
                else (self.entity_id or self.unique_id if self.unique_id else "unknown")
            )
        )  # pyright: ignore[reportReturnType] pyright does not correctly handles `type(self.name) is not UndefinedType`
