"""JSON Schema definitions for Home Assistant selectors.

Provides structured schema information for HA selector types, enabling LLMs
to navigate type hierarchies on-demand via discriminator-style annotations.

The selector system uses a single-key object pattern as its discriminator:
{"selector": {"number": {...}}} - the key "number" identifies the type.

This module provides:
- SELECTOR_SCHEMAS: JSON Schema definitions per selector type
- SELECTOR_TYPES: List of all known selector types for x-selector-types annotation
- get_selector_schema(): Retrieve schema for a specific selector type
- get_selector_list_schema(): Get schema listing all available types
"""

from __future__ import annotations

from collections.abc import Mapping
import copy
from typing import Any

from homeassistant.helpers.selector import SELECTORS as HA_SELECTOR_TYPES


def _string_or_array(description: str) -> dict[str, Any]:
    """Create a schema for a value that can be string or array of strings."""
    return {
        "oneOf": [
            {"type": "string"},
            {"type": "array", "items": {"type": "string"}},
        ],
        "description": description,
    }


# JSON Schema definitions for known selector types.
# Schema bodies are curated for MCP clients rather than generated from HA's
# voluptuous validators. The public SELECTOR_SCHEMAS below is filtered to the
# selector types registered by the installed Home Assistant version.
_KNOWN_SELECTOR_SCHEMAS: dict[str, dict[str, Any]] = {
    "action": {
        "type": "array",
        "x-selector-type": "action",
        "description": "An automation action sequence (list of action objects)",
        "items": {"type": "object"},
    },
    "addon": {
        "type": "string",
        "x-selector-type": "addon",
        "description": "Home Assistant add-on slug",
    },
    "app": {
        "type": "string",
        "x-selector-type": "app",
        "description": "Home Assistant app slug",
    },
    "area": {
        "type": "string",
        "x-selector-type": "area",
        "description": "Area ID (e.g., 'living_room')",
    },
    "assist_pipeline": {
        "type": "string",
        "x-selector-type": "assist_pipeline",
        "description": "Assist pipeline ID",
    },
    "attribute": {
        "type": "string",
        "x-selector-type": "attribute",
        "description": "Entity attribute name",
    },
    "backup_location": {
        "type": "string",
        "x-selector-type": "backup_location",
        "description": "Backup location identifier",
    },
    "boolean": {
        "type": "boolean",
        "x-selector-type": "boolean",
        "description": "Boolean value: true or false",
    },
    "choose": {
        "x-selector-type": "choose",
        "description": (
            "Value matching one of the configured selector choices. "
            "Object-form values include active_choice and a property named "
            "for the active choice."
        ),
        "oneOf": [
            {
                "type": "object",
                "description": "Object form for an explicit active choice",
                "properties": {
                    "active_choice": {
                        "type": "string",
                        "description": (
                            "Choice key selected from the configured choices"
                        ),
                    }
                },
                "required": ["active_choice"],
                "additionalProperties": True,
            },
            {
                "not": {"type": "object"},
                "description": (
                    "Direct value form, validated against the configured "
                    "choice selectors in order"
                ),
            },
        ],
    },
    "color_rgb": {
        "type": "array",
        "x-selector-type": "color_rgb",
        "description": "RGB color as [R, G, B], each 0-255",
        "items": {"type": "integer", "minimum": 0, "maximum": 255},
        "minItems": 3,
        "maxItems": 3,
    },
    "color_temp": {
        "type": "integer",
        "x-selector-type": "color_temp",
        "description": "Color temperature in mireds (lower=cooler, higher=warmer)",
    },
    "condition": {
        "type": "object",
        "x-selector-type": "condition",
        "description": "An automation condition object",
    },
    "config_entry": {
        "type": "string",
        "x-selector-type": "config_entry",
        "description": "Config entry ID",
    },
    "constant": {
        "x-selector-type": "constant",
        "description": "A fixed constant value defined by the service",
    },
    "conversation_agent": {
        "type": "string",
        "x-selector-type": "conversation_agent",
        "description": "Conversation agent ID",
    },
    "country": {
        "type": "string",
        "x-selector-type": "country",
        "description": "ISO 3166-1 alpha-2 country code (e.g., 'US')",
        "pattern": "^[A-Z]{2}$",
    },
    "date": {
        "type": "string",
        "x-selector-type": "date",
        "description": "Date in ISO format",
        "format": "date",
        "examples": ["2024-01-15"],
    },
    "datetime": {
        "type": "string",
        "x-selector-type": "datetime",
        "description": "Date and time in ISO format",
        "format": "date-time",
        "examples": ["2024-01-15T14:30:00"],
    },
    "device": {
        "type": "string",
        "x-selector-type": "device",
        "description": "Device ID",
    },
    "duration": {
        "type": "object",
        "x-selector-type": "duration",
        "description": "Time duration with optional components",
        "properties": {
            "days": {"type": "number", "minimum": 0},
            "hours": {"type": "number", "minimum": 0},
            "minutes": {"type": "number", "minimum": 0},
            "seconds": {"type": "number", "minimum": 0},
            "milliseconds": {"type": "number", "minimum": 0},
        },
        "additionalProperties": False,
        "examples": [{"hours": 1, "minutes": 30}],
    },
    "entity": {
        "type": "string",
        "x-selector-type": "entity",
        "description": "Entity ID (e.g., 'light.living_room')",
        "pattern": "^[a-z_]+\\.[a-z0-9_]+$",
    },
    "file": {
        "type": "string",
        "x-selector-type": "file",
        "description": "File path or file content",
    },
    "floor": {
        "type": "string",
        "x-selector-type": "floor",
        "description": "Floor ID",
    },
    "icon": {
        "type": "string",
        "x-selector-type": "icon",
        "description": "Material Design Icon name (e.g., 'mdi:lightbulb')",
        "pattern": "^mdi:[a-z0-9-]+$",
    },
    "label": {
        "type": "string",
        "x-selector-type": "label",
        "description": "Label ID",
    },
    "language": {
        "type": "string",
        "x-selector-type": "language",
        "description": "Language code (e.g., 'en', 'de', 'fr')",
    },
    "location": {
        "type": "object",
        "x-selector-type": "location",
        "description": "Geographic location with coordinates",
        "properties": {
            "latitude": {"type": "number", "minimum": -90, "maximum": 90},
            "longitude": {"type": "number", "minimum": -180, "maximum": 180},
            "radius": {"type": "number", "minimum": 0},
        },
        "required": ["latitude", "longitude"],
        "examples": [{"latitude": 40.7128, "longitude": -74.006}],
    },
    "media": {
        "type": "object",
        "x-selector-type": "media",
        "description": "Media content specification",
        "properties": {
            "entity_id": {"type": "string"},
            "media_content_id": {"type": "string"},
            "media_content_type": {"type": "string"},
        },
    },
    "number": {
        "type": "number",
        "x-selector-type": "number",
        "description": "Numeric value (may have min/max/step constraints per service)",
    },
    "object": {
        "type": "object",
        "x-selector-type": "object",
        "description": "Arbitrary JSON object",
    },
    "qr_code": {
        "type": "string",
        "x-selector-type": "qr_code",
        "description": "QR code data",
    },
    "select": {
        "type": "string",
        "x-selector-type": "select",
        "description": (
            "One of a fixed set of string options (see service for valid values)"
        ),
    },
    "state": {
        "type": "string",
        "x-selector-type": "state",
        "description": "Entity state value",
    },
    "statistic": {
        "type": "string",
        "x-selector-type": "statistic",
        "description": "Statistic ID for long-term statistics",
    },
    "target": {
        "type": "object",
        "x-selector-type": "target",
        "x-target-keys": ["entity_id", "device_id", "area_id", "floor_id", "label_id"],
        "description": "Service target specification",
        "properties": {
            "entity_id": _string_or_array("Entity ID(s) to target"),
            "device_id": _string_or_array("Device ID(s) to target"),
            "area_id": _string_or_array("Area ID(s) to target"),
            "floor_id": _string_or_array("Floor ID(s) to target"),
            "label_id": _string_or_array("Label ID(s) to target"),
        },
        "additionalProperties": False,
    },
    "template": {
        "type": "string",
        "x-selector-type": "template",
        "description": "Jinja2 template string (rendered at execution time)",
        "examples": ["{{ states('sensor.temperature') | float > 25 }}"],
    },
    "text": {
        "type": "string",
        "x-selector-type": "text",
        "description": "Text string (may have multiline or regex constraints)",
    },
    "theme": {
        "type": "string",
        "x-selector-type": "theme",
        "description": "Theme name",
    },
    "time": {
        "type": "string",
        "x-selector-type": "time",
        "description": "Time in HH:MM:SS format",
        "pattern": "^\\d{2}:\\d{2}(:\\d{2})?$",
        "examples": ["14:30:00"],
    },
    "trigger": {
        "type": "object",
        "x-selector-type": "trigger",
        "description": "An automation trigger definition",
    },
}

