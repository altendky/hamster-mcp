"""SupervisorGroup: Supervisor API endpoint definitions and invocation.

Provides static endpoint definitions for Supervisor API and implements
the SourceGroup protocol for search, explain, schema, and command invocation.

Unlike the hass group (discovered at runtime), Supervisor endpoints are
defined statically.
"""

from __future__ import annotations

from dataclasses import dataclass

from .events import Done, FormatSupervisorResponse, SupervisorCall, ToolEffect
from .types import CallToolResult, TextContent

# --- Types ---


@dataclass(frozen=True, slots=True)
class EndpointInfo:
    """Metadata for a Supervisor API endpoint.

    Attributes:
        method: HTTP method (GET, POST, etc.)
        path: API path (e.g., "/core/logs", "/addons/{slug}/logs")
        description: Human-readable description
        params_schema: Parameter definitions (JSON-schema-like)
        path_params: Template parameters in the path, e.g., ("slug",)
        returns_text: True for log endpoints that return plain text
    """

    method: str
    path: str
    description: str
    params_schema: dict[str, object]
    path_params: tuple[str, ...] = ()
    returns_text: bool = False


# --- Endpoint definitions ---


# Note on terminology: Home Assistant rebranded "add-ons" to "apps" in 2026.6
# user-facing surfaces, but the Supervisor REST paths still use `/addons`.
# Descriptions use "app (add-on)" so search hits work for either term while
# keeping the legacy name visible to operators familiar with it.
_APP_SLUG = {"type": "string", "description": "App (add-on) slug"}
_BOOT_ID = {"type": "string", "description": "Boot identifier"}
_UUID = {"type": "string", "description": "Discovery service UUID"}
_BACKUP_SLUG = {"type": "string", "description": "Backup slug"}
_INTERFACE = {"type": "string", "description": "Network interface name"}
_JOB_UUID = {"type": "string", "description": "Job UUID"}


