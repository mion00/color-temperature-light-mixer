"""Sensor platform for integration_blueprint."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from homeassistant.components.light import ATTR_COLOR_TEMP_KELVIN
from homeassistant.components.sensor import RestoreSensor
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_BRIGHTNESS as BRIGHTNESS,
    CONF_UNIQUE_ID,
    EntityCategory,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BRIGHTNESS_SENSOR_NAME,
    DISPATCHER_SIGNAL_TURN_OFF,
    DOMAIN,
    TEMPERATURE_SENSOR_NAME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
):
    """Set up the sensor platform from a ConfigEntry."""
    # config = entry.as_dict()["data"]

    brightness = CCTRestoreSensor(
        config_id=entry.entry_id,
        name=BRIGHTNESS_SENSOR_NAME,
        monitored_value=BRIGHTNESS,
    )
    temperature = CCTRestoreSensor(
        config_id=entry.entry_id,
        name=TEMPERATURE_SENSOR_NAME,
        monitored_value=ATTR_COLOR_TEMP_KELVIN,
        device_class=SensorDeviceClass.TEMPERATURE,
        unit_of_measurement="K",
    )

    sensors = [brightness, temperature]

    async_add_devices(sensors)


class CCTRestoreSensor(RestoreSensor):
    """Restorable virtual sensor tracking the last state of a CCT light before turning off."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_visible_default = False

    def __init__(
        self,
        config_id: str,
        name: str,
        monitored_value: str,
        device_class: SensorDeviceClass | None = None,
        unit_of_measurement: str | None = None,
    ) -> None:
        """Initialize the sensor."""
        self._attr_unique_id = f"{config_id}_{monitored_value}"
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, config_id)})
        self.monitored_value = monitored_value
        self.config_id = config_id
        self.event_listener_disconnect: CALLBACK_TYPE | None = None

    async def async_added_to_hass(self):
        """Restore the previous state if available. Subscribe to the turn-off dispatcher signal from the CCT light."""

        # Keep track of the entity_id of each sensor, to be discoverable by the light entity
        data = self.hass.data[DOMAIN].setdefault(self.config_id, {})
        data[self.monitored_value] = self.entity_id

        restored_state = await self.async_get_last_sensor_data()

        # Restore the previous state if it is not None
        if (
            restored_state is not None
            and restored_state.as_dict()["native_value"] is not None
        ):
            _LOGGER.debug(
                "%s: restoring state: %s",
                self._friendly_name_internal(),
                restored_state,
            )
            self._attr_native_value = restored_state.as_dict()["native_value"]
            self._attr_native_unit_of_measurement = restored_state.as_dict()[
                "native_unit_of_measurement"
            ]

        # Keep track of when the CCT light turns off
        _LOGGER.debug("%s: start listening for events", self._friendly_name_internal())

        self.event_listener_disconnect = async_dispatcher_connect(
            self.hass, DISPATCHER_SIGNAL_TURN_OFF, self.cct_light_off_callback
        )

    async def async_will_remove_from_hass(self):
        """Clean up the event listener."""
        if self.event_listener_disconnect:
            _LOGGER.debug(
                "%s: shutting down event listener", self._friendly_name_internal()
            )
            self.event_listener_disconnect()

    @callback
    async def cct_light_off_callback(self, event: Mapping[str, Any]):
        """Keep track of the value of the `monitored_state` before turning off."""
        _LOGGER.debug("%s: event %s", self._friendly_name_internal(), event)

        light_entity = event.get(ATTR_ENTITY_ID)
        light_unique_id = event.get(CONF_UNIQUE_ID)

        # Check if the source light has comes from the same ConfigEntry as ourselves
        if light_unique_id != self.config_id:
            return

        # Get the brightness from the event payload, before the light shuts off
        sensor_value = event.get(self.monitored_value)

        if sensor_value is None:
            _LOGGER.warning(
                "%s: received invalid %s from %s: %s",
                self._friendly_name_internal(),
                self.monitored_value,
                light_entity,
                sensor_value,
            )
            return

        sensor_value_int = round(sensor_value)
        _LOGGER.debug(
            "%s: saving %s %d",
            self._friendly_name_internal(),
            self.monitored_value,
            sensor_value_int,
        )

        self._attr_native_value = sensor_value_int
        self.async_schedule_update_ha_state()
