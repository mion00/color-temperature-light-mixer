"""Adds config flow for Blueprint."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_USERNAME
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import _DOMAIN_SCHEMA, DOMAIN, is_capitalized

_LOGGER = logging.getLogger(__name__)


class CCTVirtuaLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for CCT Virtual Light."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""

        if user_input and not is_capitalized(user_input[CONF_NAME]):
            _LOGGER.debug("Name is not capitalized")
            errors = {CONF_NAME: "Name must start with a capital letter"}
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema(_DOMAIN_SCHEMA), errors=errors
            )

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        # Ask for information
        # _LOGGER.debug("Asking for user input")
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(_DOMAIN_SCHEMA)
        )

    async def async_step_import(
        self,
        user_input: dict,
    ) -> ConfigFlowResult:
        """Handle configuration by YAML file."""
        await self.async_set_unique_id(user_input[CONF_NAME])
        # Keep a list of lights that are configured via YAML
        data = self.hass.data.setdefault(DOMAIN, {})
        data.setdefault("__yaml__", set()).add(self.unique_id)

        for entry in self._async_current_entries():
            if entry.unique_id == self.unique_id:
                _LOGGER.debug("Updating existing config entry")
                self.hass.config_entries.async_update_entry(entry, data=user_input)
                self._abort_if_unique_id_configured()

        _LOGGER.debug("Creating a new config entry")
        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
