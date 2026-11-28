---
name: "Repair Flows"
description: "Where repairs live in this project and where an issue links to"
applyTo: "custom_components/**/repairs.py"
paths:
  - "custom_components/**/repairs.py"
---

# Repairs Instructions

**Procedure:** `haci-breaking-changes` (plugin `haci-quality`) — load it before creating an issue. The rules for
issues and repair flows are `haci.repairs`, which loads with this file; what follows is only what this project adds.

- `repairs.py` sits at the integration root, beside `config_flow_handler/` and never inside it — a repair flow is not
  a config flow, and the shim `config_flow.py` must stay a shim.
- `learn_more_url` points at the page in `docs/user/` that explains the problem, never at the README's top.
- Issue text goes into `translations/en.json` only (`haci-translations`).
