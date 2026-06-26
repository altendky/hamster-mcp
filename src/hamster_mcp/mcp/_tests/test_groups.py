"""Tests for _core/groups.py."""

from __future__ import annotations

import json
from typing import Any

import pytest

from hamster_mcp.mcp._core.events import Done, FormatServiceResponse, ServiceCall
from hamster_mcp.mcp._core.groups import GroupRegistry, ServicesGroup, SourceGroup


def _parse_json_schema(result: str) -> dict[str, Any]:
    """Parse the leading JSON schema block from a schema() response."""
    _prefix, rest = result.split("```json\n", 1)
    json_block, _suffix = rest.split("\n```", 1)
    parsed = json.loads(json_block)
    assert isinstance(parsed, dict)
    return parsed


# --- SourceGroup protocol tests ---


class TestSourceGroupProtocol:
    """Tests for SourceGroup protocol compliance."""

    def test_services_group_is_source_group(self) -> None:
        """ServicesGroup implements SourceGroup protocol."""
        group = ServicesGroup.create({})
        assert isinstance(group, SourceGroup)

    def test_protocol_methods_exist(self) -> None:
        """Protocol methods have correct signatures."""
        group = ServicesGroup.create({})
        # These should not raise
        assert hasattr(group, "name")
        assert hasattr(group, "available")
        assert callable(group.search)
        assert callable(group.explain)
        assert callable(group.schema)
        assert callable(group.has_command)
        assert callable(group.parse_call_args)


# --- GroupRegistry tests ---


class TestGroupRegistryBasics:
    """Tests for GroupRegistry basic operations."""

    def test_register_adds_group(self) -> None:
        """register() adds group, retrievable via get()."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        assert registry.get("services") is group

    def test_register_duplicate_raises(self) -> None:
        """register() with duplicate name raises ValueError."""
        registry = GroupRegistry()
        group1 = ServicesGroup.create({})
        group2 = ServicesGroup.create({})
        registry.register(group1)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(group2)

    def test_update_group_replaces(self) -> None:
        """update_group() replaces existing group."""
        registry = GroupRegistry()
        group1 = ServicesGroup.create({"light": {"turn_on": {"description": "v1"}}})
        group2 = ServicesGroup.create({"light": {"turn_on": {"description": "v2"}}})
        registry.register(group1)
        registry.update_group(group2)
        assert registry.get("services") is group2

    def test_update_group_unknown_raises(self) -> None:
        """update_group() with unknown name raises ValueError."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        with pytest.raises(ValueError, match="not found"):
            registry.update_group(group)

    def test_get_unknown_returns_none(self) -> None:
        """get() with unknown name returns None."""
        registry = GroupRegistry()
        assert registry.get("unknown") is None

    def test_all_groups_returns_all(self) -> None:
        """all_groups() returns all registered groups."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        groups = registry.all_groups()
        assert len(groups) == 1
        assert group in groups


# --- Path resolution tests ---


class TestGroupRegistryPathResolution:
    """Tests for GroupRegistry.resolve_path()."""

    def test_resolve_services_path(self) -> None:
        """resolve_path() with services path."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        result = registry.resolve_path("services/light.turn_on")
        assert result is not None
        assert result[0] is group
        assert result[1] == "light.turn_on"

    def test_resolve_nested_path(self) -> None:
        """resolve_path() with nested path preserves slashes in in-group-path."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        # Register a fake "hass" group to test nested paths
        # For now, just test with services
        result = registry.resolve_path("services/selector/duration")
        assert result is not None
        assert result[0] is group
        assert result[1] == "selector/duration"

    def test_resolve_unknown_group(self) -> None:
        """resolve_path() with unknown group returns None."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        assert registry.resolve_path("unknown/foo") is None

    def test_resolve_empty_string(self) -> None:
        """resolve_path() with empty string returns None."""
        registry = GroupRegistry()
        assert registry.resolve_path("") is None

    def test_resolve_no_slash(self) -> None:
        """resolve_path() with no slash returns None."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        assert registry.resolve_path("services") is None

    def test_resolve_trailing_slash(self) -> None:
        """resolve_path() with trailing slash returns empty in-group-path."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        result = registry.resolve_path("services/")
        assert result is not None
        assert result[0] is group
        assert result[1] == ""


