"""
Config flow for color_temperature_light_mixer.

This module implements the main configuration flow including:
- Initial user setup
- Reconfiguration of existing entries
- Reauthentication flow

For more information:
https://developers.home-assistant.io/docs/config_entries_config_flow_handler
"""

from __future__ import annotations

from typing import Any

from custom_components.color_temperature_light_mixer.config_flow_handler.schemas import (
    get_reconfigure_schema,
    get_user_schema,
)
from custom_components.color_temperature_light_mixer.const import DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.loader import async_get_loaded_integration


class ColorTemperatureMixerConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """
    Handle a config flow for color_temperature_light_mixer.

    This class manages the configuration flow for the integration, including
    initial setup, reconfiguration, and reauthentication.

    Supported flows:
    - user: Initial setup via UI
    - reconfigure: Update existing configuration

    For more details:
    https://developers.home-assistant.io/docs/config_entries_config_flow_handler
    """

    VERSION = 1

    # @staticmethod
    # def async_get_options_flow(
    #     config_entry: config_entries.ConfigEntry,
    # ) -> ColorTemperatureMixerOptionsFlow:
    #     """
    #     Get the options flow for this handler.

    #     Returns:
    #         The options flow instance for modifying integration options.

    #     """
    #     from custom_components.color_temperature_light_mixer.config_flow_handler.options_flow import (
    #         ColorTemperatureMixerOptionsFlow,
    #     )

    #     return ColorTemperatureMixerOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle a flow initialized by the user.

        This is the entry point when a user adds the integration from the UI.

        Args:
            user_input: The user input from the config flow form, or None for initial display.

        Returns:
            The config flow result, either showing a form or creating an entry.

        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Set unique ID based on username
            # await self.async_set_unique_id(slugify(user_input[CONF_NAME]))
            # self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        integration = async_get_loaded_integration(self.hass, DOMAIN)
        assert integration.documentation is not None, "Integration documentation URL is not set in manifest.json"

        # Show the form to be filled by the user
        return self.async_show_form(
            step_id="user",
            data_schema=get_user_schema(user_input),
            errors=errors,
            description_placeholders={
                "documentation_url": integration.documentation,
            },
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle reconfiguration of the integration.

        Args:
            user_input: The user input from the reconfigure form, or None for initial display.

        Returns:
            The config flow result, either showing a form or updating the entry.

        """
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_update_reload_and_abort(
                entry,
                data=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=get_reconfigure_schema(entry.data),
            errors=errors,
        )


__all__ = ["ColorTemperatureMixerConfigFlowHandler"]
