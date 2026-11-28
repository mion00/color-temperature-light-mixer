---
name: "Diagnostics"
description: "Where diagnostics live in this layout"
applyTo: "custom_components/**/diagnostics.py"
paths:
  - "custom_components/**/diagnostics.py"
---

# Diagnostics Instructions

**Procedure:** `haci-coordinator-debug` (plugin `haci-build`) — load it when reading or checking diagnostics output.
The Home Assistant rules for diagnostics are `haci.diagnostics`, which loads with this file; what follows is only what
this project adds.

- `diagnostics.py` sits at the integration root, `custom_components/<domain>/diagnostics.py`, and reads the coordinator
  through `entry.runtime_data`; `script/ha diagnostics` prints what a user downloads
  ([`blueprint-dev-instance`](../skills/blueprint-dev-instance/SKILL.md)).