# --- Search aggregation tests ---


class TestGroupRegistrySearchAll:
    """Tests for GroupRegistry.search_all()."""

    def test_search_all_aggregates(self) -> None:
        """search_all() aggregates results from all groups."""
        registry = GroupRegistry()
        group = ServicesGroup.create(
            {"light": {"turn_on": {"description": "Turn on light"}}}
        )
        registry.register(group)
        result = registry.search_all("light")
        assert "## services" in result
        assert "light.turn_on" in result

    def test_search_all_with_group_filter(self) -> None:
        """search_all() with path_filter filters to specific group."""
        registry = GroupRegistry()
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        registry.register(group)
        result = registry.search_all("light", path_filter="services")
        assert "light.turn_on" in result

    def test_search_all_with_domain_filter(self) -> None:
        """search_all() with path_filter including domain passes to group."""
        registry = GroupRegistry()
        group = ServicesGroup.create(
            {
                "light": {"turn_on": {"description": "Turn on light"}},
                "switch": {"turn_on": {"description": "Turn on switch"}},
            }
        )
        registry.register(group)
        result = registry.search_all("turn", path_filter="services/light")
        assert "light.turn_on" in result
        assert "switch.turn_on" not in result

    def test_search_all_no_results(self) -> None:
        """search_all() with no results returns appropriate message."""
        registry = GroupRegistry()
        group = ServicesGroup.create({})
        registry.register(group)
        result = registry.search_all("nonexistent")
        assert "No commands found" in result

    def test_search_all_unknown_group_filter(self) -> None:
        """search_all() with unknown group filter returns no results."""
        registry = GroupRegistry()
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        registry.register(group)
        result = registry.search_all("light", path_filter="unknown")
        assert "No commands found" in result
        assert "unknown" in result


# --- ServicesGroup tests ---


