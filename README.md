<!-- markdownlint-disable MD033 -->
<p align="center">
    <img alt="logo" src="https://github.com/mion00/color-temperature-light-mixer/blob/main/docs/logo_dark.png?raw=true#gh-dark-mode-only" width="500"/>
    <img alt="logo" src="https://github.com/mion00/color-temperature-light-mixer/blob/main/docs/logo.png?raw=true#gh-light-mode-only" width="500"/><br/>
</p>

# Color Temperature Light Mixer

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<!--
Uncomment and customize these badges if you want to use them:

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]
[![Discord][discord-shield]][discord]
-->

**✨ Develop in the cloud:** Want to contribute or customize this integration? Open it directly in GitHub Codespaces - no local setup required!

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/mion00/color-temperature-light-mixer?quickstart=1)

Home Assistant integration to group multiple light sources into a single "virtual" color temperature-changing light.

Useful for instance with LED strips having separate cold white/warm white channels (CCT or CWWW LED), in which two separate light entities are available in Home Assistant, one for each color temperature.
This integration groups together the two lights, allowing them to be controlled as a single entity in HA.

An example application is a "dumb"/analog LED strip controlled by a Shelly RGBW2 (configured in _4 white channels_ mode), where the cold light and warm light channels are each connected to a separate channel in the Shelly.

<p align="center">
    <img src="https://github.com/mion00/color-temperature-light-mixer/blob/main/docs/cct_light_integration_demo.gif?raw=true"
         alt="Animation representing how the virtual light created by this integration interacts with the warm and cold light sources that make it up"
    />
</p>

## ✨ Features

- Group two lights sources under a new, "virtual" light that combines their brightness output to achieve a varied range of color temperatures.
- The "virtual" light reaches 100% brightness by turning on **both light sources** (check the _Know limitations_ section below for more information and potential issues you may encounter with your specific setup).
- Intelligently handles unreachable settings for brightness and color temperatures based on the data passed to the `light.turn_on` service. See [this Python notebook](docs/development/color_temp_calculation.ipynb) for more details.
- Can restore its own state after a reboot.

**This integration will set up the following platforms:**

| Platform | Description                                                                               |
| -------- | ----------------------------------------------------------------------------------------- |
| `light`  | The "virtual" color changing temperature light combining the warm and cold light entities |

## 🚀 Quick Start

### Step 1: Install the Integration

**Prerequisites:** This integration requires [HACS](https://hacs.xyz/) (Home Assistant Community Store) to be installed.

Click the button below to open the integration directly in HACS:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jpawlowski&repository=color-temperature-light-mixer&category=integration)

Then:

1. Click "Download" to install the integration
2. **Restart Home Assistant** (required after installation)

> [!NOTE]
> The My Home Assistant redirect will first take you to a landing page. Click the button there to open your Home Assistant instance.

<details>
<summary><strong>Manual Installation (Advanced)</strong></summary>

If you prefer not to use HACS:

1. Download the `custom_components/color_temperature_light_mixer/` folder from this repository
2. Copy it to your Home Assistant's `custom_components/` directory
3. Restart Home Assistant

</details>

### Step 2: Add and Configure the Integration

**Important:** You must have installed the integration first (see Step 1) and restarted Home Assistant!

#### Option 1: One-Click Setup (Quick)

Click the button below to open the configuration dialog:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=color_temperature_light_mixer)

Follow the setup wizard:

1. Configure the light sources acting as warm white and cold light
2. Click Submit

#### Option 2: Manual Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for "Color Temperature Light Mixer"
4. Follow the same setup steps as Option 1

<!-- ### Step 3: Adjust Settings (Optional)

After setup, you can adjust options:

1. Go to **Settings** → **Devices & Services**
2. Find **Color Temperature Light Mixer**
3. Click **Configure** to adjust:
   - Update interval (how often to refresh data)
   - Enable debug logging -->

You can also **Reconfigure** the light sources anytime without removing the integration.

### Step 3: Start Using!

The integration creates a single entity:

- **Light group**: Light group representing a "virtual" light to control both warm and cold light sources at the same time

Find the entity in **Settings** → **Devices & Services** → **Color Temperature Light Mixer** → click on the device.

## Available Entities

### Lights

