# Development

Placeholder --- to be written during Phase 1 implementation.

## Prerequisites

- [mise](https://mise.jdx.dev/) for tool management
- Python 3.14 (installed via mise)
- pre-commit (installed via mise)
- OpenCode 1.17.4 and opencode-orchestrator-mcp 0.7.3 (installed via mise)

## Setup

```bash
mise install
uv sync --extra dev
pre-commit install
```

## OpenCode Orchestrator

The repository includes minimal OpenCode orchestrator support:

- `mise.toml` pins OpenCode `1.17.4` and `opencode-orchestrator-mcp` `0.7.3`.
- The MCP server command uses `mise exec` so OpenCode resolves the repo-pinned
  orchestrator binary.
- `OPENCODE_BINARY` points the orchestrator at the pinned OpenCode binary.
- `opencode.json` wires only the orchestrator MCP server and defines the
  orchestration-only `delegate` primary agent.

Restart OpenCode after changing `opencode.json` or files under `.opencode/`.
This initial setup does not require `agentic-mcp`, Thoughts configuration, or
mount configuration.

## Running Tests

```bash
pytest src/
```

## Pre-commit Hooks

```bash
pre-commit run --all-files
```

## Project Structure

See [Architecture](architecture.md) for the full package layout.