class TestServicesGroupConstruction:
    """Tests for ServicesGroup construction."""

    def test_empty_descriptions(self) -> None:
        """Empty descriptions creates empty group."""
        group = ServicesGroup.create({})
        assert group.name == "services"
        assert group.available is True

    def test_with_services(self) -> None:
        """Services are indexed on construction."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        assert group.has_command("light.turn_on")


class TestServicesGroupSearch:
    """Tests for ServicesGroup.search()."""

    def test_search_by_name(self) -> None:
        """search() finds services by name."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        result = group.search("turn_on")
        assert "light.turn_on" in result

    def test_search_by_description(self) -> None:
        """search() finds services by description."""
        group = ServicesGroup.create(
            {"light": {"turn_on": {"description": "Illuminate"}}}
        )
        result = group.search("illuminate")
        assert "light.turn_on" in result

    def test_search_by_field_name(self) -> None:
        """search() finds services by field names."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "description": "Turn on",
                        "fields": {"brightness": {"description": "Level"}},
                    }
                }
            }
        )
        result = group.search("brightness")
        assert "light.turn_on" in result

    def test_search_case_insensitive(self) -> None:
        """search() is case insensitive."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        result = group.search("LIGHT")
        assert "light.turn_on" in result

    def test_search_with_domain_filter(self) -> None:
        """search() with path_filter filters to domain."""
        group = ServicesGroup.create(
            {
                "light": {"turn_on": {"description": "Light on"}},
                "switch": {"turn_on": {"description": "Switch on"}},
            }
        )
        result = group.search("turn_on", path_filter="light")
        assert "light.turn_on" in result
        assert "switch.turn_on" not in result

    def test_search_no_matches(self) -> None:
        """search() with no matches returns appropriate message."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        result = group.search("nonexistent")
        assert "No services found" in result


class TestServicesGroupExplain:
    """Tests for ServicesGroup.explain()."""

    def test_explain_known_service(self) -> None:
        """explain() returns description for known service."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "description": "Turn on a light",
                        "fields": {"brightness": {"description": "Brightness level"}},
                    }
                }
            }
        )
        result = group.explain("light.turn_on")
        assert result is not None
        assert "light.turn_on" in result
        assert "Turn on a light" in result
        assert "brightness" in result

    def test_explain_unknown_service(self) -> None:
        """explain() returns None for unknown service."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        assert group.explain("light.unknown") is None

    def test_explain_unknown_domain(self) -> None:
        """explain() returns None for unknown domain."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        assert group.explain("unknown.turn_on") is None

    def test_explain_invalid_path(self) -> None:
        """explain() returns None for path without dot."""
        group = ServicesGroup.create({"light": {"turn_on": {"description": "Turn on"}}})
        assert group.explain("light") is None

    def test_explain_includes_schema_references(self) -> None:
        """explain() includes schema references for selectors used."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "description": "Turn on the light",
                        "target": {"entity": {"domain": "light"}},
                        "fields": {
                            "brightness": {
                                "selector": {"number": {}},
                                "description": "Brightness level",
                            },
                            "transition": {
                                "selector": {"number": {}},
                            },
                            "effect": {
                                "selector": {"text": {}},
                            },
                        },
                    }
                }
            }
        )
        result = group.explain("light.turn_on")
        assert result is not None
        # Check for schema references section
        assert "Schema References" in result
        assert 'schema("light.turn_on")' in result
        # Check for selector type references
        assert 'schema("selector/number")' in result
        assert 'schema("selector/text")' in result
        # Check for target schema hint
        assert 'schema("selector/target")' in result

    def test_explain_includes_bare_target(self) -> None:
        """explain() includes target when HA describes a service with bare target:."""
        group = ServicesGroup.create({"homeassistant": {"turn_on": {"target": None}}})
        result = group.explain("homeassistant.turn_on")
        assert result is not None
        assert "### Target" in result
        assert "Accepts target specification" in result


class TestServicesGroupSchema:
    """Tests for ServicesGroup.schema()."""

    def test_schema_selector(self) -> None:
        """schema() with selector path returns selector description."""
        group = ServicesGroup.create({})
        result = group.schema("selector/duration")
        assert result is not None
        assert "duration" in result
        assert "hours" in result or "minutes" in result

    def test_schema_service(self) -> None:
        """schema() with service path returns field schema."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "fields": {
                            "brightness": {
                                "required": True,
                                "selector": {"number": {}},
                                "description": "Brightness level",
                            }
                        }
                    }
                }
            }
        )
        result = group.schema("light.turn_on")
        assert result is not None
        assert "brightness" in result
        assert "required" in result

        schema = _parse_json_schema(result)
        properties = schema["properties"]
        assert "data" in properties
        assert "brightness" in properties["data"]["properties"]
        assert schema["required"] == ["data"]
        assert properties["data"]["required"] == ["brightness"]

    def test_schema_target_only_service_includes_target(self) -> None:
        """schema() includes target for services with target but no data fields."""
        group = ServicesGroup.create({"homeassistant": {"turn_on": {"target": None}}})
        result = group.schema("homeassistant.turn_on")
        assert result is not None
        assert "has no parameters" not in result
        assert "arguments.target" in result

        schema = _parse_json_schema(result)
        properties = schema["properties"]
        assert "target" in properties
        assert "data" not in properties
        assert "entity_id" in properties["target"]["properties"]

    def test_schema_service_preserves_selector_constraints(self) -> None:
        """schema() merges safe selector config into field JSON Schema."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "target": {"entity": {"domain": "light"}},
                        "fields": {
                            "brightness_pct": {
                                "selector": {
                                    "number": {
                                        "min": 0,
                                        "max": 100,
                                        "unit_of_measurement": "%",
                                    }
                                }
                            },
                            "effect": {
                                "selector": {
                                    "select": {
                                        "options": ["rainbow", "pulse"],
                                    }
                                }
                            },
                            "entity_ids": {
                                "selector": {
                                    "entity": {
                                        "multiple": True,
                                        "filter": {"domain": "light"},
                                    }
                                }
                            },
                        },
                    }
                }
            }
        )
        result = group.schema("light.turn_on")
        assert result is not None
        schema = _parse_json_schema(result)
        assert schema["properties"]["target"]["x-ha-target-config"] == {
            "entity": {"domain": "light"}
        }
        data_properties = schema["properties"]["data"]["properties"]

        brightness = data_properties["brightness_pct"]
        assert brightness["minimum"] == 0
        assert brightness["maximum"] == 100
        assert brightness["x-ha-unit-of-measurement"] == "%"

        effect = data_properties["effect"]
        assert effect["enum"] == ["rainbow", "pulse"]
        assert effect["x-ha-options"] == ["rainbow", "pulse"]

        entity_ids = data_properties["entity_ids"]
        assert entity_ids["type"] == "array"
        assert entity_ids["items"]["type"] == "string"
        assert entity_ids["items"]["x-ha-filter"] == {"domain": "light"}
        assert entity_ids["x-ha-filter"] == {"domain": "light"}

    def test_schema_service_flattens_section_fields(self) -> None:
        """schema() flattens HA section fields into arguments.data."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "fields": {
                            "additional_fields": {
                                "name": "Additional fields",
                                "collapsed": True,
                                "fields": {
                                    "color_name": {
                                        "selector": {
                                            "select": {"options": ["red", "blue"]}
                                        }
                                    }
                                },
                            }
                        }
                    }
                }
            }
        )
        result = group.schema("light.turn_on")
        assert result is not None
        assert "fields flatten into `arguments.data`" in result

        schema = _parse_json_schema(result)
        data_properties = schema["properties"]["data"]["properties"]
        assert "additional_fields" not in data_properties
        assert data_properties["color_name"]["enum"] == ["red", "blue"]
        assert data_properties["color_name"]["x-ha-section"] == "Additional fields"

    def test_schema_unknown_service(self) -> None:
        """schema() returns None for unknown service."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        assert group.schema("light.unknown") is None

    def test_schema_unknown_selector(self) -> None:
        """schema() returns fallback for unknown selector."""
        group = ServicesGroup.create({})
        result = group.schema("selector/unknown_type")
        assert result is not None
        assert "Unknown selector type" in result

    def test_schema_selector_list(self) -> None:
        """schema("selector") returns list of all selector types."""
        group = ServicesGroup.create({})
        result = group.schema("selector")
        assert result is not None
        assert "x-selector-types" in result
        assert "duration" in result
        assert "entity" in result
        assert "target" in result

    def test_schema_selector_json_block(self) -> None:
        """schema() returns JSON Schema in code block."""
        group = ServicesGroup.create({})
        result = group.schema("selector/duration")
        assert result is not None
        assert "```json" in result
        assert '"x-selector-type": "duration"' in result
        assert '"type": "object"' in result

    def test_schema_target_has_target_keys(self) -> None:
        """schema("selector/target") includes x-target-keys annotation."""
        group = ServicesGroup.create({})
        result = group.schema("selector/target")
        assert result is not None
        assert "x-target-keys" in result
        assert "entity_id" in result
        assert "device_id" in result
        assert "area_id" in result

    def test_schema_service_returns_json_schema(self) -> None:
        """schema() with service path returns JSON Schema for fields."""
        group = ServicesGroup.create(
            {
                "light": {
                    "turn_on": {
                        "fields": {
                            "brightness": {
                                "required": True,
                                "selector": {"number": {}},
                                "description": "Brightness level",
                            },
                            "transition": {
                                "selector": {"number": {}},
                                "description": "Transition time",
                            },
                        }
                    }
                }
            }
        )
        result = group.schema("light.turn_on")
        assert result is not None
        assert "```json" in result
        assert '"type": "object"' in result
        assert '"properties"' in result
        assert '"brightness"' in result
        assert '"required"' in result


class TestServicesGroupHasCommand:
    """Tests for ServicesGroup.has_command()."""

    def test_has_command_known(self) -> None:
        """has_command() returns True for known service."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        assert group.has_command("light.turn_on") is True

    def test_has_command_unknown(self) -> None:
        """has_command() returns False for unknown service."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        assert group.has_command("light.unknown") is False

    def test_has_command_unknown_domain(self) -> None:
        """has_command() returns False for unknown domain."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        assert group.has_command("unknown.turn_on") is False

    def test_has_command_invalid_path(self) -> None:
        """has_command() returns False for path without dot."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        assert group.has_command("light") is False


class TestServicesGroupParseCallArgs:
    """Tests for ServicesGroup.parse_call_args()."""

    def test_valid_args_returns_service_call(self) -> None:
        """parse_call_args() with valid args returns ServiceCall."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args(
            "light.turn_on",
            {
                "target": {"entity_id": ["light.living_room"]},
                "data": {"brightness": 255},
            },
            user_id="test-user",
        )
        assert isinstance(result, ServiceCall)
        assert result.domain == "light"
        assert result.service == "turn_on"
        assert result.target == {"entity_id": ["light.living_room"]}
        assert result.data == {"brightness": 255}
        assert result.user_id == "test-user"
        assert isinstance(result.continuation, FormatServiceResponse)

    def test_missing_target_defaults_to_none(self) -> None:
        """parse_call_args() with missing target uses None."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args("light.turn_on", {"data": {}}, user_id=None)
        assert isinstance(result, ServiceCall)
        assert result.target is None

    def test_missing_data_defaults_to_empty(self) -> None:
        """parse_call_args() with missing data uses empty dict."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args("light.turn_on", {}, user_id=None)
        assert isinstance(result, ServiceCall)
        assert result.data == {}

    def test_invalid_target_type_error(self) -> None:
        """parse_call_args() with invalid target type returns error."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args(
            "light.turn_on", {"target": "invalid"}, user_id=None
        )
        assert isinstance(result, Done)
        assert result.result.is_error
        assert "target" in result.result.content[0].text.lower()  # type: ignore[union-attr]

    def test_invalid_data_type_error(self) -> None:
        """parse_call_args() with invalid data type returns error."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args(
            "light.turn_on", {"data": "invalid"}, user_id=None
        )
        assert isinstance(result, Done)
        assert result.result.is_error
        assert "data" in result.result.content[0].text.lower()  # type: ignore[union-attr]

    def test_unknown_service_error(self) -> None:
        """parse_call_args() with unknown service returns error."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args("light.unknown", {}, user_id=None)
        assert isinstance(result, Done)
        assert result.result.is_error
        assert "not found" in result.result.content[0].text.lower()  # type: ignore[union-attr]

    def test_invalid_path_error(self) -> None:
        """parse_call_args() with invalid path returns error."""
        group = ServicesGroup.create({"light": {"turn_on": {}}})
        result = group.parse_call_args("light", {}, user_id=None)
        assert isinstance(result, Done)
        assert result.result.is_error

    def test_supports_response_true_when_response_key_present(self) -> None:
        """Service with 'response' key sets supports_response=True."""
        # Service with response support (like weather.get_forecasts)
        group = ServicesGroup.create(
            {
                "weather": {
                    "get_forecasts": {
                        "description": "Get weather forecast",
                        "response": {"optional": False},  # SupportsResponse.ONLY
                    }
                }
            }
        )
        result = group.parse_call_args("weather.get_forecasts", {}, user_id=None)
        assert isinstance(result, ServiceCall)
        assert result.supports_response is True

    def test_supports_response_false_when_response_key_absent(self) -> None:
        """Service without 'response' key sets supports_response=False."""
        # Service without response support (like remote.send_command)
        group = ServicesGroup.create(
            {
                "remote": {
                    "send_command": {
                        "description": "Send command to remote",
                        "fields": {"command": {"required": True}},
                        # No "response" key - service doesn't support responses
                    }
                }
            }
        )
        result = group.parse_call_args("remote.send_command", {}, user_id=None)
        assert isinstance(result, ServiceCall)
        assert result.supports_response is False

    def test_supports_response_optional_true(self) -> None:
        """parse_call_args() handles SupportsResponse.OPTIONAL services."""
        # Service with optional response support
        group = ServicesGroup.create(
            {
                "calendar": {
                    "get_events": {
                        "description": "Get calendar events",
                        "response": {"optional": True},  # SupportsResponse.OPTIONAL
                    }
                }
            }
        )
        result = group.parse_call_args("calendar.get_events", {}, user_id=None)
        assert isinstance(result, ServiceCall)
        assert result.supports_response is True
