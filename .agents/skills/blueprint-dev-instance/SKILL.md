---
name: blueprint-dev-instance
description: >-
  Run and read this repository's Home Assistant development instance — starting and restarting it with
  `script/develop`, sharing it with the developer, reading entity states, config entries, diagnostics and the log with
  `script/ha`, raising log levels, and knowing when `config/.storage/` is the right source instead. Use when asked to
  "start Home Assistant", "restart Home Assistant", "check the logs", "what does the entity show", "did the entry
  load", "get the diagnostics", "walk the config flow", "switch the Home Assistant version", or whenever a debugging
  step needs the running instance. SYMPTOMS — load this if you are about to: run `hass` or `pip` by hand instead of
  `script/develop`; run `script/develop` without checking `script/ha status` first; read or write
  `config/.storage/` while Home Assistant is running; ask the developer to read a state or download diagnostics from
  the UI; go through `ps` looking for who restarted the instance; or switch the Home Assistant environment unasked.
---

# The development instance

This repository runs one Home Assistant instance against `config/`, and `script/ha` reads and controls it. This skill
is how to use the two here; the debugging procedure itself — reading the log, localising a failure, the coordinator
failure contract, blocking calls — is `haci-coordinator-debug` (plugin `haci-build`). Every `script/ha` command and
option: [`ha-cli.md`](../blueprint-tooling/references/ha-cli.md).

## 1. Start and restart

```bash
./script/develop
```

Start it in the background — it runs until stopped. If Home Assistant is unresponsive or the port is held:

```bash
pkill -f "hass --config" || true && pkill -f "debugpy.*5678" || true && ./script/develop
```

Never a hand-rolled `hass` or `pip` invocation: `script/develop` sets up the venv, `PYTHONPATH`, port cleanup and
debugpy. Restart after **any** change to Python files, `manifest.json`, `services.yaml`, translations, or the config
flow. `script/ha reload` reloads the config entry without restarting the instance when the change is confined to entry
data or options — it does **not** re-import Python.

`script/ha` authenticates itself with a token `script/develop` mints; there is nothing to configure, and the token never
appears in a command line or in output.

```bash
script/ha status     # reachable, and which version
script/ha entries    # did the config entry actually load
```

## 2. The instance is shared

The developer restarts Home Assistant, clicks through the UI, and tries things out while you work — often precisely
because you are busy. **Never carry the instance's run state from one step to the next. Observe it.**

```bash
script/ha status    # exit 0 up, exit 2 down; `started` and `uptime` reveal a restart you did not do
```

- **A changed run state is the expected case, not a fault.** Running when you left it stopped means the developer
  started it. Do not go through `ps`, the process tree, or the log looking for an explanation — start it, or re-run
  your command, and carry on.
- **Spend at most one re-check on it.** If it still does not add up, say what you observed and continue with the task.
- **`./script/develop` takes the instance over — it is not "start it if it is not running".** It kills whatever is
  already bound to `config/` and starts its own, by design, because the log has to stream into the terminal that
  launched it. So the developer's terminal falls silent, and the live log they were watching is gone. Check
  `script/ha status` first and simply use the instance that is already there. Run `script/develop` only when it is
  genuinely down, or when a change forces a restart — and say that you are doing it. Never restart to tidy up.
- **The same happens in reverse**, and is equally fine: when the developer runs `./script/develop`, the instance you
  started dies and whatever file you were writing its log to stops growing. Re-orient.
- **Announce it before you take exclusive control.** That covers `script/setup/reset`, `script/ha token --rotate` and
  `--revoke`, and any loop that restarts repeatedly — all of them need Home Assistant stopped or undisturbed.
- **The Home Assistant environment is the developer's choice, never yours.** `script/ha-env use`,
  `script/ha-env refresh` and `script/develop --env` move every terminal, `script/test` and the instance to another
  version at once. Switch only when asked; `script/ha-env list` and `script/ha status` show what is active and who
  started the running instance. Never pass `--force` to `script/ha-env use` or `script/develop` without asking, and
  name the environment that is active when you finish.
