# Universal Prompt Creation Engine

## Project Overview

An MCP server that provides a 12-dimensional philosophical manifold for principled prompt construction. Built on a Construct of 12 faces — each a 12x12 grid of 144 observation points — interconnected through nexi, gems, and spokes. Organized by Vector Equilibrium geometry with cube pairing for harmonization. Implemented with NetworkX (graph topology) + numpy (computation) + SQLite (persistence) + Python MCP SDK (protocol).

The engine does not generate prompts. It measures intent across 12 philosophical axes and returns a construction basis from which the client constructs.

## Architecture

- **Construct**: 12 faces (domains), each a 12x12 grid of 144 observation points with position-determined classification and potency. See `docs/CONSTRUCT-v2.md`.
- **3-Level Schema**: Axiom Layer (12 faces with 2 sub-dimensions each) → Schema Layer (12x12 grids, 144 constructs per face, 1728 total) → Coordinate Layer (computed (x,y) positions)
- **Inter-Face**: 132 directional nexi (66 unique pairs) producing 132 gems, organized as 12 spokes converging on a central gem. Nexi stratified by cube model: 6 paired + 48 adjacent + 12 opposite.
- **Cube Pairing**: 6 complementary pairs (theoretical/applied). Paired faces harmonize through shared surfaces and positional correspondence.
- **External Surface**: 4 MCP tools (`create_prompt_basis`, `explore_space`, `extend_schema`, `interpret_basis`) + 4 prompts + 4 resources
- **Internal Layers** (top to bottom):
  1. Multi-Pass Orchestrator (stress_test, triangulate, deepen)
  2. Pipeline (8 stages — single forward pass)
  3. Graph Query Layer + Graph Mutation Layer (structured graph access)
  4. TF-IDF Cache (lifecycle-managed, auto-invalidate on graph mutation — used by explore_space, not by Stage 1)
  5. Semantic Bridge (GeometricBridge — pre-computed BGE-derived face similarity + axis projections + disambiguation overrides, used by Stage 1)
  6. NetworkX (topology, 1873 nodes, 2279 edges) + numpy (computation) + SQLite (persist, canonical/user tables)

## Key Documents

| Document | Purpose |
|---|---|
| `docs/CONSTRUCT-v2.md` | Standalone Construct specification — what faces, points, spectrums, nexi, gems, spokes ARE |
| `docs/CONSTRUCT-v2-questions.md` | All 144 construction question templates by zone |
| `docs/DESIGN.md` | Full engine design specification |
| `docs/adr/` | Architecture Decision Records (12 total) |

## Key Design Decisions

See `docs/adr/` for full Architecture Decision Records:

| ADR | Decision |
|---|---|
| 001 | NetworkX as graph engine (topology container; computation is numpy) |
| 002 | 12-axis philosophical manifold with Vector Equilibrium + cube pairing |
| 003 | External tool surface (originally 3, now 4 with interpret_basis) |
| 004 | Single-process stdio deployment via uvx |
| 005 | numpy as sole additional dependency (no scipy, no scikit-learn) |
| 006 | Canonical/user data separation with SQLite write protection |
| 007 | Single forward-pass pipeline with multi-pass orchestrator |
| 008 | Geometry-integral intent parsing via GeometricBridge (no LLM dependency) |
| 009 | Grid-structured Schema Layer (12x12 grids, invariant axis meta-meaning, polarity convention) |
| 010 | Construct epistemic questions as shipped canonical content (1728 constructs from 144 templates × 12 domains) |
| 011 | Nexus-gem-spoke inter-face architecture with cube stratification |
| 012 | Spoke as computable behavioral signature (4 properties + classification) |
| 013 | BGE-large-en-v1.5 as sole embedding source at native 1024d |

## Dependencies