SELECTOR_SCHEMAS: dict[str, dict[str, Any]] = {
    selector_type: schema
    for selector_type, schema in _KNOWN_SELECTOR_SCHEMAS.items()
    if selector_type in HA_SELECTOR_TYPES
}

# Sorted list of all selector types for discovery
SELECTOR_TYPES: list[str] = sorted(SELECTOR_SCHEMAS.keys())


def get_selector_schema(selector_type: str) -> dict[str, Any] | None:
    """Get the JSON Schema for a specific selector type.

    Args:
        selector_type: The selector type name (e.g., 'duration', 'entity')

    Returns:
        JSON Schema dict for the selector, or None if unknown type.
    """
    return SELECTOR_SCHEMAS.get(selector_type)


def get_configured_selector_schema(
    selector_type: str,
    selector_config: object,
) -> dict[str, Any] | None:
    """Get a selector schema with service-specific selector config applied.

    Home Assistant selector config is partly runtime shape and partly frontend UI
    metadata. This applies safe JSON Schema constraints and preserves the full
    HA config under ``x-ha-selector-config`` for callers that need the original
    details.
    """
    base_schema = get_selector_schema(selector_type)
    if base_schema is None:
        return None

    schema = copy.deepcopy(base_schema)
    if not isinstance(selector_config, Mapping):
        return schema

    config = dict(selector_config)
    if config:
        schema["x-ha-selector-config"] = copy.deepcopy(config)

    if selector_type in {"number", "color_temp"}:
        _apply_numeric_config(schema, config)
    elif selector_type == "select":
        _apply_select_config(schema, config)
    elif selector_type == "constant":
        _apply_constant_config(schema, config)

    if filter_config := config.get("filter"):
        schema["x-ha-filter"] = copy.deepcopy(filter_config)

    if selector_type in {"area", "device", "entity", "floor", "label", "select"}:
        _apply_multiple_config(schema, config)

    return schema


