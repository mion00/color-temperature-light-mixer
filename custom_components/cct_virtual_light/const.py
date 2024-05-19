"""Constants for cct_virtual_light."""

from logging import Logger, getLogger
from typing import Any

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_COLOR_TEMP_KELVIN,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

LOGGER: Logger = getLogger(__package__)

NAME = "CCT virtual light"
DOMAIN = "cct_virtual_light"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/mion00/cct-virtual-light/issues"

AVAILABILITY = "availability"
EVENT_NEW_STATE = "new_state"

BRIGHTNESS_SENSOR_NAME = "Restored brightness"
TEMPERATURE_SENSOR_NAME = "Restored temperature"

DISPATCHER_SIGNAL_TURN_OFF = f"{DOMAIN}_turn_off"

# Configuration
CONF_WARM_LIGHT = f"warm_light_{CONF_ENTITY_ID}"
CONF_WARM_LIGHT_TEMPERATURE_KELVIN = f"warm_light_{ATTR_COLOR_TEMP_KELVIN}"
CONF_COLD_LIGHT = f"cold_light_{CONF_ENTITY_ID}"
CONF_COLD_LIGHT_TEMPERATURE_KELVIN = f"cold_light_{ATTR_COLOR_TEMP_KELVIN}"


def is_capitalized(value: str) -> bool:
    return value[0].isupper()


begin

_DOMAIN_SCHEMA = {
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_WARM_LIGHT): selector.EntitySelector({"domain": LIGHT_DOMAIN}),
    vol.Required(
        CONF_WARM_LIGHT_TEMPERATURE_KELVIN, description={"suggested_value": 3000}
    ): cv.positive_int,
    vol.Required(CONF_COLD_LIGHT): selector.EntitySelector({"domain": LIGHT_DOMAIN}),
    vol.Required(
        CONF_COLD_LIGHT_TEMPERATURE_KELVIN, description={"suggested_value": 6000}
    ): cv.positive_int,
}
"""Schema of each CCT virtual light"""
