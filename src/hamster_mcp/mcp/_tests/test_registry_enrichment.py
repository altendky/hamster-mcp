"""Tests for registry_enrichment module."""

from __future__ import annotations

import pytest

from hamster_mcp.mcp._core.registry_enrichment import (
    ENRICHMENT_KEY,
    AreaInfo,
    DeviceInfo,
    EntityInfo,
    FloorInfo,
    LabelInfo,
    RegistryContext,
    enrich_data,
)


@pytest.fixture
def sample_context() -> RegistryContext:
    """Create a sample registry context for testing."""
    return RegistryContext(
        entities={
            "light.living_room": EntityInfo(
                name="Living Room Ceiling Light",
                device_id="device_123",
                area_id="area_living",
                labels=("smart_lights", "downstairs"),
            ),
            "sensor.temperature": EntityInfo(
                name="Temperature Sensor",
                device_id="device_456",
                area_id=None,  # No direct area, uses device's area
                labels=(),
            ),
            "switch.no_device": EntityInfo(
                name="Standalone Switch",
                device_id=None,
                area_id="area_kitchen",
                labels=(),
            ),
        },
        devices={
            "device_123": DeviceInfo(
                name="Philips Hue Bridge",
                area_id="area_living",
                labels=("zigbee",),
            ),
            "device_456": DeviceInfo(
                name="Aqara Hub",
                area_id="area_bedroom",
                labels=(),
            ),
        },
        areas={
            "area_living": AreaInfo(
                name="Living Room",
                floor_id="floor_1",
                labels=(),
            ),
            "area_bedroom": AreaInfo(
                name="Bedroom",
                floor_id="floor_2",
                labels=(),
            ),
            "area_kitchen": AreaInfo(
                name="Kitchen",
                floor_id="floor_1",
                labels=(),
            ),
        },
        floors={
            "floor_1": FloorInfo(name="Ground Floor"),
            "floor_2": FloorInfo(name="First Floor"),
        },
        labels={
            "smart_lights": LabelInfo(name="Smart Lights"),
            "downstairs": LabelInfo(name="Downstairs"),
            "zigbee": LabelInfo(name="Zigbee Devices"),
        },
    )


