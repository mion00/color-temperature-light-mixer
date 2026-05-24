"""
Base entity class for color_temperature_light_mixer.

This module provides the base entity class that all integration entities inherit from.
It handles common functionality like device info, unique IDs, and coordinator integration.

For more information on entities:
https://developers.home-assistant.io/docs/core/entity
https://developers.home-assistant.io/docs/core/entity/index/#common-properties
"""

from __future__ import annotations

from custom_components.color_temperature_light_mixer.const import ATTRIBUTION, DEFAULT_NAME
from custom_components.color_temperature_light_mixer.data import ColorTemperatureMixerConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription


class ColorTemperatureMixerEntity(Entity):
    """
    Base entity class for color_temperature_light_mixer.

    All entities in this integration inherit from this class, which provides:
    - Device info management
    - Unique ID generation
    - Attribution and naming conventions

    For more information:
    https://developers.home-assistant.io/docs/core/entity
    """

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        config_entry: ColorTemperatureMixerConfigEntry,
        entity_description: EntityDescription,
    ) -> None:
        """
        Initialize the base entity.

        Args:
            entity_description: The entity description defining characteristics.

        """
        super().__init__()
        self.entity_description = entity_description
        # Include entity description key in unique_id to support multiple entities
        self._attr_unique_id = f"{config_entry.entry_id}_{entity_description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    config_entry.domain,
                    config_entry.entry_id,
                ),
            },
            name=config_entry.title,
            manufacturer=DEFAULT_NAME,
            entry_type=DeviceEntryType.SERVICE,
        )
