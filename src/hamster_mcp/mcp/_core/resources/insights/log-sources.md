# Log Sources

Which log source to query when investigating events, errors, or
automation behavior in Home Assistant.

## Overview

Home Assistant provides multiple log sources, each capturing different
types of information.  Choosing the right source avoids wasted searches.

| Source | Contains | Use for |
| --- | --- | --- |
| `hass/logbook/get_events` | Entity state changes | "When did the light turn on?", "What changed recently?" |
| `hass/system_log/list` | Errors, warnings, integration issues | "Why did this fail?", "Are there any errors?" |
| `hass/trace/list` + `hass/trace/get` | Script/automation execution traces | "What did this script do?", "Why did the automation fail?" |

## What's NOT Logged

Some user interactions bypass logging entirely:

- **UI button interactions** from custom cards (e.g., universal-remote-card)
  execute actions directly without logging
- **Frontend events** (dashboard interactions, card clicks) do not appear
  in backend logs
- **Service calls from cards** may not appear unless they cause state changes

To understand what a UI button sends, examine the card or dashboard
configuration rather than searching logs.

## Choosing the Right Source

### For "why did this fail?"

Check `hass/system_log/list` first.  This returns errors, warnings, and
integration issues:

```json
{
  "path": "hass/system_log/list",
  "arguments": {}
}
```

### For "what happened to entity X?"

Use `hass/logbook/get_events` with an entity filter:

```json
{
  "path": "hass/logbook/get_events",
  "arguments": {
    "start_time": "2026-04-11T00:00:00Z",
    "entity_ids": ["light.living_room"]
  }
}
```

### For "what did script Y do?"

Use `hass/trace/list` to find execution runs, then `hass/trace/get` for
details:

```json
{
  "path": "hass/trace/list",
  "arguments": {
    "domain": "script",
    "item_id": "my_script"
  }
}
```

```json
{
  "path": "hass/trace/get",
  "arguments": {
    "domain": "script",
    "item_id": "my_script",
    "run_id": "TRACE_ID_FROM_LIST"
  }
}
```

### For "what does this button send?"

Logs will not help.  Instead, read the dashboard or card configuration
to see what action the button invokes:

- For Lovelace dashboards: Check `.storage/lovelace*` files or
  `hass/lovelace/config`
- For custom cards: Examine the card's YAML configuration in the dashboard

## Related Resources

- *Services and Hass Groups* --- How to call services once you know what
  to invoke
- *Reading Configurations* --- How to read script and automation definitions