```
networkx    # graph topology — pure Python
numpy       # computation — vectors, TF-IDF, tension, gem, spoke, harmonization
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
│   ├── DESIGN.md                              # Full engine design specification
│   ├── CONSTRUCT-v2.md                        # Standalone Construct specification
│   ├── CONSTRUCT-v2-questions.md              # 144 construction question templates
│   ├── GEOMETRY-NOTES.md                      # Latent geometric properties (cuboctahedron, rhombic dodecahedron)
│   ├── specs/
│   │   └── semantic-bridge-algorithms.md      # Algorithm specifications for GeometricBridge
│   └── adr/
│       ├── 001-networkx-as-graph-engine.md
│       ├── 002-twelve-axis-philosophical-manifold.md
│       ├── 003-three-tool-external-surface.md
│       ├── 004-single-process-stdio-deployment.md
│       ├── 005-numpy-sole-additional-dependency.md
│       ├── 006-canonical-user-data-separation.md
│       ├── 007-single-pass-pipeline-with-multi-pass-orchestrator.md
│       ├── 008-tag-tfidf-intent-parsing.md
│       ├── 009-grid-structured-schema-layer.md
│       ├── 010-construct-as-canonical-content.md
│       ├── 011-nexus-gem-spoke-architecture.md
│       ├── 012-spoke-behavioral-signature.md
│       └── 013-bge-embedding-source.md
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
│       │   ├── canonical.py                   # Canonical graph data (1728 constructs, 132 nexi, 1 central gem)
│       │   ├── grid.py                        # Grid structure — classification, potency, spectrum generation, degree labels
│       │   └── schema.py                      # Face definitions, node/edge types, cube pairs, nexus tiers
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── embedding.py                   # Stub (v2 positions are grid coordinates, not embeddings)
│       │   ├── centrality.py                  # Stub (v2 potency is position-derived, not graph-theoretic)
│       │   ├── hashing.py                     # Graph/content hash utilities for cache invalidation
│       │   └── tfidf.py                       # TF-IDF vector cache (1728 questions, lifecycle-managed)
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── runner.py                      # Pipeline orchestration — runs stages 1-8 in sequence
│       │   ├── intent_parser.py               # Stage 1: NL → raw partial coordinate with face weights
│       │   ├── coordinate_resolver.py         # Stage 2: gap-filling on regular grid (no CSP)
│       │   ├── position_computer.py           # Stage 3: coordinates ARE positions (identity transform)
│       │   ├── construct_resolver.py          # Stage 4: active constructs per face with weight-modulated radius
│       │   ├── tension_analyzer.py            # Stage 5: positional correspondence + cube stratification
│       │   ├── nexus_gem_analyzer.py          # Stage 6: gem computation with cube tier modulation + harmonization
│       │   ├── spoke_analyzer.py              # Stage 7: spoke behavioral signatures, central gem coherence (CV)
│       │   └── construction_bridge.py         # Stage 8: construction questions + harmonization pairs + full output
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   └── multi_pass.py                  # stress_test, triangulate, deepen
│       ├── math/
│       │   ├── __init__.py
│       │   ├── tension.py                     # Positional tension (coordinate distance × cube tier weight)
│       │   ├── tfidf.py                       # TF-IDF implementation (numpy only, no sklearn)
│       │   ├── spoke.py                       # Spoke shape computation (strength, consistency, polarity, contribution)
│       │   ├── gem.py                         # Gem magnitude (potency-weighted + positional correspondence + tier modulation)
│       │   ├── harmonization.py               # Paired face resonance (bidirectional positional alignment)
│       │   └── optimization.py                # Pareto front computation
│       ├── data/                               # Pre-computed semantic bridge artifacts (BGE-derived)
│       └── tools/
│           ├── __init__.py
│           ├── create_prompt_basis.py         # Primary tool — invokes pipeline
│           ├── explore_space.py               # Expert tool — delegates to query layer + orchestrator
│           ├── extend_schema.py               # Authoring tool — delegates to mutation layer
│           └── interpret_basis.py             # Interpretation tool — focused output from construction basis
├── tests/
│   ├── __init__.py
│   ├── test_first_principles.py               # First-principles compliance tests (66 tests across 16 principles)
│   ├── test_pipeline/                         # Per-stage unit tests
│   ├── test_math/                             # Mathematical operation tests (including harmonization)
│   ├── test_graph/                            # Graph query/mutation/grid/canonical tests
│   ├── test_tools/                            # MCP tool integration tests
│   └── test_orchestrator/                     # Multi-pass orchestrator tests
├── scripts/
│   ├── build_semantic_bridge.py               # Build script (BGE-large-en-v1.5 at 1024d)
│   ├── expand_pole_synonyms.py                # WordNet-based pole-synonym expansion proposals
│   └── benchmark_8texts.py                    # Literary text benchmark (8 canonical texts, 20 assertions)
├── Documentation/
│   └── Temporary/Execution/                   # Work effort triad (Roadmap, WorkEffort, Results)
├── pyproject.toml
└── README.md
```

