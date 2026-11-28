---
name: "Home Assistant repairs"
description: "Creating repair issues, implementing RepairsFlow, translations, and the issue lifecycle"
applyTo: "custom_components/**/repairs.py"
paths:
  - "custom_components/**/repairs.py"
---

<!-- haci-vendor: jpawlowski/ha-custom-integration-skills@v0.5.3 plugins/haci-quality/skills/haci-breaking-changes/references/rules.md sha256:95be685ee291732c — written by script/haci-vendor, do not edit -->

# Repair issues and flows

Procedure: the `haci-breaking-changes` skill (plugin `haci-quality`) — what a repair issue is _for_, a migration or a
deprecation the user has to act on, and the warn-first policy that comes before either.

Upstream: [Repairs](https://contributors.home-assistant.io/core/integrations/repairs/).

## What a repair is

A repair issue tells the user about a problem they can act on — expired credentials, a deprecated setting, a device
that needs a firmware update. A fixable one has a **Fix** button that starts a repair flow.

- **Location:** `repairs.py` at the integration root, never inside the config flow package.
- **Base class:** `homeassistant.components.repairs.RepairsFlow`, not `ConfigFlow`.
- **Lifecycle:** the integration creates the issue → the user selects **Fix** → `async_create_fix_flow()` returns the
  flow → the flow ends with `async_create_entry()`, and Home Assistant deletes the issue itself. An abort, including a
  hand-over through `next_flow`, leaves it in place.
- **Only raise an issue the user can act on.** Something broken that they cannot fix themselves is a log entry, not a
  repair. A normal configuration change is a reconfigure or options flow, not a repair.

## Creating issues

```python
from homeassistant.helpers import issue_registry as ir

ir.async_create_issue(
    hass,
    DOMAIN,
    f"deprecated_option_{entry.entry_id}",
    is_fixable=True,  # Shows "Fix"; requires a fix flow
    severity=ir.IssueSeverity.WARNING,
    translation_key="deprecated_option",
    translation_placeholders={"key": "value"},
    breaks_in_ha_version="2027.1",  # When this stops working
    learn_more_url="https://…",  # The integration's own documentation
    issue_domain=DOMAIN,  # Only when raising on another integration's behalf
    data={"entry_id": entry.entry_id},  # Reaches async_create_fix_flow
)
```

- **An issue about one config entry carries the entry ID in its `issue_id`.** Issue IDs are unique per domain only;
  without it, the issues of two entries overwrite each other — re-creating an issue with a different
  `config_entry_id` moves it to the new entry and is logged. Put the entry ID in `data` as well — the repair flow reads
  it from there, not from `self.handler`, which is the domain.
- **Entry-scoped issues:** `config_entry_id=entry.entry_id` on `async_create_issue` ties the issue to the entry —
  hidden while it is disabled, deleted when it is removed, so no cleanup code is needed — and
  `ir.async_refresh_issues()` re-checks a whole set of issues (one per device, say) without deleting and re-creating
  the ones that still apply. Never delete an entry's issues in `async_unload_entry`: a reload unloads too, and every
  issue the user ignored would come back.
- `is_persistent=True` marks an issue that only exists because it was observed once — an update that failed, an
  unknown action in an automation — so it must survive a restart. Leave it off for anything the integration re-checks
  on its own, such as a deprecated option found during setup; that one comes back by itself if it is still true.
- **Ignoring is sticky.** An ignored issue stays ignored across restarts until it is deleted — by the integration or by
  the user completing its flow — and then created again. Re-creating the same `issue_id` on every coordinator update is
  therefore harmless; inventing a new ID each time defeats the user's choice, and so does deleting an issue only to
  create it again.
- `ir.async_create_issue` must run in the event loop. From a worker thread use `ir.create_issue` / `ir.delete_issue`.
- **Pick severity by tense, not by urgency.** `ERROR` — something is broken **now** and needs attention; `WARNING` —
  something breaks **later** (an API shutdown, a removal). A deprecation issue is `WARNING` while the old behaviour
  still works and becomes `ERROR` once it has stopped — the removal shipped, or a migration failed. `CRITICAL` is
  reserved for true panic and has no use in a custom integration.
- Set `is_fixable=True` only when a fix flow exists for the issue.
- **Delete the issue yourself** when the problem goes away on its own, or after a fix that ended in an abort. A flow that
  ends in `async_create_entry` needs no delete.

## Repair flows

**Without a `repairs.py`, Home Assistant answers every fixable issue with `ConfirmRepairFlow`.** Once the file exists,
`async_create_fix_flow` decides for every issue of the domain, so it returns `ConfirmRepairFlow()` for the ones that only
need an acknowledgement:

```python
async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create the flow that fixes issue_id."""
    if issue_id.startswith("deprecated_option_"):
        return DeprecatedOptionRepairFlow()
    return ConfirmRepairFlow()
```

Write a flow class only when the user has something to enter or choose:

```python
class DeprecatedOptionRepairFlow(RepairsFlow):
    """Move the deprecated option to its replacement."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> RepairsFlowResult:
        """Confirm, then apply the fix."""
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(str(self.data["entry_id"]))
            # Apply the fix to entry, then:
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="init")
```

- Home Assistant sets `self.issue_id` and `self.data` (the issue's `data`) on the flow after `async_create_fix_flow`
  returns it — never set them yourself; setting `self.issue_id` is logged and stops working in 2027.12. Read the ID
  from `self.issue_id`, not from `user_input`. `self.handler` is the **domain**, never an entry ID.
- A repair flow started from code takes the issue ID in `context={"issue_id": …}`, not in `data`.
- The form mechanics are Data Entry Flow's, identical to the config flow's. What differs: `async_create_entry(data={})`
  always takes an **empty** dict, and it removes the issue on its own.
- Validate user input before applying the fix, and keep a repair to one or two steps.
- After a configuration change, reload with `hass.config_entries.async_schedule_reload(entry.entry_id)`, which also
  cancels a pending setup retry.
- **Redirecting to reauth:** call `entry.async_start_reauth(self.hass)`, then `return self.async_create_entry(data={})`
  — the issue goes with the `create_entry`.
- **Continuing in a reconfigure or options flow:** hand over with
  `self.async_abort(reason=…, next_flow=(FlowType.CONFIG_FLOW, flow_id))`. An abort does not remove the issue: delete
  it in the step that completes the fix.

## Translations

Every issue has translations; none is created without them. **Exactly one of `fix_flow` and `description` per issue** —
never both, and which one depends on `is_fixable`. `title` is required; `short_title` is an optional shorter form for
tight spaces.

**What the text says.** The description or the flow step explains what is happening and why it matters, gives the exact
steps to fix it — a numbered list when there are several, and how, not just "update the firmware" — says what to expect
afterwards, and names the device or entry concerned through a placeholder.

Not fixable — the user reads it and acts elsewhere:

```json
{
  "issues": {
    "api_key_expired": {
      "title": "Issue title",
      "description": "Description with {placeholder}"
    }
  }
}
```

Fixable — the flow's own steps carry the text. `ConfirmRepairFlow` shows its form in step `confirm`; a custom flow uses
the `step_id`s it passes to `async_show_form`:

```json
{
  "issues": {
    "deprecated_option": {
      "title": "Issue title",
      "fix_flow": {
        "step": {
          "confirm": {
            "title": "Repair step title",
            "description": "Instructions"
          }
        }
      }
    }
  }
}
```
