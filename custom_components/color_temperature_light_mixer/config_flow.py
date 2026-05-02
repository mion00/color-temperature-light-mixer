"""
Config flow for color_temperature_light_mixer.

This module provides backwards compatibility for hassfest.
The actual implementation is in the config_flow_handler package.
"""

from __future__ import annotations

from .config_flow_handler import ColorTemperatureMixerConfigFlowHandler

__all__ = ["ColorTemperatureMixerConfigFlowHandler"]
