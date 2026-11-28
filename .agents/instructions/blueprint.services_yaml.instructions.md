---
name: "Service Action Definitions"
description: "Where this project's services.yaml schema, implementations and checks live"
applyTo: "**/services.yaml"
paths:
  - "**/services.yaml"
---

# Service Actions Definition Instructions

**Procedure:** `haci-service-action` (plugin `haci-build`) — load it before editing this file. The Home Assistant
rules for `services.yaml` are `haci.services-yaml`, which loads with this file; what follows is only what this project
adds.

- **Schema:** `schemas/yaml/services_schema.yaml` at the repository root defines the complete structure and the full
  list of selectors. Consult it when unsure about available fields.
- Every field gets a selector, and a specific one — a field that renders as an untyped box is a review blocker here.
- The implementations are in `custom_components/<domain>/service_actions/`.
- User documentation in `docs/user/` says "action" too, never "service".
- `script/hassfest` cross-checks this file against the translation keys, and `script/yaml-check` runs yamllint. Home
  Assistant validates the schema again on load — see `config/home-assistant.log`.
