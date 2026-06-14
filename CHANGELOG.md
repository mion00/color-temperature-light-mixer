# Changelog

## [0.2.1](https://github.com/mion00/color-temperature-light-mixer/compare/v0.2.0...v0.2.1) (2026-06-14)


### Bug Fixes

* **diagnostics.py:** fix missing runtime data when exporting diagnostics ([d3d670b](https://github.com/mion00/color-temperature-light-mixer/commit/d3d670b37316fcac6727b59eca20ba761b281f7d))

## [0.2.0](https://github.com/mion00/color-temperature-light-mixer/compare/0.1.2...v0.2.0) (2026-05-31)


### ⚠ BREAKING CHANGES

* Changed `unique_id` properties for created entities. Upon update of this integration, each configured instance of this integration will result in the previous "virtual" light group entity being marked as not available, and a newly created "virtual" light group entity with `_2` prepended to its entity ID. To fix this:
    - Go in the device page of each of your configured virtual CCT lights
    - manually remove the unavailable entity
    - click on the upper right menu in this page and use "Recreate Entity IDs" to correctly rename the entity with `_2` in its name

### Bug Fixes

* **ColorTemperatureMixerLight:** use helper method to output the best available entity name in logs ([a43db40](https://github.com/mion00/color-temperature-light-mixer/commit/a43db40d9f2c808645476ce069ee66a516a45789))


### Code Refactoring

* update the integration codebase following the updated blueprint structure ([04f62fc](https://github.com/mion00/color-temperature-light-mixer/commit/04f62fc9f4ac6fc69a35d8f7157a1edb03b7e727))

## 0.1.2 (2024-05-29)

## 0.1.1 (2024-05-29)

### Fix

- **light.py**: correctly keep track of previous turned on state

## 0.1.0 (2024-05-28)

### Feat

- **mixed_light.ypynb**: add Python notebook for ease of plotting
- **light.py**: restore the state of the light without the need for two internal diagnostic sensors

## 0.0.7 (2024-05-25)

## 0.0.6 (2024-05-25)

## 0.0.5 (2024-05-25)

### Fix

- **light.py**: implement method async_turn_off() to fire custom signal for sensors

## 0.0.4 (2024-05-25)

## 0.0.3 (2024-05-25)

## 0.0.2 (2024-05-25)

## 0.0.1 (2024-05-25)

### Refactor

- **manifest.json**: capitalize name of integration
