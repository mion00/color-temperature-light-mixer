"""
API package for color_temperature_light_mixer.

Architecture:
    Three-layer data flow: Entities → Coordinator → API Client.
    Only the coordinator should call the API client. Entities must never
    import or call the API client directly.

Exception hierarchy:
    ColorTemperatureMixerApiClientError (base)
    ├── ColorTemperatureMixerApiClientCommunicationError (network/timeout)
    └── ColorTemperatureMixerApiClientAuthenticationError (401/403)

Coordinator exception mapping:
    ApiClientAuthenticationError → ConfigEntryAuthFailed (triggers reauth)
    ApiClientCommunicationError → UpdateFailed (auto-retry)
    ApiClientError             → UpdateFailed (auto-retry)
"""

from .client import (
    ColorTemperatureMixerApiClient,
    ColorTemperatureMixerApiClientAuthenticationError,
    ColorTemperatureMixerApiClientCommunicationError,
    ColorTemperatureMixerApiClientError,
)

__all__ = [
    "ColorTemperatureMixerApiClient",
    "ColorTemperatureMixerApiClientAuthenticationError",
    "ColorTemperatureMixerApiClientCommunicationError",
    "ColorTemperatureMixerApiClientError",
]
