"""Button platform for Hamster MCP integration.

Provides a button entity to refresh WebSocket command documentation
from the Home Assistant developer docs repository.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity

from .const import DEFAULT_DOCS_GIT_REF

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from ._runtime import EntryRuntime

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities for Hamster MCP."""
    async_add_entities([HamsterRefreshDocsButton(entry)])


class HamsterRefreshDocsButton(ButtonEntity):
    """Button to refresh WebSocket command documentation from GitHub.

    Not a dataclass: Inherits from ButtonEntity, a Home Assistant framework base
    class that defines the button entity contract. Framework subclasses must follow
    their parent class's initialization and lifecycle patterns. TODO: Investigate
    whether dataclass inheritance with Home Assistant entity base classes is viable.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "refresh_websocket_docs"
    _attr_icon = "mdi:file-document-refresh"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the button.

        Args:
            entry: Config entry for the integration
        """
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_refresh_websocket_docs"

    async def async_press(self) -> None:
        """Handle button press --- refresh WebSocket docs."""
        runtime: EntryRuntime = self._entry.runtime_data

        git_ref = self._entry.options.get("docs_git_ref", DEFAULT_DOCS_GIT_REF)

        try:
            result = await runtime.refresh_docs(git_ref=git_ref)
            _LOGGER.info(
                "WebSocket docs refreshed: %d/%d commands enriched",
                result["commands_enriched"],
                result["commands_total"],
            )
        except Exception:
            _LOGGER.exception("Failed to refresh WebSocket docs")
