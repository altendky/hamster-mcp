# Reading Configurations

How to read the full definition of scripts, automations, and other
configurable entities --- as opposed to just their runtime state.

## State vs Configuration

Home Assistant exposes two distinct views of an entity:

- **State** (`hass/get_states`) --- The current runtime snapshot: whether a
  script is running, when it was last triggered, its mode, and
  `friendly_name`.  This tells you *what an entity is doing now* but not
  *what it is defined to do*.
- **Configuration** (domain-specific commands) --- The full definition: the
  action sequence of a script, the triggers and conditions of an automation,
  etc.  This tells you *how the entity is built*.

When you need to understand, review, or troubleshoot what a script or
automation actually does, use the configuration commands --- not `get_states`.

## Configuration Commands

### Scripts --- `script/config`

Returns the complete script definition including its action sequence.

```json
{
  "path": "hass/script/config",
  "arguments": {
    "entity_id": "script.watch_tv"
  }
}
```

The response contains the full config dict:

```json
{
  "config": {
    "alias": "Watch TV",
    "icon": "mdi:television",
    "mode": "single",
    "sequence": [
      {"action": "media_player.turn_on", "target": {"entity_id": "media_player.tv"}},
      {"delay": {"seconds": 2}},
      {"action": "media_player.select_source", "target": {"entity_id": "media_player.tv"}, "data": {"source": "HDMI 1"}}
    ]
  }
}
```

Key fields in the config: `alias`, `icon`, `description`, `mode`,
`sequence` (the full action list), `fields` (input parameters), and
`variables`.

### Automations --- `automation/config`

Returns the complete automation definition including triggers, conditions,
and actions.

```json
{
  "path": "hass/automation/config",
  "arguments": {
    "entity_id": "automation.turn_on_lights_at_sunset"
  }
}
```

The response contains the full config dict with `trigger`, `condition`,
`action`, `alias`, `description`, `mode`, and other fields.

## Discovering Entities to Read

To find all scripts or automations, filter entities from `get_states` by
domain prefix:

1. Call `hass/get_states` to get all entity states.
2. Filter for entities whose `entity_id` starts with `script.` or
   `automation.`.
3. Use the entity ID with the corresponding config command.

Alternatively, use `hass/config/entity_registry/list` and filter by
`entity_id` prefix for a lighter-weight listing.

## Trace Commands (Execution History)

Trace commands inspect **past executions** of scripts and automations.
They are the right tool for debugging *what happened during a run*, but
not for reading the current definition.

### `trace/list` --- List execution runs

```json
{
  "path": "hass/trace/list",
  "arguments": {
    "domain": "script",
    "item_id": "watch_tv"
  }
}
```

Returns a list of recent runs with `run_id`, `state` (stopped/running),
`script_execution` (finished/error), and timestamps.  Omit `item_id` to
list traces for all items in the domain.

### `trace/get` --- Get full execution trace

```json
{
  "path": "hass/trace/get",
  "arguments": {
    "domain": "script",
    "item_id": "watch_tv",
    "run_id": "abc123..."
  }
}
```

Returns the step-by-step execution trace including variable changes,
action results, errors, and timing for each step.

### Traces include a config snapshot --- but prefer `script/config`

Each trace embeds the entity's config as it existed at execution time.
**Do not** use `trace/get` as a way to read the current configuration.
The config in a trace may be out of date if the entity has been modified
since that run, and traces require the entity to have been executed at
least once.  Use `script/config` or `automation/config` instead.

## Quick Reference

| Goal | Command | Input |
| --- | --- | --- |
| Read a script's full definition | `hass/script/config` | `entity_id` |
| Read an automation's full definition | `hass/automation/config` | `entity_id` |
| See current state of any entity | `hass/get_states` | (none) |
| List execution history | `hass/trace/list` | `domain`, optional `item_id` |
| Inspect a specific execution run | `hass/trace/get` | `domain`, `item_id`, `run_id` |
