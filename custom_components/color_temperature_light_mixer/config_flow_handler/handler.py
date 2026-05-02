"""
Config flow handler for color_temperature_light_mixer.

This module provides backwards compatibility by re-exporting the flow handlers
from their respective modules. The actual implementation is split across:

- config_flow.py: Main config flow (user, reauth, reconfigure)
- options_flow.py: Options flow for post-setup configuration
- subentry_flow.py: Template for future subentry flows
- schemas/: Voluptuous schemas for all forms
- validators/: Validation logic for user inputs

This structure keeps the code organized while allowing complex flows to grow
without becoming monolithic.

For more information:
https://developers.home-assistant.io/docs/config_entries_config_flow_handler
"""

from __future__ import annotations

from custom_components.color_temperature_light_mixer.config_flow_handler.config_flow import (
    ColorTemperatureMixerConfigFlowHandler,
)
from custom_components.color_temperature_light_mixer.config_flow_handler.options_flow import (
    ColorTemperatureMixerOptionsFlow,
)

# Re-export for backwards compatibility and external imports
__all__ = [
    "ColorTemperatureMixerConfigFlowHandler",
    "ColorTemperatureMixerOptionsFlow",
]
