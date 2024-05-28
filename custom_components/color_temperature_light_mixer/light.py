"""Light platform."""

import asyncio
from collections.abc import Awaitable
import json
import logging
from typing import Any

from homeassistant.components.group.light import FORWARDED_ATTRIBUTES, LightGroup
from homeassistant.components.group.util import find_state_attributes
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    DOMAIN as DOMAIN_LIGHT,
    ColorMode,
)
from homeassistant.components.sensor import RestoreSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITY_ID,
    CONF_NAME,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_COLD_LIGHT,
    CONF_COLD_LIGHT_TEMPERATURE_KELVIN,
    CONF_WARM_LIGHT,
    CONF_WARM_LIGHT_TEMPERATURE_KELVIN,
    DOMAIN,
)
from .helper import (
    BrightnessCalculator,
    BrightnessTemperaturePriority,
    TemperatureCalculator,
    TurnOnSettings,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
):
    """Set up the sensor platform."""
    config = entry.as_dict()["data"]

    light = TemperatureMixerLight(
        name=config[CONF_NAME],
        warm_light={
            CONF_ENTITY_ID: config[CONF_WARM_LIGHT],
            ATTR_COLOR_TEMP_KELVIN: config[CONF_WARM_LIGHT_TEMPERATURE_KELVIN],
        },
        cold_light={
            CONF_ENTITY_ID: config[CONF_COLD_LIGHT],
            ATTR_COLOR_TEMP_KELVIN: config[CONF_COLD_LIGHT_TEMPERATURE_KELVIN],
        },
        config_id=entry.entry_id,
    )

    async_add_devices([light])


