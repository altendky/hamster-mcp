# Hamster

![Hamster icon](custom_components/hamster/brand/icon.png)

[![CI](https://github.com/altendky/hamster/actions/workflows/ci.yml/badge.svg)](https://github.com/altendky/hamster/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/altendky/hamster)](LICENSE-MIT)

Home Assistant MCP Server --- exposes HA's full capabilities via the
[Model Context Protocol](https://modelcontextprotocol.io/).

## What Is This?

Hamster is a Home Assistant custom component that dynamically generates MCP
tools from HA's service registry at runtime.
Unlike other HA MCP projects that define tools statically, Hamster discovers
all available services and their schemas automatically.

## Status

**Beta.** Functional and ready for testing and feedback.

## Key Features

- **Dynamic tool generation** from `hass.services.async_services()` --- no
  static tool definitions
- **Built-in HA authentication** via `HomeAssistantView` --- no separate
  tokens or OAuth setup
- **Tristate tool control** --- enable, disable, or auto-discover each service
- **Sans-IO protocol core** --- fully testable without mocking
- **Full admin access** --- services, states, registries, automations,
  dashboards, supervisor (when available)

## Requirements

- Home Assistant 2025.2 or later
- Python 3.13 or later

## Installation

### HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) if you haven't already.
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → Menu (three dots) → Custom repositories
   - URL: `https://github.com/altendky/hamster`
   - Category: Integration
3. Search for "Hamster MCP" in HACS and install it.
4. Restart Home Assistant.
5. Add the integration via Settings → Devices & Services → Add Integration → Hamster MCP.

### Manual Installation

1. Copy the `custom_components/hamster` directory to your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via Settings → Devices & Services → Add Integration → Hamster MCP.

## Usage

After installation, the MCP server is available at:

```text
POST https://<your-ha-host>/api/hamster
```

This uses the [Streamable HTTP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http)
MCP transport. Authentication is handled by Home Assistant --- create a
**Long-Lived Access Token** in your HA user profile (under Security) and pass
it as a Bearer token:

```text
Authorization: Bearer <your-token>
```

### Configuration

The integration requires no configuration to get started --- just confirm the
setup when adding it. Optional settings are available under the integration's
**Configure** button:

- **Auto-fetch docs on startup** --- automatically fetch WebSocket API
  documentation for richer tool descriptions (default: on)
- **Docs URL / Git ref** --- customize the source for WebSocket API docs

## Documentation

See [docs/src/project/index.md](docs/src/project/index.md) for architecture,
principles, and design decisions.

## License

Licensed under either of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
- MIT License ([LICENSE-MIT](LICENSE-MIT))

at your option.
