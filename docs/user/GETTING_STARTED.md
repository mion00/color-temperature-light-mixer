# Getting Started with Color Temperature Light Mixer

This guide will help you install and set up the Color Temperature Light Mixer custom integration for Home Assistant.

## Prerequisites

- Home Assistant 2025.7.0 or newer
- HACS (Home Assistant Community Store) installed
- Network connectivity to [external service/device]

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/mion00/color-temperature-light-mixer`
6. Set category to "Integration"
7. Click "Add"
8. Find "Color Temperature Light Mixer" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/mion00/color-temperature-light-mixer/releases)
2. Extract the `color_temperature_light_mixer` folder from the archive
3. Copy it to `custom_components/color_temperature_light_mixer/` in your Home Assistant configuration directory
4. Restart Home Assistant

## Initial Setup

After installation, add the integration:

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Color Temperature Light Mixer"
4. Follow the configuration steps

## What Gets Created

After successful setup, the integration creates:

### Devices

- **Device Name:** Main device representing your virtual light

### Entities

The following entities are automatically created:

#### Light

- `light.<device_name>` - Light group used to command both warm and cold light sources

## Troubleshooting

### Entities Not Updating

If entities show "Unavailable" or don't update:

1. Check that the device/service is online
2. Verify API credentials haven't expired
3. Review logs: **Settings** → **System** → **Logs**
4. Try reloading the integration

### Debug Logging

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: warning
  logs:
    custom_components.color_temperature_light_mixer: debug
```

Add this to `configuration.yaml`, restart, and reproduce the issue. Check logs for detailed information.

## Next Steps

- Report issues at [GitHub Issues](https://github.com/mion00/color-temperature-light-mixer/issues)

## Support

For help and discussion:

- [GitHub Discussions](https://github.com/mion00/color-temperature-light-mixer/discussions)
- [Home Assistant Community Forum](https://community.home-assistant.io/)
