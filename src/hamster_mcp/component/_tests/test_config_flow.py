"""Tests for config_flow.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import (  # type: ignore[import-untyped]
    MockConfigEntry,
)

from hamster_mcp.component.config_flow import HamsterConfigFlow
from hamster_mcp.component.const import (
    DEFAULT_AUTO_FETCH_DOCS,
    DEFAULT_DOCS_GIT_REF,
    DEFAULT_DOCS_URL_TEMPLATE,
    DOMAIN,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations for testing."""


async def test_form_shows_on_initial_step(hass: HomeAssistant) -> None:
    """Test that the form is shown on the initial step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result.get("errors") in (None, {})


async def test_entry_created_on_submit(hass: HomeAssistant) -> None:
    """Test that entry is created when form is submitted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM

    # Submit the form (user_input is empty since we have no fields)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hamster MCP"
    assert result["data"] == {}


async def test_version_correct() -> None:
    """Test that the config flow has correct version."""
    # DOMAIN is set by the ConfigFlow decorator and stored differently
    assert HamsterConfigFlow.VERSION == 1


async def test_single_config_entry_abort(hass: HomeAssistant) -> None:
    """Test that a second config entry is aborted (single_config_entry).

    Note: We don't actually load/setup the entry since that requires HTTP
    infrastructure. The single_config_entry abort happens based on the
    entry existing in the config entries registry, not on it being loaded.
    """
    # First entry - complete the flow to create entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Second entry should be aborted - single_config_entry enforces this
    # at flow init time based on existing entries
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


# --- Options flow tests ---


async def test_options_flow_shows_form(hass: HomeAssistant) -> None:
    """Test that the options flow shows a form with expected fields."""
    entry = MockConfigEntry(domain=DOMAIN, title="Hamster MCP", data={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    data_schema = result["data_schema"]
    assert data_schema is not None
    schema_keys = {str(k) for k in data_schema.schema}
    assert schema_keys == {"auto_fetch_docs", "docs_url_template", "docs_git_ref"}


async def test_options_flow_saves_user_input(hass: HomeAssistant) -> None:
    """Test that submitting the options flow creates an entry with user data."""
    entry = MockConfigEntry(domain=DOMAIN, title="Hamster MCP", data={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    user_input = {
        "auto_fetch_docs": False,
        "docs_url_template": "https://example.com/{ref}/docs.md",
        "docs_git_ref": "main",
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=user_input
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == user_input
    assert entry.options == user_input


async def test_options_flow_defaults_from_existing_options(
    hass: HomeAssistant,
) -> None:
    """Test that form defaults reflect previously saved options."""
    saved_options = {
        "auto_fetch_docs": False,
        "docs_url_template": "https://custom.example.com/{ref}/ws.md",
        "docs_git_ref": "develop",
    }
    entry = MockConfigEntry(
        domain=DOMAIN, title="Hamster MCP", data={}, options=saved_options
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM

    data_schema = result["data_schema"]
    assert data_schema is not None
    defaults = {str(k): k.default() for k in data_schema.schema}
    assert defaults == saved_options


async def test_options_flow_defaults_without_existing_options(
    hass: HomeAssistant,
) -> None:
    """Test that form defaults use constants when no options are saved."""
    entry = MockConfigEntry(domain=DOMAIN, title="Hamster MCP", data={})
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM

    data_schema = result["data_schema"]
    assert data_schema is not None
    defaults = {str(k): k.default() for k in data_schema.schema}
    assert defaults == {
        "auto_fetch_docs": DEFAULT_AUTO_FETCH_DOCS,
        "docs_url_template": DEFAULT_DOCS_URL_TEMPLATE,
        "docs_git_ref": DEFAULT_DOCS_GIT_REF,
    }
