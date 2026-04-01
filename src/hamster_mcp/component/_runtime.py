"""Per-entry runtime state for Hamster MCP.

Replaces closures that previously captured local variables in
``async_setup_entry``.  Each method reads config values lazily from
``entry.options`` at call time, so stale references are impossible
even if an object is retained past an options-change reload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import time
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.service import async_get_all_descriptions

from hamster_mcp.mcp._core.groups import ServicesGroup

from .const import DEFAULT_DOCS_GIT_REF, DEFAULT_DOCS_URL_TEMPLATE

if TYPE_CHECKING:
    import asyncio

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.storage import Store

    from hamster_mcp.mcp._core.session import SessionManager
    from hamster_mcp.mcp._io.aiohttp import AiohttpMCPTransport

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=False, slots=True)
class EntryRuntime:
    """Per-config-entry mutable state.

    Methods on this class replace the closures that were previously
    defined inside ``async_setup_entry``.  Config values such as
    ``docs_url_template`` and ``docs_git_ref`` are read from
    ``entry.options`` at call time (lazy), eliminating the
    captured-at-setup / stale-reference pattern.

    Structural options (e.g. ``enable_services_group``) still require
    a full reload because they change which objects are created.

    Two-phase initialization: ``manager``, ``transport``, and ``wakeup_task``
    are set after construction because ``SessionManager`` receives
    ``self.build_instructions`` as the ``instructions_factory`` parameter.
    """

    hass: HomeAssistant
    entry: ConfigEntry
    docs_store: Store[dict[str, Any]]
    # Two-phase init fields (set after construction)
    manager: SessionManager | None = field(init=False, default=None)
    transport: AiohttpMCPTransport | None = field(init=False, default=None)
    wakeup_task: asyncio.Task[None] | None = field(init=False, default=None)

    # -- Lazy config reads ------------------------------------------------

    @property
    def docs_url_template(self) -> str:
        """URL template for WebSocket docs, read from current options."""
        return self.entry.options.get(  # type: ignore[no-any-return]
            "docs_url_template", DEFAULT_DOCS_URL_TEMPLATE
        )

    @property
    def docs_git_ref(self) -> str:
        """Git ref for WebSocket docs, read from current options."""
        return self.entry.options.get(  # type: ignore[no-any-return]
            "docs_git_ref", DEFAULT_DOCS_GIT_REF
        )

    # -- Methods (replace closures) ---------------------------------------

    def build_instructions(
        self,
        user_id: str | None,
        user_name: str | None,
    ) -> str | None:
        """Build MCP instructions with current HA state.

        Called once per session at initialize time so the base URL
        reflects the current configuration without requiring a restart.
        Returns ``None`` when no URL is available (e.g. during early startup).
        """
        try:
            base_url = get_url(self.hass)
        except NoURLAvailableError:
            return None
        parts = [f"Home Assistant instance URL: {base_url}"]
        if user_name:
            parts.append(f"Authenticated user: {user_name}")
        return "\n".join(parts)

    async def refresh_docs(
        self,
        *,
        git_ref: str | None = None,
    ) -> dict[str, int]:
        """Fetch, parse, enrich, and cache WebSocket docs.

        Args:
            git_ref: Git ref override.  Defaults to the current
                ``docs_git_ref`` option when ``None``.
        """
        # Import here to avoid circular import at module level.
        from hamster_mcp.component import _refresh_websocket_docs

        assert self.manager is not None, "manager not set (two-phase init incomplete)"
        return await _refresh_websocket_docs(
            self.hass,
            self.manager,
            self.docs_store,
            url_template=self.docs_url_template,
            git_ref=git_ref if git_ref is not None else self.docs_git_ref,
        )

    async def handle_refresh_docs_service(self, call: Any) -> None:
        """Handle the ``hamster.refresh_docs`` service call."""
        ref = call.data.get("git_ref", self.docs_git_ref)
        try:
            result = await self.refresh_docs(git_ref=ref)
            _LOGGER.info(
                "WebSocket docs refreshed via service: "
                "%d/%d commands enriched (ref=%s)",
                result["commands_enriched"],
                result["commands_total"],
                ref,
            )
        except Exception:
            _LOGGER.exception("Failed to refresh WebSocket docs via service")

    async def rebuild_services(self) -> None:
        """Rebuild the services group after service changes."""
        assert self.manager is not None, "manager not set (two-phase init incomplete)"
        try:
            descriptions = await async_get_all_descriptions(self.hass)
            services_group = ServicesGroup.create(descriptions)
            self.manager.update_services_group(services_group)
        except Exception:
            _LOGGER.warning("Failed to rebuild services group, keeping existing")

    def on_service_event(self, event: Event) -> None:
        """Handle service registered/removed events."""
        assert self.manager is not None, "manager not set (two-phase init incomplete)"
        assert self.transport is not None, (
            "transport not set (two-phase init incomplete)"
        )
        self.manager.notify_services_changed(time.monotonic())
        self.transport.notify_activity()

    async def auto_fetch_docs(self) -> None:
        """Fetch docs from GitHub in the background."""
        ref = self.docs_git_ref
        try:
            result = await self.refresh_docs(git_ref=ref)
            _LOGGER.info(
                "Auto-fetched WebSocket docs: %d/%d commands enriched (ref=%s)",
                result["commands_enriched"],
                result["commands_total"],
                ref,
            )
        except Exception:
            _LOGGER.warning(
                "Auto-fetch of WebSocket docs failed (will use cached if available)"
            )
