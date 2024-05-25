# Color Temperature Light Mixer

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacs-shield]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

[![Community Forum][forum-shield]][forum]

Home Assistant integration to group multiple light sources into a single "virtual" color temperature-changing light.

Useful for instance with LED strips having separate cold white/warm white channels (CCT or CWWW LED), in which two separate light entities are exposed in Home Assistant, one for each color temperature. This integration groups together the two lights, allowing them to be controlled as a single entity in HA.

An example application is a "dumb"/analog LED strip with controlled by a Shelly RGBW2, configured in _4 white channels_ mode, where the cold light and warm light channels are each controlled by a separate channel in the Shelly.

<p align="center">
    <img src="https://github.com/mion00/color-temperature-light-mixer/blob/main/docs/cct_light_integration_demo.gif?raw=true"/>
</p>

---
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Installation](#installation)
  - [Install from HACS (recommended)](#install-from-hacs-recommended)
  - [Manual installation](#manual-installation)
- [Configuration](#configuration)
  - [YAML file](#yaml-file)
- [Track updates](#track-updates)
- [Known Limitations and issues](#known-limitations-and-issues)
- [Troubleshooting](#troubleshooting)
- [Contributions are welcome!](#contributions-are-welcome)
- [Authors & contributors](#authors--contributors)
  - [Credits](#credits)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Installation

### Install from HACS (recommended)

1. Have [HACS][hacs] installed, this will allow you to easily manage and track updates.
1. Add this repository as a _Custom repository_ ([more details](https://hacs.xyz/docs/faq/custom_repositories/)) or just press the button below:\
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)][hacs-repository]
1. Once added, search in HACS for "Color Temperature Light Mixer".
1. Click __Install__.
1. You can configure the component via:
    1. Home Assistant UI\
    In the HA UI go to "Configuration" > "Integrations" click "+" and search for "Color Temperature Light Mixer".
    1. `configuration.yaml`\
    Follow the instructions below, then restart Home Assistant.

### Manual installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `color_temperature_light_mixer`.
1. Download the file `color_temperature_light_mixer.zip` from the [latest release section][releases-latest] in this repository.
1. Extract _all_ files from this archive you downloaded in the directory (folder) you created.
1. Restart Home Assistant
1. You can configure the component via:
    1. Home Assistant UI\
    In the HA UI go to "Configuration" > "Integrations" click "+" and search for "Color Temperature Light Mixer".
    1. `configuration.yaml`\
    Follow the instructions below, then restart Home Assistant.

## Configuration

The integration can be configured via either HA UI and YAML.

The following configuration options are supported:

Name | Description
-- | --
`name` | The name of the "virtual" color changing temperature light.
`warm_light_entity_id` | The `entity_id` representing the warm light (yellow-ish color).
`warm_light_color_temp_kelvin` | The color temperature of the warm light, in Kelvin.
`cold_light_entity_id` | The `entity_id` representing the cold light (blu-ish color).
`cold_light_color_temp_kelvin` | The color temperature of the cold light, in Kelvin.

### YAML file

The same configuration options can be specified via the `configuration.yaml`.
See the following snippet for an example:

```yaml
color_temperature_light_mixer:
  - name: Virtual
    warm_light_entity_id: light.warm_white
    warm_light_color_temp_kelvin: 3000
    cold_light_entity_id: light.cold_white
    cold_light_color_temp_kelvin: 6000
```

__This integration will set up the following platforms:__

Platform | Description
-- | --
`light` | The color changing temperature light.
`sensor` | Two supporting sensors (hidden by default) to maintain the state of the light across HA reboots.

## Track updates

You can automatically track new versions of this component and update it by [HACS][hacs].

## Known Limitations and issues

- This integration makes the assumption that 100% brightness is achieved when both warm white AND cold white LEDs are on.
Check the specifications of your lights to see if this type of setup is supported (compared instead to having only one of the strips at 100% power at a time).
- At the moment only two light sources are supported per "virtual" light.
- At the moment the assumption is that each light source "contributes" equally to the resulting temperature. This was a design choice done to keep the math required in the computations simple. In some particular setups however this might not be the case.

## Troubleshooting

To enable debug logs use this configuration:

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.color_temperature_light_mixer: debug
```

...then restart HA.

## Contributions are welcome!

This is an active open-source project. We are always open to people who want to
use the code or contribute to it.

We have set up a separate document containing our
[contribution guidelines](CONTRIBUTING.md).

Thank you for being involved!

## Authors & contributors

For a full list of all authors and contributors, check [the contributor's page][contributors].

### Credits
The original inspiration came from the template light provided by [gfrancesco](https://github.com/gfrancesco/cwww-template-light-ha), as part of this [HA forum thread](https://community.home-assistant.io/t/create-a-temperature-changing-light-from-2-lights-and-shelly-rgbw2-solved/266408/15).

This Home Assistant custom component was created and is updated using the [HA-Blueprint template](https://github.com/Limych/ha-blueprint). You can use this template to maintain your own Home Assistant custom components.

***

[component]: https://github.com/mion00/color-temperature-light-mixer
[commits-shield]: https://img.shields.io/github/commit-activity/y/mion00/color-temperature-light-mixer.svg?style=popout
[commits]: https://github.com/mion00/color-temperature-light-mixer/commits/master
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=popout
[hacs]: https://hacs.xyz
[hacs-repository]: https://my.home-assistant.io/redirect/hacs_repository/?owner=mion00&repository=color-temperature-light-mixer&category=integration
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=popout
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/mion00/color-temperature-light-mixer
[maintenance-shield]: https://img.shields.io/badge/maintainer-mion00-blue.svg?style=popout
[releases-shield]: https://img.shields.io/github/release/mion00/color-temperature-light-mixer.svg?style=popout
[releases]: https://github.com/mion00/color-temperature-light-mixer/releases
[releases-latest]: https://github.com/mion00/color-temperature-light-mixer/releases/latest
[user_profile]: https://github.com/mion00
[report_bug]: https://github.com/mion00/color-temperature-light-mixer/issues/new?template=bug_report.md
[suggest_idea]: https://github.com/mion00/color-temperature-light-mixer/issues/new?template=feature_request.md
[contributors]: https://github.com/mion00/color-temperature-light-mixer/graphs/contributors