- **Color temperature mixer light**: Light group representing a "virtual" light to combine warm and cold light sources

## Configuration Options

### During Setup

| Name                           | Required | Description                                                    |
| ------------------------------ | -------- | -------------------------------------------------------------- |
| Name                           | Yes      | The name of the "virtual" color changing temperature light     |
| `warm_light_entity_id`         | Yes      | The `entity_id` representing the warm light (yellow-ish color) |
| `warm_light_color_temp_kelvin` | Yes      | The color temperature of the warm light, in Kelvin             |
| `cold_light_entity_id`         | Yes      | The `entity_id` representing the cold light (blu-ish color)    |
| `cold_light_color_temp_kelvin` | Yes      | The color temperature of the cold light, in Kelvin             |

## Known limitations and issues

- This integration makes the assumption that 100% brightness is achieved when both warm white AND cold white LEDs are on.
  Check the specifications of your lights to see if this type of setup is supported (compared instead to having only one of the strips at 100% power at a time).\
  A future development might include the ability to cap the output brightness for setups where this is required.
- At the moment the assumption is that each light source "contributes" equally to the resulting temperature. This was a design choice done to keep the math required in the computations simple. In some particular setups however this might not be the case.

- At the moment only two light sources are supported per "virtual" light.\
  It is nonetheless possible to create multiple "virtual" lights, each with their own pair of light sources.
- Support for light transitions has not been appropriately tested yet.

## Troubleshooting

