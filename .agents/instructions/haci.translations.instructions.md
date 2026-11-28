---
name: "Home Assistant translations"
description: "Language-aware strings, placeholders, what hassfest rejects, Core-only syntax, entity translations and UI text style"
applyTo: "**/translations/*.json"
paths:
  - "**/translations/*.json"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-build/skills/haci-translations/references/rules.md sha256:04ac4545b33243ae — written by script/haci-vendor, do not edit -->

# Home Assistant translation rules

Procedure: the `haci-translations` skill (plugin `haci-build`) — which keys a given change needs, and how to write them.

These rules apply to a custom integration's `translations/<language>.json` files. `en.json` is the required base
language; the other files are named by their [BCP 47](https://www.rfc-editor.org/info/bcp47) code (`de`, `fr-CA`).

## Language-aware from the first line

An integration may ship in one language for years; it is still written so that adding the second one is a new file,
not a refactoring.

- **No user-facing text in Python.** Entity, attribute and device names, state values, select options, errors, repair
  issues, notifications, units that are words, config flow text — all of it comes from a translation key. Log messages
  stay English: they are for developers.
- **States, attribute values and select options are `snake_case` codes**; the prose lives in the translation. A
  display string as a state breaks every automation the day it is translated.
- **Every value of an `ENUM` sensor, an enum attribute and a `select` has its `state` translation** — hassfest checks
  the file format, not that each option is covered.
- **Placeholders carry values** — a number, a name, a time — never a sentence or a word in one language.
- **Text Home Assistant has no translation slot for** (a notification body, generated dashboard text, an entity
  description) comes from the integration's own per-language files, loaded for `hass.config.language` — never from a
  string literal.
- **`en.json` is the base, whatever language the author works in.** Home Assistant falls back to English for every key
  a language lacks, so `en.json` is always complete; the author's own language is a second file beside it.

## Placeholders

`{variable}` is replaced at runtime. The placeholder name is never translated (`{host}` stays `{host}`, not `{hôte}`)
and matches the code exactly.

**No single quotes around a placeholder inside a string value** — they cannot be translated (German uses „…", French
«…») and hassfest rejects them:

- ✅ `"message": "Service {service} is unavailable"`
- ✅ `"message": "Service \"{service}\" is unavailable"`
- ❌ `"message": "Service '{service}' is unavailable"`

This is about quotes inside the value, not the JSON delimiters.

- **Placeholder names are valid identifiers** (`[a-zA-Z_][a-zA-Z0-9_]*`) **and say what they hold** — `{device_name}`,
  not `{name2}` or `{0}`; the name is the translator's only context. Entity state values take no placeholders at all.
- **No plural syntax.** ICU forms like `{count, plural, one {…} other {…}}` are frontend-only. Phrase the string so it
  reads right for any number: "Devices found: {count}", not "{count} device(s) found".
- **A translation whose placeholders differ from `en.json` is dropped** — Home Assistant logs an error and shows the
  English string instead. Keep the placeholder set identical in every language.

## What hassfest rejects in a string

- A URL — put it in a placeholder (`"Get a key from {settings_url}."`) and pass it from code
- HTML tags — Markdown where the field supports it, plain text elsewhere
- Leading or trailing whitespace
- A key that is not lowercase `a-z`, `0-9`, `_` or `-`, or that starts, ends or doubles a `_`/`-` — entity, state,
  action and field keys alike

## Core's shared strings

**Never use `[%key:...%]` references, and never create `strings.json`.** Both are Home Assistant **Core** build-time
features. Core compiles `strings.json` into `translations/en.json` and resolves the references on the way; a custom
integration has no such build step, so its `translations/*.json` is served exactly as written.

- ❌ `"stale_auth": "[%key:component::{domain}::config::error::invalid_auth%]"` — the UI shows that literal string
- ❌ `"off": "[%key:common::state::off%]"` — Core's `common` strings do not exist here
- ✅ Write out the full English text for every key, even when it duplicates another key or a Core string

**Copy Core's wording rather than inventing a variant.** The shared strings are under `common` in
`homeassistant/strings.json` of the installed Home Assistant package — `cannot_connect` is "Failed to connect",
`invalid_auth` is "Invalid authentication", the reauth title is "Authentication expired for {name}".

Symptom when this is wrong: the config flow shows raw keys (`username` instead of `Username`) instead of translated
labels.

## Entity translations

An entity's strings resolve only when its code sets `has_entity_name` to `True`, a `translation_key` that matches the
JSON key, and `translation_placeholders` for every placeholder in its name.

```json
"entity": {
  "sensor": {
    "air_quality": {
      "name": "Air quality index",
      "state": {
        "good": "Good",
        "poor": "Poor"
      }
    }
  }
}
```

## Markdown, proper nouns, form of address

- Markdown works in config and options `description`, `abort`, `progress` and `create_entry`, and in issue `title` and
  `description` — nowhere else.
- Never translate Home Assistant, Supervisor, brand and product names, or technical identifiers.
- **Use the form of address Home Assistant already uses in that language**, so the integration does not switch
  register mid-dialog: German "du" not "Sie", Spanish "tú" not "usted", French "vous" not "tu". The per-language
  agreements are on the [language guidelines](https://contributors.home-assistant.io/translate/reference/languages/)
  page; for a language it does not list, follow Core's own `translations/<lang>.json`. German additionally needs the
  correct imperative: "Gib deine Anmeldedaten ein", never "Gebe"
  ([Duden: Bildung des Imperativs](https://www.duden.de/sprachwissen/sprachratgeber/Bildung-des-Imperativs)).

## Multi-language files

A language file carries no key `en.json` lacks — that is a stale or misspelled key. A key it lacks falls back to
English, so a new key in `en.json` never requires touching another language file. A region-specific file (`fr-CA`,
`pt-BR`) falls back to **English**, not to its base language, for every key it lacks — so copy the base language's
string for each key that reads the same in the region, rather than leaving it out.

Only native speakers provide translations, and terminology stays consistent within and across languages.

## UI text style

English strings follow Home Assistant's [UI text guidelines](https://contributors.home-assistant.io/design/ui-text/)
and its [style guide](https://contributors.home-assistant.io/writing/reference/style/):

- American English, active voice, and "you"/"your" — never "the user"
- Sentence case for titles, labels, buttons and names: "Scan interval", not "Scan Interval"
- "Home Assistant" in full — never "HA" or "HASS"
- No "e.g.", "i.e." or "etc." — "like", "for example", "such as"
- The Oxford comma: "Zigbee, Z-Wave, and Matter"
- No all caps for emphasis
- "Select", not "click"
- Backticks around code-like values (entity IDs, file names); brand and protocol names as their owners write them
- Product terms in lowercase mid-sentence: automation, entity, device
- **Remove** when the thing still exists afterwards, **delete** when it is gone for good; **add** something that
  exists, **create** something new
- Short `state_badge` translations — one that overflows is visible only in the UI
- `data_description` for every field that is not self-explanatory

**One thing has one name**, the one the [glossary](https://contributors.home-assistant.io/glossary/) gives it. Never
the retired ones: "action", not "service"; "integration", not "component"; "app", not "add-on"; "dashboard", not
"Lovelace"; "backward-incompatible change", not "breaking change" (in text users read — commit footers keep
`BREAKING CHANGE:`).

## References

- [Translations](https://contributors.home-assistant.io/core/integrations/translations/) — the primary reference for
  the key structure; it documents Core's `strings.json` and `[%key:...%]` syntax, neither of which applies to a custom
  integration
- [UI text](https://contributors.home-assistant.io/design/ui-text/) and the
  [glossary](https://contributors.home-assistant.io/glossary/) — wording and terms