## Conventions

- Each class in its own file
- "Face" not "branch" — each domain is a face of the Construct
- Pipeline stages are internal — never exposed as MCP tools
- All graph access goes through Graph Query Layer or Graph Mutation Layer — no direct NetworkX calls elsewhere
- Canonical graph data is read-only at the DB level (SQLite triggers)
- Canonical node IDs are permanent across versions (format: `face.x_y` for constructs, `nexus.source.target` for nexi)
- User extensions use provenance tagging, never modify canonical tables
- TF-IDF cache is lifecycle-managed: computed at startup, invalidated on graph mutation, recomputed lazily
- Mathematical operations live in `math/` module (6 modules), imported by pipeline stages
- Grid structure logic (classification, potency, spectrum generation, degree labels) lives in `graph/grid.py`
- Nexus, gem, spoke, and harmonization computations are separate math modules
- Potency weighting uses `effective_potency` (potency × face weight) — never raw potency alone
- Positional correspondence replaces declared cross-face edges — same position = shared archetype, opposite = tension
- Cube tier modulates all inter-face computation: paired nexi dampen tension (0.4×), opposite amplify (1.5×)
- Meaning hierarchy visible in output: corners → integration, edges → demarcation, midpoints → axial_balance, center → composition
- Use `print()` during development for debugging, remove when stable
- Contradiction detection lives in Graph Mutation Layer, not in individual tools
- Stage 1 intent parser uses GeometricBridge (pre-computed BGE-derived artifacts), not TF-IDF, for face relevance and axis projection
- Semantic bridge build-time dependencies live under `[build]` extra: `sentence-transformers`, `torch`, `wordfreq`, `nltk`. Runtime stays numpy-only (ADR-005, ADR-013)
- The Construct specification (`docs/CONSTRUCT-v2.md`) is the source of truth for what faces, points, spectrums, nexi, gems, spokes, and the central gem ARE — use engine-specific language only in engine code, not in the Construct spec

## Philosophical Geometry (v2)

The Construct's geometry is defined by three root decisions:

1. **Axis meta-meaning**: X = constitutive character (what kind of thing), Y = dispositional orientation (how it engages). Invariant across all 12 faces.
2. **Polarity convention**: Low (0) = constrained/foundational, High (11) = expansive/exploratory. Same direction on every axis of every face.
3. **Sub-dimensions**: Each face names what constitutive character and dispositional orientation mean in its domain.

These three decisions, combined with grid coordinates, produce meaning at every point through inference — not individual authoring. 144 question templates × 12 domain replacement strings = 1728 construction questions.

The 12 faces are organized as 6 complementary pairs (cube model). Paired faces share a surface and are structurally tuned to receive each other's activations (harmonization). The inter-face topology is stratified: paired nexi carry complementary resonance, adjacent nexi carry proximal interaction, opposite nexi carry maximal contrast.

The Vector Equilibrium (cuboctahedron) is latent — it describes the emergent shape of 12 equidistant faces, but is not imposed on the computation. The rhombic dodecahedron provides recursive embedding via space-filling.

