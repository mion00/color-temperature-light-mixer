---
name: "Home Assistant integration manifest"
description: "Required manifest.json fields, integration types, IoT classes, and requirements"
applyTo: "**/manifest.json"
paths:
  - "**/manifest.json"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-build/skills/haci-config-flow/references/rules.manifest.md sha256:38b5cbb99ae2a19a — written by script/haci-vendor, do not edit -->

# Manifest rules

Procedure: the `haci-config-flow` skill (plugin `haci-build`) — the discovery matchers this file declares, and the
config flow steps they start.

## Required Fields

Home Assistant's own manifest requirements plus the fields the Marketplace requires:

```json
{
  "domain": "<domain>",
  "name": "Your Integration Title",
  "codeowners": ["@your_github_username"],
  "config_flow": true,
  "documentation": "https://github.com/your_org/your_repo",
  "integration_type": "device",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/your_org/your_repo/issues",
  "requirements": [],
  "version": "0.0.0"
}
```

## Field Reference

**Core fields:**

- `domain` - Integration identifier (matches directory name)
- `name` - Display name in Home Assistant
- `version` - Required: the Marketplace refuses to install without it, and it must equal the release tag. Any version
  AwesomeVersion recognises works (SemVer, CalVer).
- `documentation` - Link to documentation
- `issue_tracker` - Link to GitHub issues (required for the catalog)
- `codeowners` - GitHub usernames for notifications

**Integration behavior:**

- `config_flow` - Boolean, true if integration has UI config
- `integration_type` - One of: `device`, `hub`, `service`, `helper`. `virtual` can only be provided by Home Assistant
  Core, and `entity`, `hardware` and `system` are not for a custom integration. Unset defaults to `hub` — set it
  explicitly.
- `iot_class` - Connectivity type (see below)
- `requirements` - Python package dependencies

**Optional fields:**

- `dependencies` - Integrations loaded before setup. This guarantees the integration is **loaded**, not that its
  config entries are set up. A custom integration may list both built-in and other custom integrations here.
- `after_dependencies` - Load after these integrations, without requiring them
- `loggers` - The logger names the integration's requirements use in their `getLogger` calls, so the user's log-level
  setting reaches the library too
- `single_config_entry` - `true` prevents the user adding a second entry. This is the only thing that makes "the one
  entry" a safe assumption in a service action handler.
- `categories` - One to three values from the
  [category list](https://contributors.home-assistant.io/core/integrations/categories/), `category` or
  `category.subcategory`, the primary one first. Optional
  for a custom integration, but the catalog publishes them and the HACS action warns when the key is missing.
- `quality_scale` - The tier the integration claims: `bronze` to `platinum`, or `custom`. Optional for custom
  integrations and not shown in the UI. Hassfest rejects `silver` and above without a non-empty `codeowners`.
- `disabled` - A reason string that stops Home Assistant from loading the integration at all; it only logs the reason.
  An emergency brake for a release that must not run, never a feature switch.
- `import_executor` - Custom integrations only. Defaults to `true`, importing the integration off the event loop; set
  `false` only when the import itself must run in the event loop.
- `dhcp`, `zeroconf`, `ssdp`, `usb`, `bluetooth` - Discovery configs. Each protocol has a matcher rule that fails
  silently when guessed — see the discovery-matchers reference of `haci-config-flow`.
- `homekit`, `mqtt` - Protocol configs
- `preview_features` - Home Assistant Labs features the user switches on themselves, keyed by slug, each with optional
  `feedback_url`, `learn_more_url` and `report_issue_url`. Works for a custom integration too; point the URLs at the
  integration's own repository, and read the switch with `async_is_preview_feature_enabled()` /
  `async_subscribe_preview_feature()` from `homeassistant.components.labs`.

There is **no minimum Home Assistant version key** in `manifest.json`. That lives in `hacs.json` → `homeassistant`. Raising it is not a breaking change, but it must reach the
changelog (`haci-breaking-changes`, plugin `haci-quality`).

**Naming:** if the product exists as both a local and a cloud integration, the cloud one appends "Cloud". The local
one uses the plain product name — never append "Local".

## IoT Class Values

Choose the most accurate:

- `cloud_polling` - Cloud API with polling
- `cloud_push` - Cloud API with push updates
- `local_polling` - Local device with polling
- `local_push` - Local device with push updates
- `calculated` - Derived from other entities
- `assumed_state` - Cannot verify state

## Requirements Format

Use package name with version constraint:

```json
"requirements": [
  "some-package==1.2.3"
]
```

**Only list what Home Assistant does not already ship.** A custom integration must not repeat a package from Core's
own `requirements.txt` — `aiohttp`, `probatio`, `httpx`, `awesomeversion` and friends are already there, and
pinning them from here can only conflict with Core.

## Validation

Hassfest is the gate. Home Assistant and the Marketplace also validate on install and load, and errors appear
in the log.

## References

- [Manifest Documentation](https://contributors.home-assistant.io/core/integrations/manifest/)
- [IoT Class](https://contributors.home-assistant.io/core/integrations/manifest/#iot_class)
- [Marketplace: custom integrations](https://contributors.home-assistant.io/marketplace/guides/integrations/)
