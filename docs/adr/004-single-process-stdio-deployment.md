# ADR-004: Single-Process stdio Deployment via uvx

**Date**: 2026-03-27
**Status**: Accepted

## Context

MCP servers can be deployed in several modes:
- stdio (subprocess spawned by client, communicates via stdin/stdout)
- SSE (HTTP server, communicates via Server-Sent Events)
- Embedded (library import, no protocol boundary)

The engine must be downloadable and activatable with minimal friction.

## Decision

Deploy as a **single Python process** using **stdio transport**, distributed via **PyPI/uvx**.

MCP client configuration:
```json
{
  "advanced-prompting-engine": {
    "command": "uvx",
    "args": ["advanced-prompting-engine"]
  }
}
```

## Rationale

- stdio requires no port allocation, no network configuration, no firewall rules
- `uvx` auto-resolves Python dependencies (networkx, numpy, mcp) without manual pip install
- Single process: NetworkX (in-memory), SQLite (in-process C library), MCP SDK (stdio handler) — zero external processes
- No daemon to start/stop, no background service, no container
- Activation requires only Python 3.10+ and `uvx` installed — one gate

## Consequences

- **Positive**: Maximally self-contained — the entire runtime is one OS process reading stdin and writing stdout
- **Positive**: No infrastructure to provision, monitor, or maintain
- **Positive**: Identical behavior on macOS, Linux, Windows (Python portability)
- **Negative**: Single client per process — no concurrent access. Acceptable for MCP which is inherently single-session.
- **Negative**: Requires Python 3.10+ and `uvx` on the host — not zero-install
- **Trade-off**: No HTTP endpoint means no browser-based or multi-client access. If needed in the future, SSE transport can be added alongside stdio without architectural changes.
