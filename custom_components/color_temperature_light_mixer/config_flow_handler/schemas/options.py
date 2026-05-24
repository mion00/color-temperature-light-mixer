"""
Options flow schemas.

Schemas for the options flow that allows users to modify settings
after initial configuration.

When adding many options, consider grouping them:
- basic_options.py: Common settings (update interval, debug mode)
- advanced_options.py: Advanced settings
- device_options.py: Device-specific settings
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol


def get_options_schema(defaults: Mapping[str, Any] | None = None) -> vol.Schema:
    """
    Get schema for options flow.

    Args:
        defaults: Optional dictionary of current option values.

    Returns:
        Voluptuous schema for options configuration.

    """
    defaults = defaults or {}
    return vol.Schema({})


__all__ = [
    "get_options_schema",
]