SUPERVISOR_ENDPOINTS: dict[str, EndpointInfo] = {
    # --- Apps (formerly add-ons) ---
    "addons": EndpointInfo(
        method="GET",
        path="/addons",
        description="List installed apps (add-ons)",
        params_schema={},
    ),
    "addons/{slug}/info": EndpointInfo(
        method="GET",
        path="/addons/{slug}/info",
        description="Get app (add-on) information",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
    ),
    "addons/{slug}/stats": EndpointInfo(
        method="GET",
        path="/addons/{slug}/stats",
        description="Get app (add-on) resource usage statistics",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
    ),
    "addons/{slug}/changelog": EndpointInfo(
        method="GET",
        path="/addons/{slug}/changelog",
        description="Get app (add-on) changelog",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
        returns_text=True,
    ),
    "addons/{slug}/documentation": EndpointInfo(
        method="GET",
        path="/addons/{slug}/documentation",
        description="Get app (add-on) documentation",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
        returns_text=True,
    ),
    "addons/{slug}/logs": EndpointInfo(
        method="GET",
        path="/addons/{slug}/logs",
        description="Get app (add-on) logs from the Systemd journal",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
        returns_text=True,
    ),
    "addons/{slug}/logs/follow": EndpointInfo(
        method="GET",
        path="/addons/{slug}/logs/follow",
        description="Stream app (add-on) logs (continuous follow)",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
        returns_text=True,
    ),
    "addons/{slug}/logs/latest": EndpointInfo(
        method="GET",
        path="/addons/{slug}/logs/latest",
        description="Get logs from the latest startup of the app (add-on) container",
        params_schema={"slug": _APP_SLUG},
        path_params=("slug",),
        returns_text=True,
    ),
    "addons/{slug}/logs/boots/{bootid}": EndpointInfo(
        method="GET",
        path="/addons/{slug}/logs/boots/{bootid}",
        description="Get app (add-on) logs for a specific boot",
        params_schema={"slug": _APP_SLUG, "bootid": _BOOT_ID},
        path_params=("slug", "bootid"),
        returns_text=True,
    ),
    # --- Audio plugin ---
    "audio/info": EndpointInfo(
        method="GET",
        path="/audio/info",
        description="Get audio plugin information",
        params_schema={},
    ),
    "audio/stats": EndpointInfo(
        method="GET",
        path="/audio/stats",
        description="Get audio plugin resource usage statistics",
        params_schema={},
    ),
    "audio/logs": EndpointInfo(
        method="GET",
        path="/audio/logs",
        description="Get audio plugin logs from the Systemd journal",
        params_schema={},
        returns_text=True,
    ),
    "audio/logs/follow": EndpointInfo(
        method="GET",
        path="/audio/logs/follow",
        description="Stream audio plugin logs (continuous follow)",
        params_schema={},
        returns_text=True,
    ),
    "audio/logs/latest": EndpointInfo(
        method="GET",
        path="/audio/logs/latest",
        description="Get logs from the latest startup of the audio plugin container",
        params_schema={},
        returns_text=True,
    ),
    # --- Backups ---
    "backups": EndpointInfo(
        method="GET",
        path="/backups",
        description="List backups",
        params_schema={},
    ),
    "backups/info": EndpointInfo(
        method="GET",
        path="/backups/info",
        description="Get backup manager information",
        params_schema={},
    ),
    "backups/{slug}/info": EndpointInfo(
        method="GET",
        path="/backups/{slug}/info",
        description="Get details for a specific backup",
        params_schema={"slug": _BACKUP_SLUG},
        path_params=("slug",),
    ),
    # --- CLI plugin ---
    "cli/info": EndpointInfo(
        method="GET",
        path="/cli/info",
        description="Get CLI plugin information",
        params_schema={},
    ),
    "cli/stats": EndpointInfo(
        method="GET",
        path="/cli/stats",
        description="Get CLI plugin resource usage statistics",
        params_schema={},
    ),
    # --- Home Assistant Core ---
    "core/info": EndpointInfo(
        method="GET",
        path="/core/info",
        description="Get Home Assistant Core information",
        params_schema={},
    ),
    "core/stats": EndpointInfo(
        method="GET",
        path="/core/stats",
        description="Get Home Assistant Core resource usage statistics",
        params_schema={},
    ),
    "core/logs": EndpointInfo(
        method="GET",
        path="/core/logs",
        description="Get Home Assistant Core logs from the Systemd journal",
        params_schema={},
        returns_text=True,
    ),
    "core/logs/follow": EndpointInfo(
        method="GET",
        path="/core/logs/follow",
        description="Stream Home Assistant Core logs (continuous follow)",
        params_schema={},
        returns_text=True,
    ),
    "core/logs/latest": EndpointInfo(
        method="GET",
        path="/core/logs/latest",
        description=(
            "Get logs from the latest startup of the Home Assistant Core container"
        ),
        params_schema={},
        returns_text=True,
    ),
    "core/logs/boots/{bootid}": EndpointInfo(
        method="GET",
        path="/core/logs/boots/{bootid}",
        description="Get Home Assistant Core logs for a specific boot",
        params_schema={"bootid": _BOOT_ID},
        path_params=("bootid",),
        returns_text=True,
    ),
    # --- Discovery ---
    "discovery": EndpointInfo(
        method="GET",
        path="/discovery",
        description="List enabled discovery services from apps (add-ons)",
        params_schema={},
    ),
    "discovery/{uuid}": EndpointInfo(
        method="GET",
        path="/discovery/{uuid}",
        description="Get a specific discovery service by UUID",
        params_schema={"uuid": _UUID},
        path_params=("uuid",),
    ),
    # --- DNS plugin ---
    "dns/info": EndpointInfo(
        method="GET",
        path="/dns/info",
        description="Get DNS plugin information",
        params_schema={},
    ),
    "dns/stats": EndpointInfo(
        method="GET",
        path="/dns/stats",
        description="Get DNS plugin resource usage statistics",
        params_schema={},
    ),
    "dns/logs": EndpointInfo(
        method="GET",
        path="/dns/logs",
        description="Get DNS plugin logs from the Systemd journal",
        params_schema={},
        returns_text=True,
    ),
    "dns/logs/latest": EndpointInfo(
        method="GET",
        path="/dns/logs/latest",
        description="Get logs from the latest startup of the DNS plugin container",
        params_schema={},
        returns_text=True,
    ),
    # --- Hardware ---
    "hardware/info": EndpointInfo(
        method="GET",
        path="/hardware/info",
        description="Get hardware information",
        params_schema={},
    ),
    "hardware/audio": EndpointInfo(
        method="GET",
        path="/hardware/audio",
        description="Get audio hardware information",
        params_schema={},
    ),
    # --- Host ---
    "host/info": EndpointInfo(
        method="GET",
        path="/host/info",
        description="Get host system information",
        params_schema={},
    ),
    "host/logs": EndpointInfo(
        method="GET",
        path="/host/logs",
        description="Get host system logs from the Systemd journal",
        params_schema={},
        returns_text=True,
    ),
    "host/logs/follow": EndpointInfo(
        method="GET",
        path="/host/logs/follow",
        description="Stream host system logs (continuous follow)",
        params_schema={},
        returns_text=True,
    ),
    "host/logs/latest": EndpointInfo(
        method="GET",
        path="/host/logs/latest",
        description="Get logs from the latest boot of the host system",
        params_schema={},
        returns_text=True,
    ),
    "host/logs/identifiers": EndpointInfo(
        method="GET",
        path="/host/logs/identifiers",
        description="List Systemd journal identifiers available on the host",
        params_schema={},
    ),
    "host/logs/boots": EndpointInfo(
        method="GET",
        path="/host/logs/boots",
        description="List boot IDs known to the host journal",
        params_schema={},
    ),
    # --- Jobs ---
    "jobs/info": EndpointInfo(
        method="GET",
        path="/jobs/info",
        description="Get information about Supervisor jobs",
        params_schema={},
    ),
    "jobs/{uuid}": EndpointInfo(
        method="GET",
        path="/jobs/{uuid}",
        description="Get information about a specific Supervisor job",
        params_schema={"uuid": _JOB_UUID},
        path_params=("uuid",),
    ),
    # --- Mounts ---
    "mounts": EndpointInfo(
        method="GET",
        path="/mounts",
        description="List configured network mounts",
        params_schema={},
    ),
    # --- Multicast plugin ---
    "multicast/info": EndpointInfo(
        method="GET",
        path="/multicast/info",
        description="Get multicast plugin information",
        params_schema={},
    ),
    "multicast/stats": EndpointInfo(
        method="GET",
        path="/multicast/stats",
        description="Get multicast plugin resource usage statistics",
        params_schema={},
    ),
    "multicast/logs": EndpointInfo(
        method="GET",
        path="/multicast/logs",
        description="Get multicast plugin logs from the Systemd journal",
        params_schema={},
        returns_text=True,
    ),
    # --- Network ---
    "network/info": EndpointInfo(
        method="GET",
        path="/network/info",
        description="Get network information",
        params_schema={},
    ),
    "network/interface/{interface}/info": EndpointInfo(
        method="GET",
        path="/network/interface/{interface}/info",
        description="Get information about a specific network interface",
        params_schema={"interface": _INTERFACE},
        path_params=("interface",),
    ),
    # --- Observer plugin ---
    "observer/info": EndpointInfo(
        method="GET",
        path="/observer/info",
        description="Get observer plugin information",
        params_schema={},
    ),
    "observer/stats": EndpointInfo(
        method="GET",
        path="/observer/stats",
        description="Get observer plugin resource usage statistics",
        params_schema={},
    ),
    # --- Operating system ---
    "os/info": EndpointInfo(
        method="GET",
        path="/os/info",
        description="Get Home Assistant OS information",
        params_schema={},
    ),
    # --- Resolution center ---
    "resolution/info": EndpointInfo(
        method="GET",
        path="/resolution/info",
        description="Get resolution center information (issues, suggestions, checks)",
        params_schema={},
    ),
    # --- Services discovery ---
    "services": EndpointInfo(
        method="GET",
        path="/services",
        description="List services provided by apps (add-ons)",
        params_schema={},
    ),
    # --- Store ---
    "store": EndpointInfo(
        method="GET",
        path="/store",
        description="Get app (add-on) store overview",
        params_schema={},
    ),
    "store/addons": EndpointInfo(
        method="GET",
        path="/store/addons",
        description="List apps (add-ons) available in the store",
        params_schema={},
    ),
    "store/repositories": EndpointInfo(
        method="GET",
        path="/store/repositories",
        description="List app (add-on) repositories configured in the store",
        params_schema={},
    ),
    # --- Supervisor ---
    "supervisor/info": EndpointInfo(
        method="GET",
        path="/supervisor/info",
        description="Get Supervisor information",
        params_schema={},
    ),
    "supervisor/stats": EndpointInfo(
        method="GET",
        path="/supervisor/stats",
        description="Get Supervisor resource usage statistics",
        params_schema={},
    ),
    "supervisor/logs": EndpointInfo(
        method="GET",
        path="/supervisor/logs",
        description="Get Supervisor logs from the Systemd journal",
        params_schema={},
        returns_text=True,
    ),
    "supervisor/logs/follow": EndpointInfo(
        method="GET",
        path="/supervisor/logs/follow",
        description="Stream Supervisor logs (continuous follow)",
        params_schema={},
        returns_text=True,
    ),
    "supervisor/logs/latest": EndpointInfo(
        method="GET",
        path="/supervisor/logs/latest",
        description="Get logs from the latest startup of the Supervisor container",
        params_schema={},
        returns_text=True,
    ),
}


