---
name: "Translation Files"
description: "Which language files to touch, where the schema and Core's strings are, and where the UI text style also applies"
applyTo: "**/translations/*.json"
paths:
  - "**/translations/*.json"
---

# Translation Files Instructions

**Procedure:** `haci-translations` (plugin `haci-build`) — load it before adding or changing strings; it says which
keys a given change needs, which is where most missing-key findings from `script/hassfest` come from. The Home
Assistant rules for translation files are `haci.translations`, which loads with this file; what follows is only what
this project adds.

**Applies to:** `custom_components/<domain>/translations/*.json`

## Languages

- Update **`en.json` only**, and only when asked or at a feature milestone. **Never** edit or create another language
  file without asking — code works without translations, so business logic comes first. If the developer asks for
  another language, confirm which files before starting.
- Whether the integration should ship more languages is the developer's product decision:
  `haci-user-experience` (plugin `haci-build`).

## Where things are

- **Schema:** `schemas/json/translation_schema.json` defines the complete structure.
- **Core's shared strings** to copy wording from: `.venv/lib/python3.*/site-packages/homeassistant/strings.json`,
  under `common`.
- **The project's terms:** if `docs/development/GLOSSARY.md` exists, it decides the wording.
- **Validation:** `script/hassfest` checks keys and placeholders; `script/lint` formats the JSON with Prettier.
  `tests/test_translations.py` walks the running entities for enum states without a translation, attribute names
  without a display name, and orphaned keys — keep it passing.

## UI text style

The rules are in `haci.translations` (_UI text style_). Here they also cover:

- `docs/user/` pages — see [`blueprint.markdown`](blueprint.markdown.instructions.md#user-documentation-docsuser).
- The release notes prompt in `script/release-notes` (Rule 8), which carries a condensed copy for the update dialog.
  In the upstream template, a change to the style goes there too; a project adds its own wording rules to
  `.github/release-notes/prompt.md`, since the script is template-managed.
