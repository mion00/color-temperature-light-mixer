"""Constants for cct_virtual_light."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "CCT virtual light"
DOMAIN = "cct_virtual_light"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/mion00/cct-virtual-light/issues"

CONF_WARM_LIGHT = "warm_light"
CONF_COLD_LIGHT = "cold_light"

AVAILABILITY = "availability"
EVENT_NEW_STATE = "new_state"
