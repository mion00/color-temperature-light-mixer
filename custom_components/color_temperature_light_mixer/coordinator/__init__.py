"""
Data update coordinator package for color_temperature_light_mixer.

This package provides the coordinator infrastructure for managing periodic
data updates and distributing them to all entities in the integration.

Package structure:
- base.py: Main coordinator class (ColorTemperatureMixerDataUpdateCoordinator)
- data_processing.py: Data validation, transformation, and caching utilities
- error_handling.py: Error recovery strategies and retry logic
- listeners.py: Event listeners and entity callbacks

For more information on coordinators:
https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
"""

from __future__ import annotations

from .base import ColorTemperatureMixerDataUpdateCoordinator

__all__ = ["ColorTemperatureMixerDataUpdateCoordinator"]