- **`ha call`, `ha flow`, `ha reload` and `ha loglevel` change what the developer sees.** Cheap and reversible, but a
  config entry created by a flow stays until someone removes it.
- **State the run state when you finish — after checking it**, never from memory.

## 3. Ask the instance, or read the files?

While Home Assistant runs, `script/ha` is authoritative and `config/.storage/` is stale by design; with it stopped, the
files are the only source and accurate. The save delays behind that are in `haci-coordinator-debug`. What is specific
here:

- Everything about `config/` applies to `.local/ha-config/<name>/` while another environment is active;
  `script/ha status` names the directory as `config_dir`.
- The recorder's `commit_interval` is 30 s in `config/configuration.yaml`.
- `script/setup/seed-auth` takes Home Assistant's own `.ha_run.lock` before it writes into `config/.storage/`.
- `config/.storage/auth` and `dev_access_token` are read-denied: they are credentials, not debugging material.

| Question                                           | Use                                         |
| -------------------------------------------------- | ------------------------------------------- |
| What is this entity's state right now              | `script/ha states` / `entity`               |
| Did the entry load, and why not                    | `script/ha entries`                         |
| What unique IDs / registry flags does it have      | `script/ha entities`                        |
| What does the coordinator actually hand out        | `script/ha diagnostics`                     |
| Did an error happen                                | `script/ha logs`, then the log file         |
| Startup order, full traceback, surrounding context | `config/home-assistant.log`                 |
| The previous run                                   | `config/home-assistant.log.1`               |
| What a migration persisted                         | `config/.storage/*` — **with HA stopped**   |
| Whether a value changed over the last hours        | `script/ha watch`, or the recorder database |

## 4. Read the log

```bash
script/ha logs --level error        # then widen to --level warning
script/ha logs --grep coordinator
```

The raw stream is live in the terminal running `./script/develop`, and in `config/home-assistant.log` (previous run in
`config/home-assistant.log.1`):

```bash
rg -n "<domain>|Traceback|ERROR|WARNING" config/home-assistant.log | tail -50
```

Raise verbosity without restarting — this takes effect immediately and does not survive a restart:

```bash
script/ha loglevel custom_components.<domain>=debug homeassistant.helpers.update_coordinator=debug
```

A persistent level goes into the `logger:` block of `config/configuration.yaml`, which already sets
`custom_components.<domain>: debug`; Home Assistant's debug mode (`homeassistant: debug: true`) is on there too. A
`debug_console:` line in the same file adds the Python console.

## 5. Symptom → command

| Symptom                                           | Command                          |
| ------------------------------------------------- | -------------------------------- |
| Integration missing from the add-integration list | `script/ha setup-info`           |
| "Config entry not ready, retrying"                | `script/ha entries`              |
| Entry loads, all entities `unavailable`           | `script/ha states`               |
| Entities available but values `unknown`/`None`    | `script/ha entity sensor.<id>`   |
| Values never change                               | `script/ha watch --seconds 120`  |
| Endless reauth prompts                            | `script/ha entries`              |
| Config flow rejects valid input                   | `script/ha flow start`           |
| "Detected blocking call inside the event loop"    | `script/ha logs --level warning` |
| Entity duplicated after an update                 | `script/ha entities`             |

`script/ha entries` prints the entry `state` and its `reason`. `script/ha diagnostics | jq .data` shows the coordinator
payload without an edit and a restart, whenever the integration implements diagnostics. Which layer each symptom points
at is in `haci-coordinator-debug`.

## 6. Confirm the fix

```bash
script/lint && script/type-check
script/test
```

Restart, reproduce the original scenario, and confirm the log is clean:

```bash
pkill -f "hass --config" && ./script/develop     # any change to a .py file needs this
script/ha entries                                 # state: loaded, reason: -
script/ha states                                  # the values you expected
script/ha logs --level warning                    # nothing new
```

If the failure was data-shaped, `script/ha diagnostics | jq .data` should now show the corrected structure.
