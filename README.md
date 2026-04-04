# <img src="custom_components/hamster_mcp/brand/icon.svg" alt="Hamster icon" width="64"> Hamster MCP

[![HACS: Custom](https://img.shields.io/badge/HACS-Custom-orange)](https://hacs.xyz/)
[![HA: 2025.2+](https://img.shields.io/badge/HA-2025.2+-blue)](https://www.home-assistant.io/)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue)](LICENSE-MIT)

Let AI assistants control, query, and troubleshoot your Home Assistant
setup.

## What Can It Do?

Hamster MCP connects AI assistants — like Claude, ChatGPT, Cursor, and
others — to your Home Assistant instance. Once connected, you can ask
your AI assistant to:

- **Check on your home** — "Which lights are on right now?" or "What's
  the temperature in the bedroom?"
- **Control devices** — "Turn on the porch light at 50% brightness" or
  "Set the thermostat to 72"
- **Find problems** — "Are any of my entities unavailable?" or "Show me
  devices that are offline"
- **Explore your setup** — "List all automations" or "What devices are
  in the living room?"
- **Dig into system details** — "Show me the Home Assistant logs" or
  "What add-ons are installed?" (HA OS only)

## How It Works

Hamster MCP runs inside your Home Assistant as a custom integration. It
gives your AI assistant a way to discover everything your HA instance
can do — all your services, entities, devices, and areas — automatically.
When you add a new device or automation, the AI can find and use it
without any extra configuration.

Behind the scenes, your AI assistant explores what's available in a few
quick steps before taking action. This means it handles any HA service
or query without needing hundreds of pre-defined tools, but the first
interaction in a conversation may take a moment while the AI gets
oriented.

## What You Need

- **Home Assistant 2025.2 or later**
- **[HACS](https://hacs.xyz/)** (for the recommended install method)
- **An AI tool that supports MCP** — see [Connecting Your AI
  Tool](#connecting-your-ai-tool) for compatible clients and setup
  links

## Installation

### HACS (Recommended)

1. Open HACS → Integrations → three-dot menu → **Custom repositories**.
2. Add `https://github.com/altendky/hamster-mcp` with category
   **Integration**.
3. Search for **Hamster MCP** in HACS and install it.
4. Restart Home Assistant.
5. Go to
   [Settings → Devices & Services](https://my.home-assistant.io/redirect/integrations/)
   → **Add Integration** → **Hamster MCP**.

### Manual

1. Copy the `custom_components/hamster_mcp` directory into your Home
   Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to
   [Settings → Devices & Services](https://my.home-assistant.io/redirect/integrations/)
   → **Add Integration** → **Hamster MCP**.

## Connecting Your AI Tool

Once the integration is running, point your AI tool at your Home
Assistant instance:

- **URL:** `https://<your-ha-host>/api/hamster_mcp`
- **Transport:** Streamable HTTP

### Network access

The MCP endpoint is served by Home Assistant itself, so it's reachable
wherever your HA instance is.

- **Local AI tools** (Claude Desktop, Cursor, etc.) work as long as
  they're on the same network as your HA instance.
- **Cloud AI tools** (Claude.ai, ChatGPT, etc.) need your HA instance
  to be accessible from the internet — through
  [Nabu Casa](https://www.nabucasa.com/),
  a reverse proxy, or similar.

### Authentication

Some AI tools will prompt you to log in through Home Assistant
automatically — just follow the login screen when it appears. Others
need a static token: create a
[Long-Lived Access Token](https://www.home-assistant.io/docs/authentication/#your-account-profile)
in your HA profile (under Security) and provide it as a Bearer token in
your AI tool's configuration.

### Compatible clients

These AI tools are known to work with Hamster MCP. Follow the setup
links for instructions on adding an MCP server in each tool:

| Client | Local / Cloud | Setup guide |
| --- | --- | --- |
| [Claude.ai](https://claude.ai) | Cloud | [Custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp) |
| [ChatGPT](https://chatgpt.com) | Cloud | [Developer mode](https://platform.openai.com/docs/guides/developer-mode) |
| [Claude Desktop](https://claude.ai/download) | Local | [Local servers](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop) / [Remote servers](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp) |
| [Claude Code](https://claude.com/product/claude-code) | Local | [MCP setup](https://code.claude.com/docs/en/mcp) |
| [Cursor](https://www.cursor.com/) | Local | [MCP setup](https://docs.cursor.com/context/model-context-protocol) |

Any MCP client that supports Streamable HTTP transport should work.
See the [full client list](https://modelcontextprotocol.io/clients) on
the MCP website.

## Try It Out

After connecting, try asking your AI assistant:

- "What devices are in my living room?"
- "Are any of my entities unavailable?"
- "Turn on the kitchen light to 50% brightness."

If you get a useful answer, everything is working.

## Status

Hamster MCP is in early release — functional and actively developed.
Feedback and bug reports are welcome via
[GitHub Issues](https://github.com/altendky/hamster-mcp/issues).

## License

Licensed under either of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE))
- MIT License ([LICENSE-MIT](LICENSE-MIT))

at your option.
