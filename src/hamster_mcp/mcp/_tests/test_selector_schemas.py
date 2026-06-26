"""Tests for selector schema catalog parity."""

from __future__ import annotations

import json
from typing import Any

from homeassistant.helpers.selector import SELECTORS

from hamster_mcp.mcp._core.groups import ServicesGroup
from hamster_mcp.mcp._core.selector_schemas import SELECTOR_SCHEMAS, SELECTOR_TYPES


def _parse_json_schema(result: str) -> dict[str, Any]:
    """Parse the leading JSON schema block from a schema() response."""
    _prefix, rest = result.split("```json\n", 1)
    json_block, _suffix = rest.split("\n```", 1)
    parsed = json.loads(json_block)
    assert isinstance(parsed, dict)
    return parsed


def test_selector_catalog_matches_home_assistant_registry() -> None:
    """The static schema catalog tracks HA's registered selector names."""
    assert set(SELECTOR_SCHEMAS) == set(SELECTORS)
    assert sorted(SELECTORS) == SELECTOR_TYPES


def test_schema_resolves_each_registered_selector() -> None:
    """schema("selector/<type>") works for every HA selector type."""
    group = ServicesGroup.create({})

    for selector_type in SELECTORS:
        result = group.schema(f"selector/{selector_type}")

        assert result is not None
        parsed = _parse_json_schema(result)
        assert parsed["x-selector-type"] == selector_type
        assert isinstance(parsed.get("description"), str)