### Enable Debug Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.color_temperature_light_mixer: debug
```

## 🤝 Contributing

Contributions are welcome! Please open an issue or pull request if you have suggestions or improvements.

You have two options to set up a development environment — expand below for full details.

<details>
<summary><strong>Development Setup</strong></summary>

Both options provide the same fully-configured environment with Home Assistant, Python 3.14, Node.js LTS, and all necessary tools.

### Option 1: GitHub Codespaces (Recommended) ☁️

Develop directly in your browser without installing anything locally!

1. Click the green **"Code"** button in this repository
2. Switch to the **"Codespaces"** tab
3. Click **"Create codespace on main"**
4. **Wait for setup** (2-3 minutes first time) — everything installs automatically
5. **Review and commit** your changes in the Source Control panel (`Ctrl+Shift+G`)

> [!TIP]
> Codespaces gives you **60 hours/month free** for personal accounts. When you start Home Assistant (`script/develop`), port 8123 forwards automatically.

### Option 2: Local Development with VS Code 💻

#### Prerequisites

You'll need these installed locally:

- **A Docker-compatible container engine** — see options by platform:

  | Option                                                                                                                   | 🍎 macOS | 🐧 Linux | 🪟 Windows | Notes                                                                                                                                                                                                                                     |
  | ------------------------------------------------------------------------------------------------------------------------ | :------: | :------: | :--------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | [Docker Desktop](https://www.docker.com/products/docker-desktop/)                                                        |    ✅    |    ✅    |     ✅     | **Easiest starting point for all platforms.** GUI-based, well-documented, one installer. Uses WSL2 as default backend on Windows (Hyper-V also available). Installation requires admin rights; daily use does not. Free for personal use. |
  | [OrbStack](https://orbstack.dev/) ⭐                                                                                     |    ✅    |    —     |     —      | **Recommended for macOS** once Docker Desktop feels slow. Starts in ~2s, much lighter on RAM/CPU, full Docker API compatibility. Free for personal use.                                                                                   |
  | [Docker CE](https://docs.docker.com/engine/install/) (native) ⭐                                                         |    —     |    ✅    |     —      | **Recommended for Linux.** Install directly via your package manager — no VM, no GUI, no overhead. Free.                                                                                                                                  |
  | [WSL2](https://learn.microsoft.com/windows/wsl/install) + [Docker CE](https://docs.docker.com/engine/install/ubuntu/) ⭐ |    —     |    —     |     ✅     | **Recommended for Windows** once you're comfortable with WSL2. Docker runs natively inside WSL2 — no GUI overhead. Requires one-time WSL2 setup. Free.                                                                                    |
  | [Rancher Desktop](https://rancherdesktop.io/)                                                                            |    ✅    |    ✅    |     ✅     | Open source by SUSE. GUI-based, uses WSL2 on Windows. Good alternative to Docker Desktop. Free.                                                                                                                                           |
  | [Colima](https://github.com/abiosoft/colima)                                                                             |    ✅    |    ✅    |     —      | CLI-only, very lightweight. Good for terminal-focused workflows. Free.                                                                                                                                                                    |

- **VS Code** with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
- **Git** — macOS and Linux usually have it already; see below if not, or to get a newer version:
  - **🍎 macOS:** The system Git (`xcode-select --install`) works fine. Recommended: `brew install git` ([Homebrew](https://brew.sh/)) for a current version.
  - **🐧 Linux:** Usually pre-installed. If not: `sudo apt install git` (or your distro's equivalent).
  - **🪟 Windows + WSL2 ⭐:** Install Git _inside WSL2_ with `sudo apt install git`. Git on Windows itself is not needed — VS Code clones and operates entirely within WSL2.
  - **🪟 Windows + Docker Desktop:** Install via `winget install Git.Git` or download [Git for Windows](https://git-scm.com/download/win).
- **Hardware** — the devcontainer runs a full Home Assistant instance including Python tooling:

  |          | Minimum    | Recommended                           |
  | -------- | ---------- | ------------------------------------- |
  | **RAM**  | 8 GB       | 16 GB or more                         |
  | **CPU**  | 4 cores    | 8 cores or more                       |
  | **Disk** | 10 GB free | 20 GB free (SSD strongly recommended) |

> [!TIP]
> **Not sure which Docker option to pick?** Start with [Docker Desktop](https://www.docker.com/products/docker-desktop/) — it works on all platforms, has a GUI, and needs no extra setup. The ⭐ options are faster alternatives once you're comfortable. macOS and Linux offer the best devcontainer experience — containers run with no extra VM layer and file I/O is fast. Windows works well too; this integration uses named container volumes (files live inside WSL2, not on the Windows drive) to keep performance acceptable.

> [!NOTE]
> **New to Dev Containers?** See the [VS Code Dev Containers documentation](https://code.visualstudio.com/docs/devcontainers/containers#_system-requirements) for system requirements and how to install the extension. **Once the extension is installed, you're done** — this repository already ships a complete devcontainer configuration. You don't need to follow the rest of the VS Code guide; the setup steps below are all that's needed.

#### Setup Steps

1. **Clone in a Dev Container:**

   **🍎 macOS / 🐧 Linux:** Clone the repository and open the folder in VS Code → click **"Reopen in Container"** when prompted (or `F1` → **"Dev Containers: Reopen in Container"**).

   **🪟 Windows:** In VS Code, press `F1` → **"Dev Containers: Clone Repository in Named Container Volume..."** and enter the repository URL. This keeps files inside WSL2 for best I/O performance.

2. Wait for the container to build (2-3 minutes first time)

3. **Review and commit** changes in Source Control (`Ctrl+Shift+G`)

4. **Start developing**:

   ```bash
   script/develop  # Home Assistant runs at http://localhost:8123
   ```

> [!NOTE]
> Both Codespaces and local DevContainer provide the exact same experience. The only difference is where the container runs (GitHub's cloud vs. your machine).

</details>

---

## 🤖 AI-Assisted Development

> [!NOTE]
> **Transparency Notice:** This integration was developed with assistance from AI coding agents (GitHub Copilot, Claude, and others). While the codebase follows Home Assistant Core standards, AI-generated code may not be reviewed or tested to the same extent as manually written code. AI tools were used to generate boilerplate code, implement standard integration features (config flow, coordinator, entities), ensure code quality and type safety, and write documentation. If you encounter unexpected behavior, please [open an issue](../../issues) on GitHub.
>
> _This section can be removed or modified if AI assistance was not used in your integration's development._

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [@mion00][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/mion00/color-temperature-light-mixer.svg?style=for-the-badge
[commits]: https://github.com/mion00/color-temperature-light-mixer/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/mion00/color-temperature-light-mixer.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40mion00-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/mion00/color-temperature-light-mixer.svg?style=for-the-badge
[releases]: https://github.com/mion00/color-temperature-light-mixer/releases
[user_profile]: https://github.com/jpawlowski

<!-- Optional badge definitions - uncomment if needed:
[buymecoffee]: https://www.buymeacoffee.com/jpawlowski
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
-->
