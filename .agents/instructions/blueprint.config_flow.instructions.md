---
name: "Config Flow"
description: "Where the config flow's modules live in this project, its unique ID policy, and how to walk a flow"
applyTo: "custom_components/**/config_flow_handler/**/*.py, custom_components/**/config_flow.py"
paths:
  - "custom_components/**/config_flow_handler/**/*.py"
  - "custom_components/**/config_flow.py"
---

# Config Flow Instructions

**Procedure:** `haci-config-flow` (plugin `haci-build`) — load it before touching setup, options, reauth, reconfigure,
discovery or subentries. The Home Assistant rules for config flow files are `haci.config-flow`, which loads with this
file; what follows is only what this project adds.

## Package layout

The real flow lives in `config_flow_handler/`. The top-level `config_flow.py` is a thin shim Home Assistant discovers —
leave it alone. The template ships `__init__.py`, `config_flow.py`, `options_flow.py`, `schemas/config.py`,
`schemas/options.py` and `validators/credentials.py`; create the rest when something needs them, rather than leaving
empty scaffolding behind.

```text
config_flow_handler/
├── __init__.py          # exports
├── config_flow.py       # user, reauth, reauth_confirm, reconfigure, discovery steps
├── options_flow.py      # post-setup options, only when there is something to tune
├── handler.py           # logic shared between the flows above
├── subentry_flow.py     # multi-device / multi-account subentries
├── schemas/
│   ├── config.py        # probatio schemas for setup steps
│   └── options.py       # probatio schemas for the options flow
└── validators/
    ├── credentials.py   # "can we actually talk to it" checks
    └── sanitizers.py    # input normalisation (strip, lowercase host, …)
```

- A new option's field goes into `schemas/config.py` or `schemas/options.py`; an integration without options yet
  creates `options_flow.py` and `schemas/options.py` with its first real option.
- Its `data` and `data_description` strings go into `translations/en.json` only
  (`haci-translations`).

## Unique IDs

- **Never** use an email address or a username, not even for a cloud service where Core's docs accept them — the user
  can change both at the provider. Use the account ID the API returns.

## Validate and walk the flow

```bash
script/lint && script/type-check
script/hassfest          # cross-checks every step/error/abort key against translations
script/test
```

Then restart the instance and walk every flow you touched from the terminal before the browser:

```bash
script/ha flow start                              # or --reconfigure
script/ha flow step <flow_id> host=192.0.2.10 username=admin password="$PASSWORD"
script/ha flow options                            # then step through it the same way
script/ha entries                                 # the entry exists and loaded
```

Each step prints its `step_id`, any `errors`, and every field with its type and default. Full reference:
[`references/ha-cli.md`](../skills/blueprint-tooling/references/ha-cli.md).