# --- Helper functions ---


def _make_error(message: str) -> Done:
    """Create a Done result with an error."""
    return Done(
        result=CallToolResult(
            content=(TextContent(text=message),),
            is_error=True,
        )
    )


# --- SupervisorGroup ---


@dataclass(frozen=True, slots=True)
class SupervisorGroup:
    """Source group for Supervisor API endpoints.

    Provides search, explain, schema, and call functionality for
    Supervisor API endpoints. Uses static endpoint definitions.

    Use `.create()` classmethod to construct with pre-computed search index.
    """

    _available: bool
    _entries: tuple[tuple[str, str, EndpointInfo], ...]

    @classmethod
    def create(cls, available: bool) -> SupervisorGroup:
        """Build with availability status.

        Args:
            available: Whether Supervisor is available on this installation

        Returns:
            SupervisorGroup with pre-computed search index.
        """
        entries: list[tuple[str, str, EndpointInfo]] = []
        for endpoint_path, info in SUPERVISOR_ENDPOINTS.items():
            # Build search text from endpoint path and description
            search_text = f"{endpoint_path} {info.description}".lower()
            entries.append((endpoint_path, search_text, info))

        return cls(_available=available, _entries=tuple(entries))

    @property
    def name(self) -> str:
        """Group name."""
        return "supervisor"

    @property
    def available(self) -> bool:
        """Whether Supervisor is available."""
        return self._available

    def search(self, query: str, *, path_filter: str | None = None) -> str:
        """Search for endpoints matching a keyword.

        Args:
            query: Search keyword (case-insensitive substring match)
            path_filter: Optional prefix filter (e.g., "core" for "core/*")

        Returns:
            Formatted text summary of matching endpoints.
        """
        if not self._available:
            return "Supervisor is not available on this installation."

        query_lower = query.lower()
        matches: list[tuple[str, EndpointInfo]] = []

        for endpoint_path, search_text, info in self._entries:
            # Apply path filter if provided
            if path_filter is not None and not endpoint_path.startswith(path_filter):
                continue

            if query_lower in search_text:
                matches.append((endpoint_path, info))

        if not matches:
            if path_filter:
                return (
                    f'No endpoints found matching "{query}" '
                    f'with path filter "{path_filter}".'
                )
            return f'No endpoints found matching "{query}".'

        # Format results
        if path_filter:
            header = (
                f'Found {len(matches)} endpoints matching "{query}" '
                f'(filter: "{path_filter}"):'
            )
        else:
            header = f'Found {len(matches)} endpoints matching "{query}":'

        lines = [header, ""]
        for i, (ep_path, info) in enumerate(matches, 1):
            lines.append(f"{i}. **{ep_path}** - {info.description}")

        return "\n".join(lines)

    def explain(self, path: str) -> str | None:
        """Get detailed description of an endpoint.

        Args:
            path: Endpoint path (e.g., "core/logs", "addons/{slug}/info")

        Returns:
            Formatted text with endpoint details, or None if not found or unavailable.
        """
        if not self._available:
            return None

        info = SUPERVISOR_ENDPOINTS.get(path)
        if info is None:
            return None

        lines = [f"## {path}"]

        # Description
        lines.append("")
        lines.append(info.description)

        # Method
        lines.append("")
        lines.append(f"**Method:** {info.method}")

        # API path
        lines.append(f"**API Path:** {info.path}")

        # Response type
        if info.returns_text:
            lines.append("**Returns:** Plain text (logs)")
        else:
            lines.append("**Returns:** JSON")

        # Path parameters
        if info.path_params:
            lines.append("")
            lines.append("### Path Parameters")
            for param in info.path_params:
                param_info = info.params_schema.get(param, {})
                if isinstance(param_info, dict):
                    desc = param_info.get("description", "")
                    param_type = param_info.get("type", "string")
                    lines.append(f"- **{param}** (required) [{param_type}]: {desc}")
                else:
                    lines.append(f"- **{param}** (required)")

        # Additional parameters
        other_params = {
            k: v for k, v in info.params_schema.items() if k not in info.path_params
        }
        if other_params:
            lines.append("")
            lines.append("### Parameters")
            for param_name, param_info in other_params.items():
                if isinstance(param_info, dict):
                    desc = param_info.get("description", "")
                    param_type = param_info.get("type", "any")
                    lines.append(f"- **{param_name}** [{param_type}]: {desc}")
                else:
                    lines.append(f"- **{param_name}**")

        return "\n".join(lines)

    def schema(self, path: str) -> str | None:
        """Get schema information for an endpoint.

        Args:
            path: Endpoint path

        Returns:
            Formatted schema text, or None if not found.
        """
        if not self._available:
            return None

        info = SUPERVISOR_ENDPOINTS.get(path)
        if info is None:
            return None

        lines = [f"## {path} Parameters", ""]

        if info.params_schema:
            for param_name, param_info in info.params_schema.items():
                if isinstance(param_info, dict):
                    param_type = param_info.get("type", "any")
                    desc = param_info.get("description")
                    required = param_name in info.path_params

                    req_str = " (required)" if required else ""
                    type_str = f" - type: {param_type}"

                    lines.append(f"- **{param_name}**{req_str}{type_str}")
                    if desc:
                        lines.append(f"  {desc}")
                else:
                    lines.append(f"- **{param_name}**")
        else:
            lines.append("No parameters required.")

        return "\n".join(lines)

    def has_command(self, path: str) -> bool:
        """Check if an endpoint exists.

        Returns False if Supervisor is not available.
        """
        if not self._available:
            return False
        return path in SUPERVISOR_ENDPOINTS

    def parse_call_args(
        self, path: str, arguments: dict[str, object], user_id: str | None
    ) -> ToolEffect:
        """Parse and validate call arguments for an endpoint.

        Args:
            path: Endpoint path (e.g., "core/logs", "addons/{slug}/logs")
            arguments: Tool arguments with path parameters
            user_id: Authenticated user ID for authorization

        Returns:
            SupervisorCall effect on success, Done with error otherwise.
        """
        if not self._available:
            return _make_error("Supervisor is not available on this installation.")

        info = SUPERVISOR_ENDPOINTS.get(path)
        if info is None:
            return _make_error(f"Endpoint not found: {path}")

        # Substitute path parameters
        api_path = info.path
        remaining_args = dict(arguments)

        for param in info.path_params:
            param_value = remaining_args.pop(param, None)
            if param_value is None:
                return _make_error(f"Missing required path parameter: {param}")
            if not isinstance(param_value, str):
                return _make_error(
                    f"Invalid path parameter '{param}' (must be a string)"
                )
            api_path = api_path.replace(f"{{{param}}}", param_value)

        return SupervisorCall(
            method=info.method,
            path=api_path,
            params=remaining_args,
            user_id=user_id,
            continuation=FormatSupervisorResponse(),
            returns_text=info.returns_text,
        )
