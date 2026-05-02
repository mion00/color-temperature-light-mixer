"""
Entity package for color_temperature_light_mixer.

Architecture:
    All platform entities inherit from (PlatformEntity, ColorTemperatureMixerEntity).
    MRO order matters — platform-specific class first, then the integration base.
    Entities read data from coordinator.data and NEVER call the API client directly.
    Unique IDs follow the pattern: {entry_id}_{description.key}

See entity/base.py for the ColorTemperatureMixerEntity base class.
"""

from .base import ColorTemperatureMixerEntity

__all__ = ["ColorTemperatureMixerEntity"]
