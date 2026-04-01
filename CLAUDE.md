# Universal Prompt Creation Engine

## Project Overview

An MCP server that provides a 10-dimensional philosophical manifold for principled prompt construction. Built on a Construct of 10 planes — each a 10x10 grid of epistemic observation points — interconnected through nexi, gems, and spokes. Implemented with NetworkX (graph compute) + numpy (linear algebra) + SQLite (persistence) + Python MCP SDK (protocol).

The engine does not generate prompts. It measures intent across 10 philosophical axes and returns a construction basis from which the client constructs.

## Architecture

- **Construct**: 10 planes (branches), each a 10x10 grid of 100 observation points with position-determined classification and potency. See `docs/CONSTRUCT.md`.
- **3-Level Schema**: Axiom Layer (10 branches with 2 sub-dimensions each) → Schema Layer (10x10 grids, 100 constructs per branch, 1000 total) → Coordinate Layer (computed (x,y) positions)
- **Inter-Branch**: 90 directional nexi producing 90 gems, organized as 10 spokes converging on a central gem. Dual view: network (pair-level) and radial (branch-level).
- **External Surface**: 3 MCP tools (`create_prompt_basis`, `explore_space`, `extend_schema`) + 4 prompts + 3 resources
- **Internal Layers** (top to bottom):
  1. Multi-Pass Orchestrator (stress_test, triangulate, deepen)
  2. Pipeline (8 stages — single forward pass)
  3. Graph Query Layer + Graph Mutation Layer (structured graph access)
  4. Embedding Cache + TF-IDF Cache (lifecycle-managed, auto-invalidate on graph mutation)
  5. NetworkX (compute, 1101 nodes, 1629 edges) + SQLite (persist, canonical/user tables)

## Key Documents

| Document | Purpose |
|---|---|
| `docs/CONSTRUCT.md` | Standalone Construct specification — what planes, points, spectrums, nexi, gems, spokes ARE |
| `docs/CONSTRUCT-INTEGRATION.md` | How Construct elements map to engine components, section impact map |
| `docs/DESIGN.md` | Full engine design specification |
| `docs/adr/` | Architecture Decision Records (12 total) |

## Key Design Decisions

See `docs/adr/` for full Architecture Decision Records:

| ADR | Decision |
|---|---|
| 001 | NetworkX as graph engine |
| 002 | 10-axis philosophical manifold |
| 003 | 3-tool external surface |
| 004 | Single-process stdio deployment via uvx |
| 005 | numpy as sole additional dependency (no scipy, no scikit-learn) |
| 006 | Canonical/user data separation with SQLite write protection |
| 007 | Single forward-pass pipeline with multi-pass orchestrator |
| 008 | Tag-based + TF-IDF intent parsing (no LLM dependency) |
| 009 | Grid-structured Schema Layer (10x10 grids, position-determined classification/potency) |
| 010 | Construct epistemic questions as shipped canonical content (1000 constructs) |
| 011 | Nexus-gem-spoke inter-branch architecture |
| 012 | Spoke as computable behavioral signature (4 properties + classification) |

## Dependencies

