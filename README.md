# <img src="custom_components/hamster_mcp/brand/icon.svg" alt="Hamster icon" width="64"> Hamster MCP

[![HACS: Custom](https://img.shields.io/badge/HACS-Custom-orange)](https://hacs.xyz/)
[![HA: 2025.2+](https://img.shields.io/badge/HA-2025.2+-blue)](https://www.home-assistant.io/)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue)](LICENSE-MIT)

Full AI debugging and maintenance access to your Home Assistant.

## What Can It Do?

Hamster MCP connects AI assistants — like Claude, ChatGPT, Cursor, and
others — to your Home Assistant instance. It's built for debugging and
maintenance — the kind of access you need when something isn't working
or you want to understand what's going on inside your system.

- **Debug voice assistants** — "Show me the last 5 voice pipeline runs
  and why speech-to-text failed"
- **Inspect Matter networks** — "What Matter nodes are in my network
  and are any unreachable?"
- **Review system health** — "List all repairs and diagnostics for my
  system"
- **Debug automations** — "Show me the trace for the last time the
  motion automation ran"
- **Check logs** — "Show me the Supervisor logs from the last hour" or
  "Are there any errors in the Home Assistant core log?"
- **Audit entity exposure** — "Which entities are exposed to Alexa
  but not to Google Assistant?"
- **Manage Bluetooth** — "What Bluetooth scanners are active and what
  are their connection stats?"

It also handles everyday tasks — turning on lights, listing automations,
checking entity states — but that's not its focus.

## How It Works

Hamster MCP runs inside your Home Assistant as a custom integration. It
exposes HA's capabilities through three source groups:

- **Services** — all HA service actions (lights, climate, automations,
  scripts, etc.), with full field descriptions and selector metadata
- **WebSocket commands** (~200 commands) — entity/device/area
  registries, history, system log, config entries, diagnostics, repairs,
  Matter, Assist Pipeline, voice/conversation, Cloud/Nabu Casa, auth
  management, trace debugging, HACS, and more
- **Supervisor** (HA OS only) — Core/Supervisor/host logs, add-on
  management, backups, host and network info

Your AI assistant discovers what's available through 6 meta-tools:

| Tool | Purpose |
| --- | --- |
| `search` | Find commands by keyword across all groups |
| `explain` | Get a detailed description of a command |
| `schema` | Get parameter types and selector details |
| `call` | Execute a command |
| `list_resources` | List available guidance documents |
| `read_resource` | Read a guidance document |

When you add a new integration, any WebSocket commands or services it
registers are available to the AI immediately — no MCP server update
needed. The tradeoff: the first interaction in a conversation may take a
moment while the AI explores what's available.

## How It Compares

There are several MCP servers for Home Assistant. Here's how Hamster
fits in:

**[ha-mcp](https://github.com/homeassistant-ai/ha-mcp)** (2k+ stars)
is the most popular, with 92 curated tools covering everyday control,
automation management, dashboards, HACS, and more. Its `ha_call_service`
tool is fully generic — it can call any HA service, including those from
custom integrations. For everyday use it's excellent. However, its other
90 tools only wrap a subset of HA's WebSocket commands. Entire
subsystems have no coverage:

- Matter (commissioning, node diagnostics, thread/wifi credentials)
- Assist Pipeline (create/manage/run/debug voice pipelines)
- Voice/Conversation (agent listing, sentence management, debug scoring)
- Cloud/Nabu Casa (subscription, remote connect/disconnect, Alexa/Google
  entity management)
- Auth management (list/create/delete users, change passwords)
- Trace debugging (set breakpoints, step through automations)
- Diagnostics and Repairs
- Bluetooth scanner management
- Shopping list, application credentials, webhooks, network config
- `validate_config`, `fire_event`, `extract_from_target`,
  `get_triggers_for_target`

**[home-assistant-vibecode-agent](https://github.com/Coolver/home-assistant-vibecode-agent)**
(500+ stars) is focused on IDE-based development — editing HA
configuration files, managing HACS packages, creating dashboards from
Cursor or VS Code. It's a two-part architecture (HA add-on + local MCP
client) with git-based versioning and rollback.

**[hass-mcp](https://github.com/voska/hass-mcp)** (280+ stars) is
intentionally lean — REST-only, no WebSocket or Supervisor access, with
guided prompts for automation creation.

**[hass-mcp-server](https://github.com/ganhammar/hass-mcp-server)**
(23 stars) is also a custom component like Hamster, but with hardcoded
tools and OAuth 2.0 support for use with Claude in the browser.

**[mcp-server-home-assistant](https://github.com/allenporter/mcp-server-home-assistant)**
(archived) is being upstreamed into Home Assistant Core itself — official
first-party MCP support is coming.

**Hamster's position:** full dynamic access to all ~200 WebSocket
commands, every service, and the Supervisor, through 6 meta-tools.
Runs inside HA as a custom component with native auth. Designed for
debugging and maintenance rather than everyday device control.

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

- **URL:** `https://<your-ha-host>:<port>/api/hamster_mcp`
  (e.g., `http://homeassistant.local:8123/api/hamster_mcp`)
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
your AI tool's configuration. Treat this token like a password — don't
share it or commit it to version control.

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

- "Show me the last 5 voice pipeline runs and their results."
- "Are there any system repairs I should look at?"
- "Show me which automations reference the front door sensor and their most recent traces."

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
