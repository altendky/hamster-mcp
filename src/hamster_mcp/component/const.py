"""Constants for the Hamster MCP integration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from ._runtime import EntryRuntime

    type HamsterMCPConfigEntry = ConfigEntry[EntryRuntime]

DOMAIN = "hamster_mcp"
DEFAULT_IDLE_TIMEOUT: float = 1800.0  # 30 minutes
DEFAULT_ENABLE_SERVICES_GROUP: bool = True
DEFAULT_AUTO_FETCH_DOCS: bool = True
DEFAULT_DOCS_GIT_REF: str = "master"
DEFAULT_DOCS_URL_TEMPLATE: str = (
    "https://raw.githubusercontent.com/"
    "home-assistant/developers.home-assistant/"
    "{ref}/docs/api/websocket.md"
)
PLATFORMS: list[Platform] = [Platform.BUTTON]
