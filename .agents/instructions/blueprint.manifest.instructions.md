---
name: "Integration Manifest"
description: "The manifest schema, version ownership and validation in this project"
applyTo: "**/manifest.json"
paths:
  - "**/manifest.json"
---

# Manifest Instructions

**Procedure:** `haci-config-flow` (plugin `haci-build`) — load it when adding a discovery matcher, which is configured
together with the config flow step it starts. The Home Assistant rules for `manifest.json` are `haci.manifest`, which
loads with this file; what follows is only what this project adds.

- Applies to `custom_components/<domain>/manifest.json`.
- **Schema:** `schemas/json/manifest_schema.json` combines Home Assistant's manifest requirements with the fields the
  Marketplace requires, and carries the category list. Always validate against it.
- `version` is SemVer, and `script/version` owns the field — never edit it by hand.
- The minimum Home Assistant version lives in `hacs.json` → `homeassistant`
  (`haci-marketplace`).
- `script/hassfest` is the gate.