class TestEnrichData:
    """Tests for the enrich_data function."""

    def test_scalar_passthrough(self, sample_context: RegistryContext) -> None:
        """Scalar values pass through unchanged."""
        assert enrich_data("hello", sample_context) == "hello"
        assert enrich_data(42, sample_context) == 42
        assert enrich_data(3.14, sample_context) == 3.14
        assert enrich_data(True, sample_context) is True
        assert enrich_data(None, sample_context) is None

    def test_empty_dict(self, sample_context: RegistryContext) -> None:
        """Empty dict returns empty dict."""
        assert enrich_data({}, sample_context) == {}

    def test_dict_without_enrichable_keys(
        self, sample_context: RegistryContext
    ) -> None:
        """Dict without entity_id/device_id/area_id is unchanged."""
        data = {"state": "on", "brightness": 255}
        result = enrich_data(data, sample_context)
        assert result == {"state": "on", "brightness": 255}

    def test_enrich_entity_id(self, sample_context: RegistryContext) -> None:
        """Entity ID enrichment adds name, device, area, floor, labels."""
        data = {"entity_id": "light.living_room", "state": "on"}
        result = enrich_data(data, sample_context)

        assert result["entity_id"] == "light.living_room"
        assert result["state"] == "on"
        assert ENRICHMENT_KEY in result

        enrichment = result[ENRICHMENT_KEY]
        assert enrichment["name"] == "Living Room Ceiling Light"
        assert enrichment["device_name"] == "Philips Hue Bridge"
        assert enrichment["area_name"] == "Living Room"
        assert enrichment["floor_name"] == "Ground Floor"
        assert "Smart Lights" in enrichment["labels"]
        assert "Downstairs" in enrichment["labels"]
        # Device labels should also be included
        assert "Zigbee Devices" in enrichment["labels"]

    def test_enrich_entity_without_direct_area(
        self, sample_context: RegistryContext
    ) -> None:
        """Entity without direct area uses device's area."""
        data = {"entity_id": "sensor.temperature"}
        result = enrich_data(data, sample_context)

        enrichment = result[ENRICHMENT_KEY]
        assert enrichment["name"] == "Temperature Sensor"
        assert enrichment["device_name"] == "Aqara Hub"
        # Should use device's area since entity has no direct area
        assert enrichment["area_name"] == "Bedroom"
        assert enrichment["floor_name"] == "First Floor"

    def test_enrich_entity_without_device(
        self, sample_context: RegistryContext
    ) -> None:
        """Entity without device still enriches area."""
        data = {"entity_id": "switch.no_device"}
        result = enrich_data(data, sample_context)

        enrichment = result[ENRICHMENT_KEY]
        assert enrichment["name"] == "Standalone Switch"
        assert "device_name" not in enrichment
        assert enrichment["area_name"] == "Kitchen"

    def test_unknown_entity_id(self, sample_context: RegistryContext) -> None:
        """Unknown entity_id produces no enrichment."""
        data = {"entity_id": "light.unknown", "state": "off"}
        result = enrich_data(data, sample_context)

        # No enrichment key when entity not found
        assert result == {"entity_id": "light.unknown", "state": "off"}

    def test_enrich_device_id(self, sample_context: RegistryContext) -> None:
        """Device ID enrichment adds device_name, area, floor."""
        data = {"device_id": "device_123", "manufacturer": "Philips"}
        result = enrich_data(data, sample_context)

        enrichment = result[ENRICHMENT_KEY]
        assert enrichment["device_name"] == "Philips Hue Bridge"
        assert enrichment["area_name"] == "Living Room"
        assert enrichment["floor_name"] == "Ground Floor"

    def test_enrich_area_id(self, sample_context: RegistryContext) -> None:
        """Area ID enrichment adds area_name and floor_name."""
        data = {"area_id": "area_living", "entity_count": 5}
        result = enrich_data(data, sample_context)

        enrichment = result[ENRICHMENT_KEY]
        assert enrichment["area_name"] == "Living Room"
        assert enrichment["floor_name"] == "Ground Floor"

    def test_entity_takes_precedence_over_device(
        self, sample_context: RegistryContext
    ) -> None:
        """When both entity_id and device_id present, entity enrichment is used."""
        data = {
            "entity_id": "light.living_room",
            "device_id": "device_456",  # Different device
        }
        result = enrich_data(data, sample_context)

        enrichment = result[ENRICHMENT_KEY]
        # Should use entity's device, not the explicit device_id
        assert enrichment["device_name"] == "Philips Hue Bridge"

    def test_enrich_list(self, sample_context: RegistryContext) -> None:
        """List of dicts are each enriched."""
        data = [
            {"entity_id": "light.living_room", "state": "on"},
            {"entity_id": "sensor.temperature", "state": "21"},
        ]
        result = enrich_data(data, sample_context)

        assert len(result) == 2
        assert result[0][ENRICHMENT_KEY]["name"] == "Living Room Ceiling Light"
        assert result[1][ENRICHMENT_KEY]["name"] == "Temperature Sensor"

    def test_enrich_nested_structure(self, sample_context: RegistryContext) -> None:
        """Nested structures are recursively enriched."""
        data = {
            "result": {
                "entities": [
                    {"entity_id": "light.living_room"},
                ]
            }
        }
        result = enrich_data(data, sample_context)

        # The nested entity should be enriched
        entity = result["result"]["entities"][0]
        assert ENRICHMENT_KEY in entity
        assert entity[ENRICHMENT_KEY]["name"] == "Living Room Ceiling Light"

    def test_empty_context(self) -> None:
        """Empty context produces no enrichment."""
        empty_context = RegistryContext.empty()
        data = {"entity_id": "light.living_room", "state": "on"}
        result = enrich_data(data, empty_context)

        # No enrichment when context is empty
        assert result == {"entity_id": "light.living_room", "state": "on"}

    def test_unresolved_label_ids(self) -> None:
        """Unresolved label IDs are included as-is."""
        context = RegistryContext(
            entities={
                "light.test": EntityInfo(
                    name="Test Light",
                    device_id=None,
                    area_id=None,
                    labels=("known_label", "unknown_label"),
                ),
            },
            labels={
                "known_label": LabelInfo(name="Known Label"),
                # unknown_label not in registry
            },
        )
        data = {"entity_id": "light.test"}
        result = enrich_data(data, context)

        enrichment = result[ENRICHMENT_KEY]
        # Known label is resolved, unknown is kept as ID
        assert "Known Label" in enrichment["labels"]
        assert "unknown_label" in enrichment["labels"]


class TestRegistryContext:
    """Tests for RegistryContext dataclass."""

    def test_empty_factory(self) -> None:
        """RegistryContext.empty() creates empty context."""
        ctx = RegistryContext.empty()
        assert ctx.entities == {}
        assert ctx.devices == {}
        assert ctx.areas == {}
        assert ctx.floors == {}
        assert ctx.labels == {}

    def test_frozen(self) -> None:
        """RegistryContext is immutable."""
        ctx = RegistryContext.empty()
        with pytest.raises(AttributeError):
            ctx.entities = {}  # type: ignore[misc]


class TestInfoDataclasses:
    """Tests for the Info dataclasses."""

    def test_entity_info_defaults(self) -> None:
        """EntityInfo has proper defaults."""
        info = EntityInfo(name=None, device_id=None, area_id=None)
        assert info.labels == ()

    def test_device_info_defaults(self) -> None:
        """DeviceInfo has proper defaults."""
        info = DeviceInfo(name=None, area_id=None)
        assert info.labels == ()

    def test_area_info_defaults(self) -> None:
        """AreaInfo has proper defaults."""
        info = AreaInfo(name="Test")
        assert info.floor_id is None
        assert info.labels == ()