```
networkx    # graph engine — pure Python
numpy       # linear algebra — eigendecomposition, vectors, TF-IDF, spoke stats
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
│   ├── DESIGN.md                              # Full design specification
│   ├── CONSTRUCT.md                           # Standalone Construct specification
│   ├── CONSTRUCT-INTEGRATION.md               # Construct-to-engine mapping
│   └── adr/
│       ├── 001-networkx-as-graph-engine.md
│       ├── 002-ten-axis-philosophical-manifold.md
│       ├── 003-three-tool-external-surface.md
│       ├── 004-single-process-stdio-deployment.md
│       ├── 005-numpy-sole-additional-dependency.md
│       ├── 006-canonical-user-data-separation.md
│       ├── 007-single-pass-pipeline-with-multi-pass-orchestrator.md
│       ├── 008-tag-tfidf-intent-parsing.md
│       ├── 009-grid-structured-schema-layer.md
│       ├── 010-construct-as-canonical-content.md
│       ├── 011-nexus-gem-spoke-architecture.md
│       └── 012-spoke-behavioral-signature.md
├── src/
│   └── advanced_prompting_engine/
│       ├── __init__.py
│       ├── __main__.py                        # Entry point
│       ├── server.py                          # MCP server setup, tool/resource/prompt registration
│       ├── graph/
│       │   ├── __init__.py
│       │   ├── store.py                       # SQLite persistence (canonical + user tables)
│       │   ├── query.py                       # Graph Query Layer — grid-aware read access
│       │   ├── mutation.py                    # Graph Mutation Layer — writes with contradiction detection
│       │   ├── canonical.py                   # Canonical graph data (1000 constructs, 90 nexi, 1 central gem)
│       │   ├── grid.py                        # Grid structure — classification, potency, spectrum generation
│       │   └── schema.py                      # 3-level schema definitions, node/edge types
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── embedding.py                   # Spectral embedding cache (1101 nodes, lifecycle-managed)
│       │   └── tfidf.py                       # TF-IDF vector cache (1000 questions, lifecycle-managed)
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── runner.py                      # Pipeline orchestration — runs stages 1-8 in sequence
│       │   ├── intent_parser.py               # Stage 1: NL → raw partial coordinate (x,y) positions
│       │   ├── coordinate_resolver.py         # Stage 2: CSP, constraint propagation, gap-filling
│       │   ├── position_computer.py           # Stage 3: spectral embedding lookup, centroid
│       │   ├── construct_resolver.py          # Stage 4: active constructs per branch with classification/potency
│       │   ├── tension_analyzer.py            # Stage 5: potency-weighted tension + spectrum oppositions
│       │   ├── nexus_gem_analyzer.py          # Stage 6: nexus integration, gem computation
│       │   ├── spoke_analyzer.py              # Stage 7: spoke behavioral signatures, central gem coherence
│       │   └── construction_bridge.py         # Stage 8: construction questions + full output assembly
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   └── multi_pass.py                  # stress_test, triangulate, deepen
│       ├── math/
│       │   ├── __init__.py
│       │   ├── distance.py                    # Graph distance metrics (weighted path, coordinate distance)
│       │   ├── embedding.py                   # Spectral embedding (Laplacian, eigendecomposition)
│       │   ├── csp.py                         # Constraint satisfaction (arc consistency, candidate scoring)
│       │   ├── tension.py                     # Potency-weighted tension propagation (direct, spectrum, cascade)
│       │   ├── community.py                   # Community detection (Louvain wrapper)
│       │   ├── centrality.py                  # Centrality measures (betweenness, PageRank)
│       │   ├── tfidf.py                       # TF-IDF implementation (numpy only, no sklearn)
│       │   ├── spoke.py                       # Spoke shape computation (strength, consistency, polarity, contribution)
│       │   ├── gem.py                         # Gem magnitude computation
│       │   └── optimization.py                # Pareto front computation
│       └── tools/
│           ├── __init__.py
│           ├── create_prompt_basis.py         # Primary tool — invokes pipeline
│           ├── explore_space.py               # Expert tool — delegates to query layer + orchestrator
│           └── extend_schema.py               # Authoring tool — delegates to mutation layer
├── tests/
│   ├── __init__.py
│   ├── test_pipeline/                         # Per-stage unit tests (8 stages)
│   ├── test_math/                             # Mathematical operation tests
│   ├── test_graph/                            # Graph query/mutation/grid tests
│   └── test_tools/                            # MCP tool integration tests
├── pyproject.toml
└── README.md
```

## Conventions

- Each class in its own file
- Pipeline stages are internal — never exposed as MCP tools
- All graph access goes through Graph Query Layer or Graph Mutation Layer — no direct NetworkX calls elsewhere
- Canonical graph data is read-only at the DB level (SQLite triggers)
- Canonical node IDs are permanent across versions (format: `branch.x_y` for constructs, `nexus.source.target` for nexi)
- User extensions use provenance tagging, never modify canonical tables
- Caches (embedding, TF-IDF) are lifecycle-managed: computed at startup, invalidated on graph mutation, recomputed lazily
- Mathematical operations live in `math/` module, imported by pipeline stages and caches
- Grid structure logic (classification, potency derivation, spectrum generation) lives in `graph/grid.py`
- Nexus, gem, and spoke computations are separate math modules (`math/gem.py`, `math/spoke.py`)
- Potency weighting is applied in tension, gem, and spoke computations — never ignored
- Use `print()` during development for debugging, remove when stable
- Contradiction detection lives in Graph Mutation Layer, not in individual tools
- The Construct specification (`docs/CONSTRUCT.md`) is the source of truth for what planes, points, spectrums, nexi, gems, spokes, and the central gem ARE — use engine-specific language only in engine code, not in the Construct spec

## Key Terminology

Canonical definitions from CONSTRUCT.md §21:

| Term | Definition |
|---|---|
| Construct | The full 10-plane mediated interpretive system |
| Plane | A domain of meaning containing a 10 x 10 grid of points |
| Point | A coordinate-defined possibility of observation within a plane |
| Edge point | A perimeter point with amplified structural potency |
| Center point | An interior point with synthesizing structural role |
| Corner | One of the four perimeter extremities of a plane |
| Edge midpoint | A designated axial balancing point on an edge |
| Spectrum | A structural opposition between edge positions on a plane |
| Nexus | A mediating locus between two planes (45 unique sites, 90 directional participations) |
| Gem | The condensed integrated state of a nexus interaction |
| Central gem | The unique convergence point of all inter-plane relations |
| Spoke | One plane's total outward engagement profile |
| Wheel | The radial representation of the inter-plane system |
| Potency | Position-derived weight hierarchy (semantic; numeric values are implementation defaults, see CONSTRUCT.md §20.4) |
