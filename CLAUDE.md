# Universal Prompt Creation Engine

## Project Overview

An MCP server that provides a 10-dimensional philosophical manifold for principled prompt construction. Built on NetworkX (graph compute) + numpy (linear algebra) + SQLite (persistence) + Python MCP SDK (protocol).

The engine does not generate prompts. It measures intent across 10 philosophical axes and returns a construction basis from which the client constructs.

## Architecture

- **3-Level Schema**: Axiom Layer (10 philosophical branches) → Schema Layer (constructs per branch) → Coordinate Layer (computed positions)
- **External Surface**: 3 MCP tools (`create_prompt_basis`, `explore_space`, `extend_schema`) + 4 prompts + 3 resources
- **Internal Layers** (top to bottom):
  1. Multi-Pass Orchestrator (stress_test, triangulate — invokes pipeline N times)
  2. Pipeline (7 operators — single forward pass)
  3. Graph Query Layer + Graph Mutation Layer (structured graph access)
  4. Embedding Cache + TF-IDF Cache (lifecycle-managed, auto-invalidate on graph mutation)
  5. NetworkX (compute) + SQLite (persist)

## Key Design Decisions

See `docs/adr/` for full Architecture Decision Records:
- ADR-001: NetworkX as graph engine
- ADR-002: 10-axis philosophical manifold
- ADR-003: 3-tool external surface
- ADR-004: Single-process stdio deployment via uvx
- ADR-005: numpy as sole additional dependency (no scipy, no scikit-learn)
- ADR-006: Canonical/user data separation with SQLite write protection
- ADR-007: Single forward-pass pipeline with multi-pass orchestrator
- ADR-008: Tag-based + TF-IDF intent parsing (no LLM dependency)

## Dependencies

```
networkx    # graph engine — pure Python
numpy       # linear algebra — eigendecomposition, vectors, TF-IDF
mcp         # MCP protocol SDK
sqlite3     # Python stdlib — no install needed
```

No scipy. No scikit-learn. See ADR-005.

## Build & Run

```bash
# Development
pip install -e ".[dev]"
python -m advanced_prompting_engine

# Via uvx (production)
uvx advanced-prompting-engine
```

## Project Structure

```
advanced-prompting-engine/
├── CLAUDE.md
├── docs/
│   ├── DESIGN.md                          # Full design specification
│   └── adr/
│       ├── 001-networkx-as-graph-engine.md
│       ├── 002-ten-axis-philosophical-manifold.md
│       ├── 003-three-tool-external-surface.md
│       ├── 004-single-process-stdio-deployment.md
│       ├── 005-numpy-sole-additional-dependency.md
│       ├── 006-canonical-user-data-separation.md
│       ├── 007-single-pass-pipeline-with-multi-pass-orchestrator.md
│       └── 008-tag-tfidf-intent-parsing.md
├── src/
│   └── advanced_prompting_engine/
│       ├── __init__.py
│       ├── __main__.py                    # Entry point
│       ├── server.py                      # MCP server setup, tool/resource/prompt registration
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── store.py                   # SQLite persistence layer (canonical + user tables)
│       │   ├── query.py                   # Graph Query Layer — structured read access
│       │   ├── mutation.py                # Graph Mutation Layer — writes with contradiction detection
│       │   ├── canonical.py               # Canonical graph data (shipped Level 1 + Level 2)
│       │   └── schema.py                  # 3-level schema definitions, node/edge types
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── embedding.py               # Spectral embedding cache (lifecycle-managed)
│       │   └── tfidf.py                   # TF-IDF vector cache (lifecycle-managed)
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── runner.py                  # Pipeline orchestration — runs stages 1-7 in sequence
│       │   ├── intent_parser.py           # Stage 1: NL → raw partial coordinate
│       │   ├── coordinate_resolver.py     # Stage 2: CSP, constraint propagation, gap-filling
│       │   ├── position_computer.py       # Stage 3: spectral embedding lookup, centroid
│       │   ├── construct_resolver.py      # Stage 4: active constructs per branch
│       │   ├── tension_analyzer.py        # Stage 5: direct + cascading tension, resolution paths
│       │   ├── generative_analyzer.py     # Stage 6: community detection, centrality, generative edges
│       │   └── construction_bridge.py     # Stage 7: parameterized construction questions
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   └── multi_pass.py             # stress_test, triangulate — invokes pipeline N times
│       ├── math/
│       │   ├── __init__.py
│       │   ├── distance.py                # Graph distance metrics (weighted path, coordinate distance)
│       │   ├── embedding.py               # Spectral embedding computation (Laplacian, eigendecomposition)
│       │   ├── csp.py                     # Constraint satisfaction (arc consistency, candidate scoring)
│       │   ├── tension.py                 # Tension propagation (direct, cascade, decay)
│       │   ├── community.py               # Community detection (Louvain wrapper)
│       │   ├── centrality.py              # Centrality measures (betweenness, PageRank)
│       │   ├── tfidf.py                   # TF-IDF implementation (numpy only, no sklearn)
│       │   └── optimization.py            # Pareto front computation
│       └── tools/
│           ├── __init__.py
│           ├── create_prompt_basis.py     # Primary tool — invokes pipeline
│           ├── explore_space.py           # Expert tool — delegates to query layer + orchestrator
│           └── extend_schema.py           # Authoring tool — delegates to mutation layer
├── tests/
│   ├── __init__.py
│   ├── test_pipeline/                     # Per-stage unit tests
│   ├── test_math/                         # Mathematical operation tests
│   ├── test_graph/                        # Graph query/mutation tests
│   └── test_tools/                        # MCP tool integration tests
├── pyproject.toml
└── README.md
```

## Conventions

- Each class in its own file
- Pipeline operators are internal — never exposed as MCP tools
- All graph access goes through Graph Query Layer or Graph Mutation Layer — no direct NetworkX calls elsewhere
- Canonical graph data is read-only at the DB level (SQLite triggers)
- Canonical node IDs are permanent across versions (namespaced: `branch.construct_name`)
- User extensions use provenance tagging, never modify canonical tables
- Caches (embedding, TF-IDF) are lifecycle-managed: computed at startup, invalidated on graph mutation, recomputed lazily
- Mathematical operations live in `math/` module, imported by pipeline operators and caches
- Use `print()` during development for debugging, remove when stable
- Contradiction detection lives in Graph Mutation Layer, not in individual tools
