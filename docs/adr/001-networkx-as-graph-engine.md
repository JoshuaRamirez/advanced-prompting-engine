# ADR-001: NetworkX as Graph Engine

**Date**: 2026-03-27
**Status**: Accepted

## Context

The engine requires a graph database or library that provides:
- First-class graph algorithms (traversal, shortest path, community detection, centrality, spectral analysis)
- Embedded/portable deployment (no external server process)
- Strong developer training depth (reliable implementation without guessing at APIs)

Candidates evaluated:

| Option | Training Depth | Portability | First-class Graph Ops |
|--------|---------------|-------------|----------------------|
| Neo4j | Very strong | Low (server) | Yes |
| NetworkX | Very strong | High (pure Python) | Yes |
| SQLite + graph layer | Very strong | Very high | No (must build) |
| RDFLib | Strong | High | No (storage, not compute) |
| igraph | Strong | High | Yes |
| CozoDB | Moderate | High | Yes |

## Decision

Use **NetworkX** as the graph engine.

## Rationale

- Pure Python, zero native dependencies — maximizes portability
- Full algorithm suite: BFS/DFS, shortest path, centrality (betweenness, eigenvector, PageRank), community detection (Louvain), transitive closure, spectral analysis
- Very strong developer training depth — high-confidence implementation
- In-memory operation with no server process — matches the single-process deployment model
- Pairs naturally with SQLite for persistence (serialize/deserialize at startup/shutdown)

## Consequences

- **Positive**: All 9 mathematical operations identified in the design are native NetworkX operations or trivially computable from them
- **Positive**: No compilation step, no native binaries, no platform-specific builds
- **Negative**: In-memory only — graph must fit in RAM. Acceptable for expected scale (~500-5000 nodes)
- **Negative**: No built-in persistence — requires SQLite layer for durability
- **Trade-off**: Not a "database" — lacks ACID transactions, concurrent access, query language. These are not required for a single-process MCP server.
