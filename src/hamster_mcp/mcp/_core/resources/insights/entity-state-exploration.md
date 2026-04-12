# Entity State Exploration

How to discover what information an entity provides by examining its state
directly, rather than guessing or searching elsewhere.

## The Problem

When asked "what is the state of X?" or "what is X doing?", it's tempting to
guess what attributes an entity might have.  This often leads to:

- Searching for specific information that may not exist
- Missing useful attributes that ARE available
- Using the wrong approach entirely (logs, greps, reverse-engineering)

## Why Exploration Matters

Home Assistant integrates with a huge variety of devices and platforms.  Each
integration exposes different attributes:

- A `media_player` from AndroidTV ADB has `app_id`, `app_name`, `source_list`
- A `media_player` from Chromecast has `media_title`, `media_artist`,
  `media_position`
- A `media_player` from a smart TV might have `source`, `sound_mode`,
  `volume_level`
- A `climate` entity might have `hvac_action`, `current_temperature`,
  `target_temp_high`

**There is no universal schema** --- each device and integration provides its
own set of attributes.  This makes it essential to explore what each entity
provides rather than assuming.

## Recommended Pattern

When you need information about an entity:

### 1. Fetch the Entity State First

Don't assume you know what attributes exist.  Query the entity directly:

```json
{
  "path": "hass/get_states",
  "arguments": {}
}
```

Then filter the results to your entity of interest, or use a domain filter
if looking for entities of a specific type.

### 2. Examine ALL Attributes

Read through everything that's returned.  Attributes are self-documenting:

- Names describe what they contain (`app_id`, `current_temperature`,
  `media_title`)
- Values show the current data format and content
- Often contains more useful information than expected

### 3. Let the State Inform Your Next Steps

The attributes tell you what information is available.  Adapt your approach
based on what you discover rather than forcing a preconceived plan.

## Anti-Patterns

Avoid these common mistakes:

| Anti-pattern | Why it's wrong |
| --- | --- |
| Searching logs for information | State data is real-time; logs are historical |
| Grepping for specific attribute names | You may miss the actual attribute name used |
| Assuming one integration's attributes apply to another | Integrations vary widely |
| Reverse-engineering from service calls | State is the source of truth |

## Example

**Question:** "What app is running on the Shield?"

### Wrong Approach

1. Search logbook for app launch events
2. Grep configuration files for "hulu"
3. Try to reverse-engineer from recent service calls
4. Guess that there might be an `app` attribute

### Right Approach

1. Fetch state of `media_player.shield_main_floor_adb`
2. Examine the returned attributes
3. See that it has `app_id: com.hulu.livingroomplus` and `app_name: Hulu (2)`
4. Answer found directly in entity state

## Integration-Specific Attributes

Some common domains and the kinds of attributes they typically expose:

| Domain | Common attributes | Notes |
| --- | --- | --- |
| `media_player` | `source`, `volume_level`, `media_*`, `app_*` | Varies heavily by integration |
| `climate` | `current_temperature`, `hvac_action`, `target_temp_*` | HVAC-specific fields |
| `sensor` | `unit_of_measurement`, `device_class`, `state_class` | Metadata about the reading |
| `light` | `brightness`, `color_temp`, `rgb_color`, `effect` | Depends on light capabilities |
| `cover` | `current_position`, `current_tilt_position` | Position as percentage |

**Always verify** --- the actual attributes depend on the specific device and
integration, not just the domain.

## Related Resources

- **Entity IDs** (`insights:entity-ids`) --- How to discover and reference
  entities
- **Service Targeting** (`insights:service-targeting`) --- How to target
  entities in service calls
