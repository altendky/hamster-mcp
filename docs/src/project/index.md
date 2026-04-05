# Hamster MCP

Full AI debugging and maintenance access to your Home Assistant via the
Model Context Protocol (MCP).
The project emphasizes testability through sans-IO design principles and
a meta-tool API gateway pattern.

## What Makes Hamster MCP Different

Every existing HA MCP project defines tools statically in code.
Hamster MCP uses a **meta-tool pattern** --- 6 fixed MCP tools
(`search`, `explain`, `call`, `schema`, `list_resources`, `read_resource`)
that let the LLM dynamically discover and invoke any HA capability.
Three source groups are exposed: services (via `async_get_all_descriptions()`),
WebSocket commands (via `hass.data["websocket_api"]`), and Supervisor
endpoints.  No existing project uses this approach.

Running as a custom component inside HA gives direct access to:

- Service descriptions with field definitions (not available via REST API)
- Built-in HA authentication (`requires_auth=True` on `HomeAssistantView`)
- Entity, device, and area registries
- Exposure settings (`async_should_expose()`)
- Supervisor, HACS, and other internal APIs (when available)

## Documentation

### Core Design

- [Principles](principles.md) --- Sans-IO philosophy, testability goals, import rules
- [Architecture](architecture.md) --- Layer design, package structure, module layout
- [Data Flow](data-flow.md) --- MCP protocol flow, effect/continuation dispatch

### Features

- [MCP Protocol](mcp-protocol.md) --- Streamable HTTP transport, JSON-RPC, session lifecycle
- [Tool Generation](tool-generation.md) --- Meta-tool pattern, ServiceIndex, selector descriptions
- [Tristate Control](tristate-control.md) --- Enabled/Dynamic/Disabled service model (deferred)
- [Configuration](configuration.md) --- Config flow, options flow

### Infrastructure

- [CI](ci.md) --- GitHub Actions, coverage, validation
- [Development](development.md) --- Local development, pre-commit hooks, testing
- [Release](release.md) --- PyPI + HACS distribution

### Project Management

- [Decisions](decisions.md) --- Resolved design decisions
- [Open Questions](open-questions.md) --- Pending decisions, deferred items
