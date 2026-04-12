"""Pure functions for enriching command output with registry data.

Adds human-readable names from entity, device, area, floor, and label
registries to command output JSON. Enrichment data is namespaced under
a ``hamster_enrichment`` key to clearly distinguish it from original HA data.

This module performs no I/O and holds no global state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EntityInfo:
    """Entity registry information."""

    name: str | None
    device_id: str | None
    area_id: str | None
    labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Device registry information."""

    name: str | None
    area_id: str | None
    labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AreaInfo:
    """Area registry information."""

    name: str
    floor_id: str | None = None
    labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FloorInfo:
    """Floor registry information."""

    name: str


@dataclass(frozen=True, slots=True)
class LabelInfo:
    """Label registry information."""

    name: str


@dataclass(frozen=True, slots=True)
class RegistryContext:
    """Container for all registry data needed for enrichment.

    Constructed by the I/O layer from HA registry data, passed to pure
    enrichment functions.
    """

    entities: dict[str, EntityInfo] = field(default_factory=dict)
    devices: dict[str, DeviceInfo] = field(default_factory=dict)
    areas: dict[str, AreaInfo] = field(default_factory=dict)
    floors: dict[str, FloorInfo] = field(default_factory=dict)
    labels: dict[str, LabelInfo] = field(default_factory=dict)

    @classmethod
    def empty(cls) -> RegistryContext:
        """Create an empty registry context (no enrichment)."""
        return cls()


# Keys that trigger enrichment when found in a dict
_ENTITY_ID_KEY = "entity_id"
_DEVICE_ID_KEY = "device_id"
_AREA_ID_KEY = "area_id"

# Output key for enrichment data
ENRICHMENT_KEY = "hamster_enrichment"


def enrich_data(data: Any, context: RegistryContext) -> Any:
    """Recursively enrich JSON data with registry information.

    Traverses the data structure and adds ``hamster_enrichment`` objects
    to dicts that contain entity_id, device_id, or area_id fields.

    Args:
        data: JSON-compatible data (dict, list, or scalar)
        context: Registry data for lookups

    Returns:
        Enriched data with ``hamster_enrichment`` added where applicable.
        Original data is not mutated; new objects are created.
    """
    if isinstance(data, dict):
        return _enrich_dict(data, context)
    if isinstance(data, list):
        return [enrich_data(item, context) for item in data]
    # Scalars pass through unchanged
    return data


def _enrich_dict(data: dict[str, Any], context: RegistryContext) -> dict[str, Any]:
    """Enrich a dict, recursively processing nested structures.

    Args:
        data: Dict to enrich
        context: Registry data for lookups

    Returns:
        New dict with enrichment added if applicable
    """
    # First, recursively enrich nested values
    result: dict[str, Any] = {}
    for key, value in data.items():
        result[key] = enrich_data(value, context)

    # Build enrichment for this dict
    enrichment = _build_enrichment(data, context)
    if enrichment:
        result[ENRICHMENT_KEY] = enrichment

    return result


def _build_enrichment(
    data: dict[str, Any],
    context: RegistryContext,
) -> dict[str, Any]:
    """Build the hamster_enrichment object for a dict.

    Args:
        data: Original dict (before recursive enrichment)
        context: Registry data for lookups

    Returns:
        Enrichment dict, or empty dict if no enrichment applies
    """
    enrichment: dict[str, Any] = {}

    # Enrich by entity_id
    entity_id = data.get(_ENTITY_ID_KEY)
    if isinstance(entity_id, str):
        _add_entity_enrichment(entity_id, enrichment, context)

    # Enrich by device_id (only if not already enriched via entity)
    device_id = data.get(_DEVICE_ID_KEY)
    if isinstance(device_id, str) and "device_name" not in enrichment:
        _add_device_enrichment(device_id, enrichment, context)

    # Enrich by area_id (only if not already enriched via entity/device)
    area_id = data.get(_AREA_ID_KEY)
    if isinstance(area_id, str) and "area_name" not in enrichment:
        _add_area_enrichment(area_id, enrichment, context)

    return enrichment


def _add_entity_enrichment(
    entity_id: str,
    enrichment: dict[str, Any],
    context: RegistryContext,
) -> None:
    """Add entity-based enrichment fields.

    Adds: name, device_name, area_name, floor_name, labels
    """
    entity = context.entities.get(entity_id)
    if entity is None:
        return

    if entity.name:
        enrichment["name"] = entity.name

    # Resolve device
    if entity.device_id:
        device = context.devices.get(entity.device_id)
        if device:
            if device.name:
                enrichment["device_name"] = device.name
            # Device's area takes precedence if entity has no direct area
            device_area_id = device.area_id
        else:
            device_area_id = None
    else:
        device_area_id = None

    # Resolve area (entity's direct area, or fallback to device's area)
    area_id = entity.area_id or device_area_id
    if area_id:
        _add_area_enrichment(area_id, enrichment, context)

    # Resolve labels (combine entity and device labels)
    all_labels = _resolve_labels(entity.labels, context)
    if entity.device_id:
        device = context.devices.get(entity.device_id)
        if device:
            device_labels = _resolve_labels(device.labels, context)
            # Merge, keeping entity labels first
            all_labels = list(dict.fromkeys(all_labels + device_labels))
    if all_labels:
        enrichment["labels"] = all_labels


def _add_device_enrichment(
    device_id: str,
    enrichment: dict[str, Any],
    context: RegistryContext,
) -> None:
    """Add device-based enrichment fields.

    Adds: device_name, area_name, floor_name, labels
    """
    device = context.devices.get(device_id)
    if device is None:
        return

    if device.name:
        enrichment["device_name"] = device.name

    if device.area_id:
        _add_area_enrichment(device.area_id, enrichment, context)

    labels = _resolve_labels(device.labels, context)
    if labels:
        enrichment["labels"] = labels


def _add_area_enrichment(
    area_id: str,
    enrichment: dict[str, Any],
    context: RegistryContext,
) -> None:
    """Add area-based enrichment fields.

    Adds: area_name, floor_name
    """
    area = context.areas.get(area_id)
    if area is None:
        return

    enrichment["area_name"] = area.name

    if area.floor_id:
        floor = context.floors.get(area.floor_id)
        if floor:
            enrichment["floor_name"] = floor.name


def _resolve_labels(
    label_ids: tuple[str, ...],
    context: RegistryContext,
) -> list[str]:
    """Resolve label IDs to human-readable names.

    Args:
        label_ids: Tuple of label IDs
        context: Registry data for lookups

    Returns:
        List of resolved label names (unresolved IDs are included as-is)
    """
    result: list[str] = []
    for label_id in label_ids:
        label = context.labels.get(label_id)
        result.append(label.name if label else label_id)
    return result
