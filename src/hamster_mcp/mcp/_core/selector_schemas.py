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

import copy
from typing import Any


def _string_or_array(description: str) -> dict[str, Any]:
    """Create a schema for a value that can be string or array of strings."""
    return {
        "oneOf": [
            {"type": "string"},
            {"type": "array", "items": {"type": "string"}},
        ],
        "description": description,
    }


# JSON Schema definitions for each selector type.
# Keys match HA's selector type names exactly.
SELECTOR_SCHEMAS: dict[str, dict[str, Any]] = {
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
    "navigation": {
        "type": "string",
        "x-selector-type": "navigation",
        "description": "Navigation path within Home Assistant",
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
    "schedule": {
        "type": "object",
        "x-selector-type": "schedule",
        "description": "Schedule definition object",
    },
    "select": {
        "type": "string",
        "x-selector-type": "select",
        "description": (
            "One of a fixed set of string options (see service for valid values)"
        ),
    },
    "selector": {
        "type": "object",
        "x-selector-type": "selector",
        "description": "A selector definition object (meta-type)",
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
    "stt": {
        "type": "string",
        "x-selector-type": "stt",
        "description": "Speech-to-text engine ID",
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
    "tts": {
        "type": "string",
        "x-selector-type": "tts",
        "description": "Text-to-speech engine ID",
    },
    "ui_action": {
        "type": "object",
        "x-selector-type": "ui_action",
        "description": "UI action definition",
    },
    "ui_color": {
        "type": "string",
        "x-selector-type": "ui_color",
        "description": "UI color value",
    },
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
