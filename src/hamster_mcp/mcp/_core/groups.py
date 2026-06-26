"""Source group protocol and registry for multi-source architecture.

Provides the SourceGroup protocol and GroupRegistry for managing multiple
command sources (services, hass, supervisor).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
import json
from typing import TYPE_CHECKING, Any, Protocol, cast, runtime_checkable

from .events import Done, FormatServiceResponse, ServiceCall, ToolEffect
from .selector_schemas import (
    SELECTOR_TYPES,
    get_configured_selector_schema,
    get_selector_list_schema,
    get_selector_schema,
    get_target_schema,
)
from .types import CallToolResult, TextContent

if TYPE_CHECKING:
    from collections.abc import Mapping


@runtime_checkable
class SourceGroup(Protocol):
    """Protocol for command source groups.

    Each group exposes commands from a different source (services, hass,
    supervisor) with group-specific discovery and metadata.

    Not a dataclass: This is a Protocol — a structural typing construct that
    defines the contract source groups must implement. Protocols specify method
    signatures and properties for static type checking; they are not instantiated
    directly and serve purely as interface definitions.
    """

    @property
    def name(self) -> str:
        """Group name (e.g., 'services', 'hass', 'supervisor')."""
        ...

    @property
    def available(self) -> bool:
        """Whether this group is available. Default True for most groups."""
        ...

    def search(self, query: str, *, path_filter: str | None = None) -> str:
        """Search for commands matching query, optionally filtered by path prefix.

        Returns a formatted markdown string with search results.
        """
        ...

    def explain(self, path: str) -> str | None:
        """Get description for a command.

        Returns None if not found or unavailable.
        """
        ...

    def schema(self, path: str) -> str | None:
        """Get schema/type info for a command.

        Returns None if not found.
        """
        ...

    def has_command(self, path: str) -> bool:
        """Check if a command exists."""
        ...

    def parse_call_args(
        self, path: str, arguments: dict[str, object], user_id: str | None
    ) -> ToolEffect:
        """Parse and validate call arguments, return effect or error."""
        ...


@dataclass(frozen=False, slots=True)
class GroupRegistry:
    """Registry for source groups.

    Manages registration and lookup of groups, and provides aggregate
    operations across all groups.
    """

    _groups: dict[str, SourceGroup] = field(init=False, default_factory=dict)

    def register(self, group: SourceGroup) -> None:
        """Register a group.

        Raises ValueError if a group with the same name is already registered.
        """
        if group.name in self._groups:
            raise ValueError(f"Group already registered: {group.name}")
        self._groups[group.name] = group

    def update_group(self, group: SourceGroup) -> None:
        """Replace an existing group by name.

        Raises ValueError if the group is not found.
        """
        if group.name not in self._groups:
            raise ValueError(f"Group not found: {group.name}")
        self._groups[group.name] = group

    def get(self, name: str) -> SourceGroup | None:
        """Get a group by name, or None if not found."""
        return self._groups.get(name)

    def all_groups(self) -> list[SourceGroup]:
        """Return all registered groups."""
        return list(self._groups.values())

    def search_all(self, query: str, *, path_filter: str | None = None) -> str:
        """Aggregate search across all groups.

        If path_filter targets a specific group (e.g., "services" or
        "services/light"), only that group is searched.
        """
        # Parse path_filter to determine which groups to search
        target_group: str | None = None
        sub_filter: str | None = None

        if path_filter:
            if "/" in path_filter:
                target_group, sub_filter = path_filter.split("/", 1)
            else:
                target_group = path_filter
                sub_filter = None

        # Collect results from each group
        results: list[str] = []

        for group in self._groups.values():
            # Skip unavailable groups
            if not group.available:
                continue

            # Skip if we're filtering to a specific group
            if target_group and group.name != target_group:
                continue

            # Search the group
            group_result = group.search(query, path_filter=sub_filter)

            # Skip empty results (check for "No " at start which indicates no matches)
            if group_result.startswith("No "):
                continue

            results.append(f"## {group.name}\n\n{group_result}")

        if not results:
            if target_group:
                return (
                    f'No commands found matching "{query}" in group "{target_group}".'
                )
            return f'No commands found matching "{query}".'

        return "\n\n".join(results)

    def resolve_path(self, full_path: str) -> tuple[SourceGroup, str] | None:
        """Parse 'group/path' and return (group, in-group-path).

        Returns None if the path is invalid or the group is not found.
        """
        if not full_path:
            return None

        if "/" not in full_path:
            return None

        group_name, in_group_path = full_path.split("/", 1)

        group = self._groups.get(group_name)
        if group is None:
            return None

        return (group, in_group_path)


# --- Helper functions ---


def _make_error(message: str) -> Done:
    """Create a Done result with an error."""
    return Done(
        result=CallToolResult(
            content=(TextContent(text=message),),
            is_error=True,
        )
    )


# --- ServicesGroup ---


@dataclass(frozen=True, slots=True)
class ServicesGroup:
    """Source group for Home Assistant services.

    Wraps the service descriptions from async_get_all_descriptions() and
    provides search, explain, schema, and call functionality.

    Use `.create()` classmethod to construct from raw HA service descriptions.
    """

    _descriptions: Mapping[str, Any]
    _entries: tuple[tuple[str, str, str, dict[str, object]], ...]

    @classmethod
    def create(cls, descriptions: Mapping[str, Any]) -> ServicesGroup:
        """Build index from HA service descriptions.

        Args:
            descriptions: Dict keyed by domain, then service name.
                Each service value contains 'name', 'description', 'fields', etc.

        Returns:
            ServicesGroup with pre-computed search index.
        """
        entries: list[tuple[str, str, str, dict[str, object]]] = []

        for domain, services in descriptions.items():
            if not isinstance(services, dict):
                continue
            for service_name, service_data in services.items():
                if not isinstance(service_data, dict):
                    continue
                # Build search text from domain, service name, description, field names
                search_parts = [domain, service_name]
                desc = service_data.get("description")
                if isinstance(desc, str):
                    search_parts.append(desc)
                fields = service_data.get("fields")
                if isinstance(fields, dict):
                    search_parts.extend(fields.keys())
                search_text = " ".join(search_parts).lower()
                entries.append((domain, service_name, search_text, service_data))

        return cls(_descriptions=descriptions, _entries=tuple(entries))

    @property
    def name(self) -> str:
        """Group name."""
        return "services"

    @property
    def available(self) -> bool:
        """Services are always available."""
        return True

    def search(self, query: str, *, path_filter: str | None = None) -> str:
        """Search for services matching a keyword.

        Args:
            query: Search keyword (case-insensitive substring match)
            path_filter: Optional domain filter

        Returns:
            Formatted text summary of matching services.
        """
        query_lower = query.lower()
        matches: list[tuple[str, str, dict[str, object]]] = []

        for entry_domain, service_name, search_text, service_data in self._entries:
            if path_filter is not None and entry_domain != path_filter:
                continue
            if query_lower in search_text:
                matches.append((entry_domain, service_name, service_data))

        if not matches:
            if path_filter:
                return (
                    f'No services found in domain "{path_filter}" matching "{query}".'
                )
            return f'No services found matching "{query}".'

        # Format results
        if path_filter:
            header = (
                f'Found {len(matches)} services in domain "{path_filter}" '
                f'matching "{query}":'
            )
        else:
            header = f'Found {len(matches)} services matching "{query}":'

        lines = [header, ""]
        for i, (d, s, data) in enumerate(matches, 1):
            desc = data.get("description", "")
            if isinstance(desc, str) and desc:
                lines.append(f"{i}. **{d}.{s}** - {desc}")
            else:
                lines.append(f"{i}. **{d}.{s}**")

        return "\n".join(lines)

    def explain(self, path: str) -> str | None:
        """Get detailed description of a single service.

        Args:
            path: Service path in "domain.service" format

        Returns:
            Formatted text with full service details, or None if not found.
            Includes references to relevant JSON Schemas for type exploration.
        """
        if "." not in path:
            return None

        domain, service = path.split(".", 1)

        domain_services = self._descriptions.get(domain)
        if not isinstance(domain_services, dict):
            return None

        service_data = domain_services.get(service)
        if not isinstance(service_data, dict):
            return None

        lines = [f"## {domain}.{service}"]

        # Description
        desc = service_data.get("description")
        if isinstance(desc, str):
            lines.append("")
            lines.append(desc)

        # Target config
        target = service_data.get("target")
        has_target = "target" in service_data
        if has_target:
            lines.append("")
            lines.append("### Target")
            lines.append('*(use `schema("selector/target")` for full JSON Schema)*')
            if isinstance(target, dict) and target:
                if entity := target.get("entity"):
                    lines.append(f"- Entity: {entity}")
                if device := target.get("device"):
                    lines.append(f"- Device: {device}")
                if area := target.get("area"):
                    lines.append(f"- Area: {area}")
            else:
                lines.append("Accepts target specification")

        # Fields
        fields = service_data.get("fields")
        selector_types_used: set[str] = set()
        if isinstance(fields, dict) and fields:
            lines.append("")
            lines.append("### Fields")
            self._format_fields(fields, lines, selector_types_used=selector_types_used)

        # Schema references section
        if selector_types_used or has_target:
            lines.append("")
            lines.append("### Schema References")
            lines.append(
                f'Use `schema("{domain}.{service}")` '
                "for full JSON Schema of parameters."
            )
            if selector_types_used:
                sorted_types = sorted(selector_types_used)
                refs = ", ".join(f'`schema("selector/{t}")`' for t in sorted_types)
                lines.append(f"Selector types used: {refs}")

        return "\n".join(lines)

    def _format_fields(
        self,
        fields: dict[str, object],
        lines: list[str],
        indent: str = "",
        *,
        selector_types_used: set[str] | None = None,
    ) -> None:
        """Format field definitions recursively.

        Args:
            fields: Field definitions dict
            lines: Output lines to append to
            indent: Current indentation string
            selector_types_used: Set to collect selector types encountered
        """
        for field_name, field_data in fields.items():
            if not isinstance(field_data, dict):
                continue

            # Check if this is a section (has 'fields' key)
            if "fields" in field_data:
                section_name = field_data.get("name", field_name)
                lines.append(f"{indent}- **{section_name}** (section)")
                nested_fields = field_data.get("fields")
                if isinstance(nested_fields, dict):
                    self._format_fields(
                        nested_fields,
                        lines,
                        indent + "  ",
                        selector_types_used=selector_types_used,
                    )
                continue

            # Regular field
            field_desc = field_data.get("description", "")
            required = field_data.get("required", False)
            selector = field_data.get("selector", {})

            req_marker = " (required)" if required else ""
            selector_info = ""
            if isinstance(selector, dict) and selector:
                selector_types = list(selector.keys())
                if selector_types:
                    selector_type = selector_types[0]
                    selector_info = f" [{selector_type}]"
                    if selector_types_used is not None:
                        selector_types_used.add(selector_type)

            base = f"{indent}- **{field_name}**{req_marker}{selector_info}"
            if isinstance(field_desc, str) and field_desc:
                lines.append(f"{base}: {field_desc}")
            else:
                lines.append(base)

    def schema(self, path: str) -> str | None:
        """Get schema/type info for a service or selector.

        Returns a hybrid JSON Schema + Markdown response:
        - JSON Schema in a code block for machine parsing
        - Markdown description for human readability

        Path formats:
        - "selector" - List all selector types (x-selector-types annotation)
        - "selector/<type>" - Get JSON Schema for a specific selector
        - "domain.service" - Get JSON Schema for service parameters
        """
        # Handle selector paths
        if path == "selector":
            return self._format_selector_list_schema()
        if path.startswith("selector/"):
            selector_type = path[9:]  # Remove "selector/" prefix
            return self._format_selector_schema(selector_type)

        # Service field schema
        if "." not in path:
            return None

        domain, service = path.split(".", 1)
        domain_services = self._descriptions.get(domain)
        if not isinstance(domain_services, dict):
            return None

        service_data = domain_services.get(service)
        if not isinstance(service_data, dict):
            return None

        return self._format_service_schema(domain, service, service_data)

    def _format_selector_list_schema(self) -> str:
        """Format the selector type list with x-selector-types annotation."""
        schema = get_selector_list_schema()
        json_block = json.dumps(schema, indent=2)

        types_per_line = 8
        type_lines = []
        for i in range(0, len(SELECTOR_TYPES), types_per_line):
            chunk = SELECTOR_TYPES[i : i + types_per_line]
            type_lines.append(", ".join(chunk))

        newline = "\n"
        markdown = f"""## Available Selector Types