class TemperatureMixerLight(LightGroup, RestoreSensor):
    """Light group that mixes a group of lights having different color temperature."""

    _attr_has_entity_name = True
    _attr_name = None  # This is the main feature of the service

    def __init__(
        self,
        name: str,
        warm_light: dict[str, Any],
        cold_light: dict[str, Any],
        config_id: str,
    ) -> None:
        """Initialize the CCT light."""
        self._attr_unique_id = config_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=name,
        )
        super().__init__(
            unique_id=self.unique_id,
            name=None,  # type: ignore
            entity_ids=[warm_light[ATTR_ENTITY_ID], cold_light[ATTR_ENTITY_ID]],
            mode=False,
        )
        self._attr_min_color_temp_kelvin = warm_light[ATTR_COLOR_TEMP_KELVIN]
        self._attr_max_color_temp_kelvin = cold_light[ATTR_COLOR_TEMP_KELVIN]
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_supported_color_modes = {ColorMode.COLOR_TEMP}

        self.warm_light = warm_light
        self.cold_light = cold_light
        self.config_id = config_id
        self.previous_turn_on_state = (
            {}
        )  # Initialize previous state to empty to avoid None

    async def async_added_to_hass(self) -> None:
        """Read the previous turn_on state from the restore data, if available."""
        restored_data = await self.async_get_last_sensor_data()
        # Deserialized the saved state from JSON, if available
        if restored_data and restored_data.native_value:
            serialized_state: str = restored_data.native_value  # type: ignore -> we know it is as string
            self.previous_turn_on_state = json.loads(serialized_state)
            _LOGGER.debug(
                "%s: restoring previous_turn_on_state: %s",
                self._friendly_name_internal(),
                self.previous_turn_on_state,
            )

        # Continue initialization of parent object
        await super().async_added_to_hass()

    @callback
    def async_update_group_state(self) -> None:
        """Update the state of the light group."""
        states = {
            entity_id: state
            for entity_id in self._entity_ids
            if (state := self.hass.states.get(entity_id)) is not None
        }
        # Filter for states that are on
        on_states = {
            state: value for (state, value) in states.items() if value.state == STATE_ON
        }

        valid_state = self.mode(
            state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE)
            for state in states.values()
        )

        if not valid_state:
            # Set as unknown if any / all member is unknown or unavailable
            self._attr_is_on = None
        else:
            # Set as ON if any / all member is ON
            self._attr_is_on = self.mode(
                state.state == STATE_ON for state in states.values()
            )

        self._attr_available = any(
            state.state != STATE_UNAVAILABLE for state in states.values()
        )

        brightnesses: list[int] = list(
            find_state_attributes(list(on_states.values()), ATTR_BRIGHTNESS)
        )
        self._attr_brightness = int(sum(brightnesses) / 2) if brightnesses else None
        self._attr_color_temp_kelvin = self._compute_color_temp_kelvin(on_states)

    def _compute_color_temp_kelvin(self, on_states: dict[str, State]) -> int | None:
        """Given the dictionary of states containing the lights that are currently on, compute the combined temperature of the light group as a weighted average of the two lights temperatures."""
        # If no light is on, we are unable to compute the temperature
        if not on_states:
            return

        warm_light_state = on_states.get(self.warm_light[ATTR_ENTITY_ID])
        cold_light_state = on_states.get(self.cold_light[ATTR_ENTITY_ID])

        # Try to extract the brightness attribute if the light is on, otherwise fallback to 0
        self.warm_light[ATTR_BRIGHTNESS] = (
            int(warm_light_state.attributes.get(ATTR_BRIGHTNESS, 0))
            if warm_light_state is not None
            else 0
        )
        self.cold_light[ATTR_BRIGHTNESS] = (
            int(cold_light_state.attributes.get(ATTR_BRIGHTNESS, 0))
            if cold_light_state is not None
            else 0
        )

        temperature_calc = TemperatureCalculator(
            self.warm_light[ATTR_BRIGHTNESS],
            self.warm_light[ATTR_COLOR_TEMP_KELVIN],
            self.cold_light[ATTR_BRIGHTNESS],
            self.cold_light[ATTR_COLOR_TEMP_KELVIN],
        )
        computed_temp = temperature_calc.current_temperature()

        return computed_temp

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Given a combination of brightness or color_temp_kelvin, compute the required brightnesses for all the lights in the group."""
        _LOGGER.debug(
            "%s: turn on with params: %s", self._friendly_name_internal(), kwargs
        )

        # Extract information about the target temperature and brightness passed as kwargs, if available.
        # Otherwise try to maintain the currently set temperature and brightness, restoring them from the dedicated sensors if unavailable locally
        target_brightness = kwargs.get(ATTR_BRIGHTNESS)
        target_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

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

        # If one of the two parameter (brightness/temp) is undefined,
        # it means we do not have a state to fallback to, so read the values from our fallback state, if available
        if target_brightness is None:
            target_brightness = self.previous_turn_on_state.get(ATTR_BRIGHTNESS)
            _LOGGER.debug(
                "%s: using previous brightness: %s",
                self._friendly_name_internal(),
                target_brightness,
            )
        if target_temp_kelvin is None:
            target_temp_kelvin = self.previous_turn_on_state.get(ATTR_COLOR_TEMP_KELVIN)
            _LOGGER.debug(
                "%s: using previous temperature: %s",
                self._friendly_name_internal(),
                target_temp_kelvin,
            )

        # Populate the base service data common to all the lights
        common_data = {
            key: value for key, value in kwargs.items() if key in FORWARDED_ATTRIBUTES
        }

        if not all([target_brightness, target_temp_kelvin]):
            _LOGGER.debug(
                "%s: no restored state available, turning all each light to its default state",
                self._friendly_name_internal(),
            )
            ww_settings = TurnOnSettings(self.warm_light[CONF_ENTITY_ID], common_data)
            cw_settings = TurnOnSettings(self.cold_light[CONF_ENTITY_ID], common_data)
            await self._turn_on_lights(ww_settings, cw_settings)
            return

        # Clamp between min and max possible temperatures
        target_temp_kelvin = min(
            self.cold_light[ATTR_COLOR_TEMP_KELVIN],
            max(target_temp_kelvin, self.warm_light[ATTR_COLOR_TEMP_KELVIN]),
        )

        brightness_calculator = BrightnessCalculator(
            self.min_color_temp_kelvin,
            self.max_color_temp_kelvin,
            target_temp_kelvin,  # type: ignore
            target_brightness,  # type: ignore
            priority,
        )
        ww_brightness, cw_brightness = brightness_calculator.compute_brightnesses()

        # Personalize the service data with the light-specific brightness
        ww_settings = TurnOnSettings(
            self.warm_light[CONF_ENTITY_ID], common_data.copy(), ww_brightness
        )
        cw_settings = TurnOnSettings(
            self.cold_light[CONF_ENTITY_ID], common_data.copy(), cw_brightness
        )

        await self._turn_on_lights(ww=ww_settings, cw=cw_settings)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Forward the turn_off command to all the lights in the light group."""
        # Save our turned on state
        self._save_turn_on_state()

        _LOGGER.debug(
            "%s: invoking turn_off for the light group", self._friendly_name_internal()
        )
        await super().async_turn_off(**kwargs)

    def _save_turn_on_state(self):
        """Store the turned on state as a serialized JSON string, to read it in case HA restarts."""
        # Check that we have a value for both brightness and temperature before firing the signal
        if self.brightness is None or self.color_temp_kelvin is None:
            return
        _LOGGER.debug("%s: saving serialized state", self._friendly_name_internal())

        # Store the state as a serialized JSON string
        serialized_state = {
            ATTR_BRIGHTNESS: self.brightness,
            ATTR_COLOR_TEMP_KELVIN: self.color_temp_kelvin,
        }
        self._attr_native_value = json.dumps(serialized_state)

    async def _turn_on_lights(
        self, ww: TurnOnSettings, cw: TurnOnSettings
    ) -> Awaitable:
        service_calls = []
        for light in (ww, cw):
            target = {ATTR_ENTITY_ID: light.entity_id}
            service_data = light.common_data

            if light.brightness is not None:
                service_data[ATTR_BRIGHTNESS] = light.brightness

            _LOGGER.debug(
                "%s: forward turn_on: %s %s",
                self._friendly_name_internal(),
                target,
                service_data,
            )
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
