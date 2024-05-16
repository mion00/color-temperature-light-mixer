"""Sensor platform for integration_blueprint."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import RestoreSensor, SensorEntityDescription
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_BRIGHTNESS,
    CONF_NAME,
    CONF_SENSOR_TYPE,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_COLD_LIGHT, CONF_WARM_LIGHT, DOMAIN

_LOGGER = logging.getLogger(__name__)


ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key=DOMAIN,
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the CCT plattform sensors"""

    _LOGGER.debug(config)
    if config[CONF_SENSOR_TYPE] == "brightness":
        _LOGGER.debug("Setting up %s platform brightness sensor", DOMAIN)
        brightness_sensor = CCTBrightnessSensor(
            entity_description=ENTITY_DESCRIPTIONS[0],
            name=config[CONF_NAME],
            warm_light=config[CONF_WARM_LIGHT],
            cold_light=config[CONF_COLD_LIGHT],
        )

        # Add devices
        async_add_entities((brightness_sensor,))


# async def async_setup_entry(hass, entry, async_add_devices):
#     """Set up the sensor platform."""
#     coordinator = hass.data[DOMAIN][entry.entry_id]
#     async_add_devices(
#         CCTBrightnessSensor(
#             entity_description=entity_description,
#             name="Brightness"
#         )
#         for entity_description in ENTITY_DESCRIPTIONS
#     )


class CCTBrightnessSensor(RestoreSensor):
    """integration_blueprint Sensor class."""

    _attr_has_entity_name = True
    _attr_device_class = None
    _attr_should_poll = False

    def __init__(
        self,
        entity_description: SensorEntityDescription,
        name: str,
        warm_light: dict[str, Any],
        cold_light: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self.warm_light = warm_light
        self.cold_light = cold_light
        # index the lights by entity_id to quickly reference them from the event handler
        self.ligths = {
            warm_light[ATTR_ENTITY_ID]: self.warm_light,
            cold_light[ATTR_ENTITY_ID]: self.cold_light,
        }

    async def async_added_to_hass(self):
        """Restore the previous state if available, then subscribe to state change events from the two sub-lights"""

        restored_state = await self.async_get_last_sensor_data()

        # Restore the previous state if it is not None
        if (
            restored_state is not None
            and restored_state.as_dict()["native_value"] is not None
        ):
            self._attr_native_value = restored_state.as_dict()["native_value"]
            _LOGGER.debug("Restored previous state: %s", restored_state)

        # Track the state of the two lights
        tracked_lights = [
            self.warm_light[ATTR_ENTITY_ID],
            self.cold_light[ATTR_ENTITY_ID],
        ]
        _LOGGER.debug("Start listening for events")
        self.state_change_unsub = async_track_state_change_event(
            self.hass, tracked_lights, self.on_real_lights_state_changed
        )

    @callback
    async def on_real_lights_state_changed(self, event: Event[EventStateChangedData]):
        """Callback for when any of the monitored light changes state.
        Compute the combined brightness as the mean of the two brightness.

        Update our state iff the resulting brightness != 0, so we always know the last brightness that we had.
        """
        event_dict = event.as_dict()

        # Extract the brightness attribute from the new state, and keep track of it
        # _LOGGER.debug("Event %s", event_dict)
        event_type = event_dict["event_type"]
        entity_id = event_dict["data"][ATTR_ENTITY_ID]
        new_state = event_dict["data"].get("new_state")
        brightness = (
            new_state.attributes.get(CONF_BRIGHTNESS)
            if new_state and new_state.attributes
            else None
        )

        # _LOGGER.debug("%s entity: %s brightness: %s", event_type, entity_id, brightness)

        # Keep track of the brightness of the light as an attribute in the lights dict
        self.ligths[entity_id][CONF_BRIGHTNESS] = brightness

        # Compute our brightness as the average brightness of the two lights, defaulting to 0 if is None (meaning light is off)
        combined_brightness = round(
            sum(int(light.get(CONF_BRIGHTNESS) or 0) for light in self.ligths.values())
            / 2
        )

        # Update our state iff the brightness is not 0 (meaning all lights are off).
        # This way we can always fallback to a known brightness when HA starts up
        if combined_brightness != 0:
            _LOGGER.debug("Computed brightness %d != 0", combined_brightness)
            self._attr_native_value = combined_brightness
            self.async_schedule_update_ha_state()