{len(SELECTOR_TYPES)} selector types available:

{newline.join(f"- {line}" for line in type_lines)}

Use `schema("selector/<type>")` to get the JSON Schema for a specific type."""

        return f"```json\n{json_block}\n```\n\n{markdown}"

    def _format_selector_schema(self, selector_type: str) -> str:
        """Format a single selector type's JSON Schema."""
        schema = get_selector_schema(selector_type)

        if schema is None:
            return (
                f"Unknown selector type: {selector_type}\n\n"
                f'Use `schema("selector")` to see all {len(SELECTOR_TYPES)} '
                "available selector types."
            )

        json_block = json.dumps(schema, indent=2)
        description = schema.get("description", "")

        # Build markdown explanation
        markdown_parts = [f"## {selector_type} selector", ""]
        if description:
            markdown_parts.append(description)
            markdown_parts.append("")

        # Add type-specific notes
        schema_type = schema.get("type", "any")
        if schema_type == "object" and "properties" in schema:
            props = schema["properties"]
            required = schema.get("required", [])
            markdown_parts.append("**Properties:**")
            for prop_name, prop_schema in props.items():
                req_marker = " (required)" if prop_name in required else ""
                prop_desc = prop_schema.get("description", "")
                if isinstance(prop_schema, dict) and "oneOf" in prop_schema:
                    prop_desc = prop_schema.get("description", "string or array")
                markdown_parts.append(f"- `{prop_name}`{req_marker}: {prop_desc}")
            markdown_parts.append("")

        # Add x-target-keys note for target selector
        if "x-target-keys" in schema:
            target_keys = schema["x-target-keys"]
            markdown_parts.append(
                f"**Target keys:** {', '.join(f'`{k}`' for k in target_keys)}"
            )
            markdown_parts.append("")

        # Add examples if present
        if "examples" in schema:
            examples = schema["examples"]
            markdown_parts.append("**Examples:**")
            for ex in examples:
                if isinstance(ex, str):
                    markdown_parts.append(f"- `{ex}`")
                else:
                    markdown_parts.append(f"- `{json.dumps(ex)}`")

        return f"```json\n{json_block}\n```\n\n" + "\n".join(markdown_parts)

    def _format_service_schema(
        self, domain: str, service: str, service_data: dict[str, object]
    ) -> str:
        """Format service call arguments as JSON Schema."""
        raw_fields = service_data.get("fields")
        fields = cast(
            "dict[str, object] | None",
            raw_fields if isinstance(raw_fields, dict) and raw_fields else None,
        )
        has_target = "target" in service_data

        if fields is None and not has_target:
            return f"Service {domain}.{service} has no parameters."

        properties: dict[str, Any] = {}
        required_args: list[str] = []

        if has_target:
            target_schema = get_target_schema()
            target_schema["description"] = "Service target. Pass as `arguments.target`."
            target_config = service_data.get("target")
            if isinstance(target_config, dict) and target_config:
                target_schema["x-ha-target-config"] = copy.deepcopy(target_config)
            properties["target"] = target_schema

        if fields is not None:
            data_schema, required_fields = self._build_service_data_schema(
                domain, service, fields
            )
            properties["data"] = data_schema
            if required_fields:
                required_args.append("data")

        schema: dict[str, Any] = {
            "type": "object",
            "description": (
                f"Arguments for `call` with path `services/{domain}.{service}`. "
                "Use `target` for what to act on and `data` for service fields."
            ),
            "properties": properties,
        }
        if required_args:
            schema["required"] = required_args

        json_block = json.dumps(schema, indent=2)

        # Build markdown summary
        markdown_parts = [
            f"## {domain}.{service} Call Arguments",
            "",
            (
                "Pass this object as the `arguments` value when calling "
                f"`services/{domain}.{service}`."
            ),
            "",
        ]

        if has_target:
            markdown_parts.extend(
                [
                    "### `arguments.target`",
                    "",
                    (
                        "Service accepts a target object for entities, devices, "
                        "areas, floors, or labels."
                    ),
                    "",
                ]
            )

        if fields is not None:
            markdown_parts.extend(
                [
                    "### `arguments.data`",
                    "",
                    "Service data fields:",
                ]
            )
            self._format_service_schema_fields(fields, markdown_parts)

        return f"```json\n{json_block}\n```\n\n" + "\n".join(markdown_parts)

    def _build_service_data_schema(
        self, domain: str, service: str, fields: dict[str, object]
    ) -> tuple[dict[str, Any], list[str]]:
        """Build the ``arguments.data`` schema for service fields."""
        properties: dict[str, Any] = {}
        required_fields: list[str] = []
        self._collect_service_field_schemas(fields, properties, required_fields)

        schema: dict[str, Any] = {
            "type": "object",
            "description": (
                f"Service data for `{domain}.{service}`. Pass as `arguments.data`."
            ),
            "properties": properties,
        }
        if required_fields:
            schema["required"] = required_fields
        return schema, required_fields

    def _collect_service_field_schemas(
        self,
        fields: dict[str, object],
        properties: dict[str, Any],
        required_fields: list[str],
        section: str | None = None,
    ) -> None:
        """Collect service field schemas, flattening HA presentation sections."""
        for field_name, field_data in fields.items():
            if not isinstance(field_data, dict):
                continue

            if "fields" in field_data:
                nested_fields = field_data.get("fields")
                section_name = field_data.get("name", field_name)
                if isinstance(nested_fields, dict):
                    self._collect_service_field_schemas(
                        cast("dict[str, object]", nested_fields),
                        properties,
                        required_fields,
                        section_name if isinstance(section_name, str) else field_name,
                    )
                continue

            field_schema = self._build_service_field_schema(field_data)
            if section is not None:
                field_schema["x-ha-section"] = section
            properties[field_name] = field_schema

            if field_data.get("required", False):
                required_fields.append(field_name)

    def _build_service_field_schema(
        self, field_data: dict[object, object]
    ) -> dict[str, Any]:
        """Build a JSON Schema fragment for one HA service field."""
        selector_type, selector_config = self._selector_type_and_config(
            field_data.get("selector", {})
        )

        field_schema: dict[str, Any] = {}
        if selector_type is not None:
            selector_schema = get_configured_selector_schema(
                selector_type, selector_config
            )
            if selector_schema is None:
                field_schema["x-selector-type"] = selector_type
            else:
                field_schema = selector_schema

        desc = field_data.get("description", "")
        if isinstance(desc, str) and desc:
            field_schema["description"] = desc

        name = field_data.get("name")
        if isinstance(name, str) and name:
            field_schema["title"] = name

        if "example" in field_data:
            field_schema["examples"] = [copy.deepcopy(field_data["example"])]
        if "default" in field_data:
            field_schema["default"] = copy.deepcopy(field_data["default"])
        if filter_config := field_data.get("filter"):
            field_schema["x-ha-filter"] = copy.deepcopy(filter_config)

        return field_schema

    @staticmethod
    def _selector_type_and_config(selector: object) -> tuple[str | None, object]:
        """Return HA selector discriminator and config from a selector object."""
        if not isinstance(selector, dict) or not selector:
            return None, {}

        selector_type = next(iter(selector))
        if not isinstance(selector_type, str):
            return None, {}
        return selector_type, selector.get(selector_type, {})

    def _format_service_schema_fields(
        self, fields: dict[str, object], markdown_parts: list[str], indent: str = ""
    ) -> None:
        """Format service fields for the service schema markdown section."""
        for field_name, field_data in fields.items():
            if not isinstance(field_data, dict):
                continue

            if "fields" in field_data:
                section_name = field_data.get("name", field_name)
                markdown_parts.append(
                    f"{indent}- **{section_name}** "
                    "(section; fields flatten into `arguments.data`)"
                )
                nested_fields = field_data.get("fields")
                if isinstance(nested_fields, dict):
                    self._format_service_schema_fields(
                        cast("dict[str, object]", nested_fields),
                        markdown_parts,
                        indent + "  ",
                    )
                continue

            is_required = field_data.get("required", False)
            selector_type, _selector_config = self._selector_type_and_config(
                field_data.get("selector", {})
            )
            desc = field_data.get("description", "")

            selector_info = f" [{selector_type}]" if selector_type is not None else ""
            req_str = " (required)" if is_required else ""
            line = f"{indent}- **{field_name}**{req_str}{selector_info}"
            if isinstance(desc, str) and desc:
                line += f": {desc}"
            markdown_parts.append(line)

    def has_command(self, path: str) -> bool:
        """Check if a service exists."""
        if "." not in path:
            return False

        domain, service = path.split(".", 1)
        domain_services = self._descriptions.get(domain)
        if not isinstance(domain_services, dict):
            return False
        return service in domain_services

    def _supports_response(self, domain: str, service: str) -> bool:
        """Check if a service supports response data.

        Args:
            domain: Service domain (e.g. 'light')
            service: Service name (e.g. 'turn_on')

        Returns:
            True if the service supports returning response data, False otherwise.
            Services with a "response" key in their description support responses.
        """
        domain_services = self._descriptions.get(domain)
        if not isinstance(domain_services, dict):
            return False
        service_data = domain_services.get(service)
        if not isinstance(service_data, dict):
            return False
        # HA adds "response" key only when SupportsResponse is not NONE
        return "response" in service_data

    def parse_call_args(
        self, path: str, arguments: dict[str, object], user_id: str | None
    ) -> ToolEffect:
        """Parse and validate call arguments for a service.

        Args:
            path: Service path in "domain.service" format
            arguments: Tool arguments with optional "target" and "data" keys
            user_id: Authenticated user ID for authorization

        Returns:
            ServiceCall effect on success, Done with error otherwise.
        """
        if "." not in path:
            return _make_error(f"Invalid service path: {path}")

        domain, service = path.split(".", 1)

        # Validate service exists
        if not self.has_command(path):
            return _make_error(f"Service not found: {domain}.{service}")

        # Validate target
        target = arguments.get("target")
        if target is not None and not isinstance(target, dict):
            return _make_error("Invalid 'target' parameter (must be an object)")

        # Validate data
        data = arguments.get("data")
        if data is None:
            data = {}
        if not isinstance(data, dict):
            return _make_error("Invalid 'data' parameter (must be an object)")

        return ServiceCall(
            domain=domain,
            service=service,
            target=target,
            data=data,
            user_id=user_id,
            continuation=FormatServiceResponse(),
            supports_response=self._supports_response(domain, service),
        )
