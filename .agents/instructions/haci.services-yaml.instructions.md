---
name: "Home Assistant services.yaml"
description: "services.yaml structure, fields, selectors, target, sections and wording"
applyTo: "**/services.yaml"
paths:
  - "**/services.yaml"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-build/skills/haci-service-action/references/rules.services-yaml.md sha256:047eb9d1869f5da8 — written by script/haci-vendor, do not edit -->

# services.yaml rules

Procedure: the `haci-service-action` skill (plugin `haci-build`) — a `services.yaml` entry is never a change on its
own: the handler, the schema and the translations move with it, and the skill is what keeps those four in step.

**Reference:** [Home Assistant Service Actions Documentation](https://contributors.home-assistant.io/core/integrations/actions/)

The filename `services.yaml` is legacy from when actions were called "services". `service` stays in code
identifiers; every text a user reads — names, descriptions, user documentation — says "action", never "service" or
"service action".

## Structure

```yaml
action_name:
  name: Set target value
  description: Sets the target value of the device.
  fields:
    parameter_name:
      name: Parameter name
      description: What this parameter does.
      required: true
      example: "example_value"
      selector:
        text:
  target:
    entity:
      - domain: light
```

## Key requirements

**`name` and `description` live in the translations.** What is written here is only the fallback shown when a
translation is missing; `services.<action>.name` / `.description` and one pair per field are what users actually see,
and hassfest requires them. To keep something out of the translations — a URL, say — pass
`description_placeholders={"docs_url": …}` to `hass.services.async_register`.

**Wording** (fallbacks here and the translations alike): sentence case, never Title Case. An action name is an
imperative ("Set target value"); its description is third person and says what the action does in a sentence a person
would say ("Sets the target value of the device."), because the Assist API hands it to conversation agents as is.

**Action definition:**

- `name` - Fallback name
- `description` - Fallback explanation with Markdown support
- `fields` - Parameter definitions (optional)
- `target` - Entity/device/area selector (optional)

**Field definition:**

- `name` - Fallback field name
- `description` - Fallback field explanation
- `required` - Boolean, default false
- `example` - Example value (recommended)
- `default` - Default value (optional)
- `selector` - UI selector type — every field gets one
- `advanced` - Hide behind the advanced toggle
- `filter` - Show the field only for matching targets. Specify **either** `supported_features` **or** `attribute`,
  never both; the field appears when at least one selected entity matches.

**Target the level the action acts on** — entity via `target:`, one device via a `device_id` field with a `device:`
selector, the whole integration instance via a `config_entry_id` field with a `config_entry:` selector. A target is
never optional and never defaulted.

**`sections`** group fields in the UI (`collapsed: true` to fold them). Unlike config flow sections, they do **not**
nest the data: a field inside a section still arrives as `{"speed_pct": 50}`, not
`{"additional_fields": {"speed_pct": 50}}`.

Under `target.entity.supported_features`, a nested list means AND — both features must be present.

**`target:` never takes a `device:` filter** — only `entity:`. Hassfest fails on it. An action that needs a device of
this integration uses a `device_id` field with a `device:` selector filtered to `integration: <domain>`.

## Selectors

Every field takes one. Pick the specific one (`number:` with `min`/`max`/`step`, `duration:`, `color_rgb:`, `entity:`
with a domain filter) over `text:`; a field that renders as an untyped box is a defect.

**If `target:` is defined, do NOT define `entity_id` as a field.**

## Conventions

- Action names are verb-based: `set_mode`, `reset_filter`
- `required: true` only when there is no sensible default
- Realistic `example:` values for anything non-obvious

## Validation

Hassfest cross-checks this file against the translation keys. Home Assistant validates the schema again on load and
logs what it rejects.