## Key Terminology

Canonical definitions from CONSTRUCT-v2.md §13.2:

| Term | Definition |
|---|---|
| Construct | The full 12-face mediated interpretive system |
| Face | A domain of meaning containing a 12 × 12 grid of points |
| Point | A coordinate-defined possibility of observation within a face |
| Edge point | A perimeter point with amplified structural potency |
| Center point | An interior point with compositional structural role |
| Corner | One of the four perimeter extremities of a face — a joint pinning two outer lines together |
| Edge midpoint | A designated axial balancing point on an edge |
| Outer line | One of the 4 boundary edges of a face — produces meaning by demarcation |
| Inner line | A grid line within the face interior — produces meaning by graduation |
| Spectrum | A structural opposition between edge positions on a face |
| Constitutive character | The meta-meaning of the x-axis: what kind of thing this is within the domain |
| Dispositional orientation | The meta-meaning of the y-axis: how the thing moves or engages within the domain |
| Nexus | A mediating locus between two faces (66 unique sites, 132 directional participations) |
| Gem | The condensed integrated state of a nexus interaction |
| Central gem | The unique convergence point of all inter-face relations |
| Spoke | One face's total outward engagement profile |
| Wheel | The radial representation of the inter-face system |
| Potency | Position-derived weight hierarchy |
| Complementary pair | Two faces sharing a cube surface — one inward (theoretical), one outward (applied) |
| Harmonization | The property by which paired faces are tuned to receive each other's activations |
| Positional correspondence | Structural equivalence of same-position points across faces, created by the polarity convention |
| Inference machinery | The three authored layers (axis meta-meaning, polarity convention, sub-dimensions) that produce meaning at any coordinate |

## The 12 Domains

| # | Domain | Core Question | X-axis (constitutive) | Y-axis (dispositional) | Phase |
|---|---|---|---|---|---|
| 1 | Ontology | What entities and relationships fundamentally exist? | Particular → Universal | Static → Dynamic | Comprehension |
| 2 | Epistemology | How do we know domain states are true or justified? | Empirical → Rational | Certain → Provisional | Comprehension |
| 3 | Axiology | By what criteria and standards is worth determined? | Absolute → Relative | Quantitative → Qualitative | Comprehension |
| 4 | Teleology | What ultimate purposes do each domain serve? | Immediate → Ultimate | Intentional → Emergent | Comprehension |
| 5 | Phenomenology | How are experiences represented and realized? | Objective → Subjective | Surface → Deep | Comprehension |
| 6 | Ethics | What obligations and moral warrants govern right action? | Deontological → Consequential | Agent → Act | Evaluation |
| 7 | Aesthetics | What qualities constitute aesthetic recognition? | Autonomous → Contextual | Sensory → Conceptual | Evaluation |
| 8 | Praxeology | How are actions and intentions structured? | Individual → Coordinated | Reactive → Proactive | Application |
| 9 | Methodology | What processes govern construction and evolution? | Analytic → Synthetic | Deductive → Inductive | Application |
| 10 | Semiotics | How are signals meaningfully communicated? | Explicit → Implicit | Syntactic → Semantic | Application |
| 11 | Hermeneutics | What frameworks govern interpretation? | Literal → Figurative | Author-intent → Reader-response | Application |
| 12 | Heuristics | What practical strategies guide complexity? | Systematic → Intuitive | Conservative → Exploratory | Application |

## Cube Pairs (6 complementary pairs)

| Inward (theoretical) | Outward (applied) | Shared concern |
|---|---|---|
| Ontology | Praxeology | Being ↔ Doing |
| Epistemology | Methodology | Knowing ↔ Proceeding |
| Axiology | Ethics | Valuing ↔ Judging |
| Teleology | Heuristics | Purpose ↔ Strategy |
| Phenomenology | Aesthetics | Experiencing ↔ Recognizing form |
| Semiotics | Hermeneutics | Encoding ↔ Decoding |
