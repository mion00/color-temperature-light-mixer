# Import the device class from the component that you want to support
import asyncio
from collections.abc import Awaitable
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    DOMAIN as DOMAIN_LIGHT,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_UNIQUE_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_COLD_LIGHT,
    CONF_COLD_LIGHT_TEMPERATURE_KELVIN,
    CONF_WARM_LIGHT,
    CONF_WARM_LIGHT_TEMPERATURE_KELVIN,
    DISPATCHER_SIGNAL_TURN_OFF,
    DOMAIN,
)
from .helper import (
    BrightnessCalculator,
    BrightnessTemperaturePreference,
    TemperatureCalculator,
    TurnOnSettings,
)

_LOGGER = logging.getLogger(__name__)

# INNER_LIGHT_SCHEMA = {
#     vol.Required(CONF_ENTITY_ID): cv.entity_id,
#     vol.Required(ATTR_COLOR_TEMP_KELVIN): vol.Range(min=0),
# }

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         vol.Required(CONF_NAME): cv.string,
#         vol.Required(CONF_WARM_LIGHT): INNER_LIGHT_SCHEMA,
#         vol.Required(CONF_COLD_LIGHT): INNER_LIGHT_SCHEMA,
#     }
# )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
):
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    config = entry.as_dict()["data"]

    light = CCTVirtualLight(
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


# async def async_setup_platform(
#     hass: HomeAssistant,
#     config: ConfigType,
#     async_add_entities: AddEntitiesCallback,
#     discovery_info: DiscoveryInfoType | None = None,
# ) -> None:
#     """Set up the CCT virtual light platform"""

#     _LOGGER.debug("Setting up light platform")

#     # If the entities was loaded from __init__.py, we have the discovery info
#     if discovery_info:
#         cct_light = CCTVirtualLight(
#             discovery_info[CONF_NAME],
#             discovery_info[CONF_WARM_LIGHT],
#             discovery_info[CONF_COLD_LIGHT],
#         )
#     else:
#         cct_light = CCTVirtualLight(
#             config[CONF_NAME], config[CONF_WARM_LIGHT], config[CONF_COLD_LIGHT]
#         )

#     # Add created entities to HA
#     async_add_entities((cct_light,))


class CCTVirtualLight(LightEntity):
    """Virtual color changing temperature light"""

    # Our state depends only on the state of the other two ligths
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_name = None  # This is the main feature of the service
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = set((ColorMode.COLOR_TEMP,))

    def __init__(
        self,
        name: str,
        warm_light: dict[str, Any],
        cold_light: dict[str, Any],
        config_id: str,
    ) -> None:
        self._attr_unique_id = config_id
        self._attr_device_info = DeviceInfo(
            identifiers=set([(DOMAIN, config_id)]),
            entry_type=DeviceEntryType.SERVICE,
            name=name,
        )
        self.warm_light = warm_light
        self.cold_light = cold_light
        self.state_change_unsub: CALLBACK_TYPE | None = None

    @property
    def available(self) -> bool | None:
        # _LOGGER.debug("Checking if light is available")
        is_warm_available = self.hass.states.get(self.warm_light[ATTR_ENTITY_ID])
        is_cold_available = self.hass.states.get(self.cold_light[ATTR_ENTITY_ID])

        # Neither of the lights must be unavailable
        return (
            is_warm_available and is_warm_available.state != STATE_UNAVAILABLE
        ) and (is_cold_available and is_cold_available.state != STATE_UNAVAILABLE)

    @property
    def is_on(self) -> bool | None:
        # _LOGGER.debug("%s: checking if light is on", self._friendly_name_internal())

        warm_light_state = self.hass.states.get(self.warm_light[ATTR_ENTITY_ID])
        cold_light_state = self.hass.states.get(self.cold_light[ATTR_ENTITY_ID])

        is_warm_on = warm_light_state and warm_light_state.state == STATE_ON
        is_cold_on = cold_light_state and cold_light_state.state == STATE_ON

        # If both lights are off -> we are also off, so fire the event to save our state
        if not is_warm_on and not is_cold_on:
            # _LOGGER.debug("%s: light is off", self._friendly_name_internal())
            self._fire_turn_off_signal()

        # Light is on if either one of the two lights is on
        return is_warm_on or is_cold_on

    @property
    def brightness(self) -> int | None:
        # _LOGGER.debug("%s: computing brightness", self._friendly_name_internal())

        brightnesses = self._get_brightnesses()

        if brightnesses is None:
            return None

        # Computed the sum of each light brightness, then divide by two since the contribution of each single light is half
        total_brightness = sum(brightnesses) / 2

        return round(total_brightness)

    @property
    def color_temp_kelvin(self) -> int | None:
        brightnesses = self._get_brightnesses()
        if brightnesses is None:
            return None

        temperature_calc = TemperatureCalculator(
            brightnesses[0],
            self.warm_light[ATTR_COLOR_TEMP_KELVIN],
            brightnesses[1],
            self.cold_light[ATTR_COLOR_TEMP_KELVIN],
        )
        computed_temp = temperature_calc.current_temperature()
        # _LOGGER.debug("Computed temp: %d", computed_temp)

        return computed_temp

    @property
    def min_color_temp_kelvin(self) -> int:
        """User-configured color temperature of the warmest light"""
        return int(self.warm_light[ATTR_COLOR_TEMP_KELVIN])

    @property
    def max_color_temp_kelvin(self) -> int:
        """User-configured color temperature of the coolest light"""
        return int(self.cold_light[ATTR_COLOR_TEMP_KELVIN])

    async def async_turn_on(self, **kwargs):
        """Turn the light on"""

        _LOGGER.debug("%s: turn on params: %s", self._friendly_name_internal(), kwargs)

        # Extract information about the target temperature and brightness to be reached, if provided to,
        # otherwise try to maintain the currently set temperature and brightness, if possible
        target_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN, self.color_temp_kelvin)
        target_brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness)

        # If one of the two parameter is undefined, we cannot properly computed the target brightness,
        # so fallback to simply turning on each light, without specifying any setting
        if target_brightness is None or target_temp_kelvin is None:
            _LOGGER.debug(
                "%s: no state available, turning all each light to its default state",
                self._friendly_name_internal,
            )
            ww_settings = TurnOnSettings(self.warm_light[CONF_ENTITY_ID])
            cw_settings = TurnOnSettings(self.cold_light[CONF_ENTITY_ID])
            await self._turn_on_lights(ww_settings, cw_settings)

            # Wait for time for the state of the two lights to update
            await asyncio.sleep(0.1)

            # Now we should have the state of each light and are able to properly compute temperature and brightness
            target_temp_kelvin = kwargs.get(
                ATTR_COLOR_TEMP_KELVIN, self.color_temp_kelvin
            )
            target_brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness)

        brightness_calculator = BrightnessCalculator(
            self.min_color_temp_kelvin,
            self.max_color_temp_kelvin,
            target_temp_kelvin,
            target_brightness,
            BrightnessTemperaturePreference.BRIGHTNESS,
        )
        ww_brightness, cw_brightness = brightness_calculator.required_brightnesses()

        # Turn on the two lights with the computed brightness for each
        ww_settings = TurnOnSettings(
            self.warm_light[CONF_ENTITY_ID], {ATTR_BRIGHTNESS: ww_brightness}
        )
        cw_settings = TurnOnSettings(
            self.cold_light[CONF_ENTITY_ID], {ATTR_BRIGHTNESS: cw_brightness}
        )
        # await self._turn_on_lights(ww_settings, cw_settings)

    async def async_turn_off(self, **kwargs):
        """Turn the light off"""

        self._fire_turn_off_signal()

        target = {
            ATTR_ENTITY_ID: [
                self.warm_light[ATTR_ENTITY_ID],
                self.cold_light[ATTR_ENTITY_ID],
            ]
        }
        # Shut off both lights
        await self.hass.services.async_call(
            DOMAIN_LIGHT, SERVICE_TURN_OFF, target=target
        )

    def _fire_turn_off_signal(self):
        """Fire a signal to keep track of the brightness and temperature in separate sensors before we turn off"""
        # Check that we have a value for both brigthness and temperature before firing the signal
        if self.brightness is None or self.color_temp_kelvin is None:
            return

        signal_data = {
            CONF_UNIQUE_ID: self.unique_id,
            ATTR_ENTITY_ID: self.entity_id,
            ATTR_BRIGHTNESS: self.brightness,
            ATTR_COLOR_TEMP_KELVIN: self.color_temp_kelvin,
        }
        _LOGGER.debug("%s: firing turn off signal", self._friendly_name_internal())
        async_dispatcher_send(self.hass, DISPATCHER_SIGNAL_TURN_OFF, signal_data)

    async def async_added_to_hass(self):
        """Subscribe to state change events from the two source lights"""
        _LOGGER.debug("%s: start listening for events", self._friendly_name_internal())

        self.hass.data[DOMAIN].setdefault(
            self._friendly_name_internal(), self.entity_id
        )

        tracked_lights = [
            self.warm_light[ATTR_ENTITY_ID],
            self.cold_light[ATTR_ENTITY_ID],
        ]
        self.state_change_unsub = async_track_state_change_event(
            self.hass, tracked_lights, self.on_real_lights_state_changed
        )

    async def async_will_remove_from_hass(self):
        """Remove the subscription"""

        if self.state_change_unsub:
            _LOGGER.debug(
                "%s: cancelling subscription to lights state change",
                self._name_internal,
            )
            self.state_change_unsub()

    @callback
    async def on_real_lights_state_changed(self, event: Event[EventStateChangedData]):
        """Callback for when any of the monitored light changes state"""
        self.async_schedule_update_ha_state()

    def _get_brightnesses(self) -> list[int] | None:
        """Extract from the state of the lights their brightness value, checking for None and falling back to value 0.

        Return the values in the form `[warm_brightness, cold_brightness]`
        """

        warm_light = self.hass.states.get(self.warm_light[ATTR_ENTITY_ID])
        cold_light = self.hass.states.get(self.cold_light[ATTR_ENTITY_ID])

        # Extract the brightness attribute making sure that the attribute exists
        warm_brightness = (
            warm_light.attributes.get("brightness")
            if (warm_light and warm_light.attributes)
            else None
        )
        cold_brightness = (
            cold_light.attributes.get("brightness")
            if (cold_light and cold_light.attributes)
            else None
        )

        # If both brightness are None, set it ot None as well
        if warm_brightness is None and cold_brightness is None:
            return None

        # Convert the brightnesses to an integer, or fallback to 0 if it is not defined (the light may be unavailable or shutoff)
        brightnesses = list(
            map(lambda x: int(x or 0), [warm_brightness, cold_brightness])
        )

        # _LOGGER.debug("Brightnesses w: %d, c: %d", *brightnesses)
        return brightnesses

    async def _turn_on_lights(
        self, ww: TurnOnSettings, cw: TurnOnSettings
    ) -> Awaitable:
        service_calls = []
        for light in (ww, cw):
            target = {ATTR_ENTITY_ID: light.entity_id}
            data = (
                {attribute: light.data[attribute] for attribute in light.data}
                if light.data
                else None
            )
            service_calls.append(
                self.hass.services.async_call(
                    DOMAIN_LIGHT, SERVICE_TURN_ON, target=target, service_data=data
                )
            )

        return asyncio.gather(*service_calls)