def _apply_numeric_config(schema: dict[str, Any], config: dict[object, object]) -> None:
    """Apply numeric selector config as JSON Schema constraints."""
    if isinstance(config.get("min"), int | float):
        schema["minimum"] = config["min"]
    if isinstance(config.get("max"), int | float):
        schema["maximum"] = config["max"]

    step = config.get("step")
    if isinstance(step, int | float) and step > 0:
        schema["multipleOf"] = step

    unit = config.get("unit_of_measurement", config.get("unit"))
    if isinstance(unit, str):
        schema["x-ha-unit-of-measurement"] = unit


def _apply_select_config(schema: dict[str, Any], config: dict[object, object]) -> None:
    """Apply select options when they form a closed set."""
    options = config.get("options")
    if not isinstance(options, list):
        return

    schema["x-ha-options"] = copy.deepcopy(options)
    values: list[object] = []
    for option in options:
        if isinstance(option, str | int | float | bool):
            values.append(option)
        elif isinstance(option, Mapping) and "value" in option:
            values.append(option["value"])
        else:
            return

    if values and not config.get("custom_value", False):
        schema["enum"] = values


def _apply_constant_config(
    schema: dict[str, Any], config: dict[object, object]
) -> None:
    """Apply constant selector value."""
    if "value" not in config:
        return

    value = config["value"]
    schema["const"] = value
    json_type = _json_type(value)
    if json_type is not None:
        schema["type"] = json_type


def _apply_multiple_config(
    schema: dict[str, Any], config: dict[object, object]
) -> None:
    """Convert scalar selector output to an array when HA allows multiples."""
    if config.get("multiple") is not True or schema.get("type") == "array":
        return

    item_schema = copy.deepcopy(schema)
    description = schema.get("description")
    schema.clear()
    schema["type"] = "array"
    schema["items"] = item_schema
    if isinstance(description, str):
        schema["description"] = f"List of {description[:1].lower()}{description[1:]}"

    for key in (
        "x-selector-type",
        "x-ha-selector-config",
        "x-ha-options",
        "x-ha-filter",
    ):
        if key in item_schema:
            schema[key] = copy.deepcopy(item_schema[key])


def _json_type(value: object) -> str | None:
    """Return the JSON Schema type name for a Python value."""
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return None


def get_selector_list_schema() -> dict[str, Any]:
    """Get a schema listing all available selector types.

    Returns:
        Schema with x-selector-types annotation for type discovery.
    """
    return {
        "x-selector-types": SELECTOR_TYPES,
        "description": (
            "Home Assistant selector types. Use schema('selector/<type>') "
            "to get the full JSON Schema for a specific type."
        ),
    }


def get_target_schema() -> dict[str, Any]:
    """Get the JSON Schema for the target specification.

    This is the discriminated union for service targeting.
    Returns a deep copy to prevent mutation of the module-level constant.
    """
    return copy.deepcopy(SELECTOR_SCHEMAS["target"])
