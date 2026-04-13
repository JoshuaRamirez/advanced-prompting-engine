# Universal Prompt Creation Engine — Design Specification v2

## Overview

A universal prompt creation engine delivered as an MCP (Model Context Protocol) server. The engine provides a 12-dimensional philosophical manifold — grounded in a Construct of 12 faces, each a 12x12 grid of epistemic observation points — that any client can use to derive a principled construction basis for prompt creation.

The engine does not generate prompts. It measures a client's intent across 12 philosophical axes and returns a precise, dimensionally-situated construction basis from which the client constructs.

The Construct specification is defined in `CONSTRUCT-v2.md`. Construction question templates are defined in `CONSTRUCT-v2-questions.md`.

## Analog

The engine operates like a **spectrometer**. A spectrometer takes a sample, measures it across multiple spectral bands simultaneously, and returns a spectral signature. The chemist uses that signature to synthesize a compound. The instrument does not synthesize — the chemist does. The instrument provides the measurement that makes principled synthesis possible.

| Spectrometry | This Engine |
|---|---|
| The sample | The client's intent |
| The 12 spectral bands | The 12 philosophical faces (domains) |
| The spectral signature | The coordinate — a precise, reproducible grid position per face |
| Absorption peaks | Active constructs — what the sample registers strongly on |
| Spectral interference | Tensions — geometric spectrum oppositions and declared conflicts |
| Harmonic resonance | Generative combinations — constructs that amplify each other |
| Nexus interactions | How different spectral bands influence each other |
| Harmonization | Paired faces resonating through positional correspondence |
| The spoke profile | The behavioral signature of one band across the full spectrum |
| The chemist | The client — uses the signature to construct |
| The compound synthesized | The prompt |

---

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| Language | Python 3.10+ | Runtime |
| Graph engine | NetworkX (pure Python, in-memory) | First-class graph algorithms, traversal, community detection, centrality, embedding |
| Linear algebra | numpy | Spectral embedding, distance computation, TF-IDF vectors, spoke statistics |
| Persistence | SQLite (Python stdlib) | Durable storage, canonical/user data separation, ACID transactions |
| Protocol | MCP SDK (Python) | JSON-RPC over stdio, tool/resource/prompt exposure |
| Distribution | PyPI via `uvx` | Zero-config activation for MCP clients |

### Installable Dependencies

```
networkx    # graph engine — pure Python
numpy       # linear algebra — eigendecomposition, vectors, distances, spoke stats
mcp         # MCP protocol SDK
```

sqlite3 is in Python stdlib. scipy and scikit-learn are intentionally excluded — all needed operations (TF-IDF, Laplacian computation, cosine similarity, spoke statistics) are implemented directly with numpy. See ADR-005.

---

## Architecture Layers

The engine is organized as a strict layered architecture. Each layer depends only on the layers below it. No upward references.

```
┌──────────────────────────────────────────────────────────────────────┐
│  External Surface                                                    │
│  4 MCP tools + 4 prompts + 4 resources                               │
├──────────────────────────────────────────────────────────────────────┤
│  Multi-Pass Orchestrator                                             │
│  stress_test, triangulate, deepen                                    │
├──────────────────────────────────────────────────────────────────────┤
│  Pipeline (8 stages — single forward pass)                           │
│  intent → coordinate → position → constructs → tensions →            │
│  nexi/gems → spokes → construction basis                             │
├──────────────────────────────────────────────────────────────────────┤
│  Graph Query Layer              │  Graph Mutation Layer               │
│  (structured read access)       │  (writes + contradiction detect.)  │
├──────────────────────────────────────────────────────────────────────┤
│  Embedding Cache  │  TF-IDF Cache  │  Centrality Cache               │
│  (lifecycle-managed, auto-invalidate on graph mutation)               │
├──────────────────────────────────────────────────────────────────────┤
│  Semantic Bridge (GeometricBridge)                                    │
│  Pre-computed GloVe-derived face similarity + axis projections        │
├──────────────────────────────────────────────────────────────────────┤
│  NetworkX (in-memory graph)     │  SQLite (durable persistence)      │
│  ~1873 nodes, ~2000+ edges     │  canonical + user tables            │
└──────────────────────────────────────────────────────────────────────┘
```

### Layer 1: External Surface

Four MCP tools, four prompts, four resources. This is the only layer visible to clients.

**Tools:**

| Tool | Purpose | Delegates to |
|---|---|---|
| `create_prompt_basis` | Primary tool — measures intent, returns construction basis | Pipeline (all 8 stages) |
| `explore_space` | Expert tool — query the manifold, run orchestrator operations | Graph Query Layer + Orchestrator |
| `extend_schema` | Authoring tool — add user constructs and relations | Graph Mutation Layer |
| `interpret_basis` | Interpretation tool — focused output from a construction basis | Pipeline + Synthesis Layer |

**Resources:**

| Resource | Content |
|---|---|
| `ape://axiom_manifest` | The 12 philosophical faces with core questions, sub-dimensions, and action guidance |
| `ape://schema_manifest` | Current graph state — node/edge counts by type |
| `ape://coordinate_schema` | Schema for a valid coordinate object (12 faces, each with x, y, weight) |
| `ape://examples` | Example intents with expected construction basis outputs |

**Prompts:**

| Prompt | Guides the client through |
|---|---|
| `orient` | Understanding the manifold before using it |
| `build_construction_basis` | Building a complete basis from an intent |
| `compare_positions` | Comparing two intents dimensionally |
| `resolve_and_construct` | Resolving tensions before constructing |

### Layer 2: Multi-Pass Orchestrator

Wraps the pipeline for operations that require multiple passes or comparative analysis.

| Operation | What it does |
|---|---|
| `stress_test` | Runs the pipeline with perturbations to find coordinate sensitivity |
| `triangulate` | Runs the pipeline on two coordinates and computes dimensional comparison |
| `deepen` | Runs the pipeline, identifies weak branches, re-runs with targeted constraints |

### Layer 3: Pipeline (8 Stages)

A single forward pass through 8 sequential stages. Each stage reads from a shared `PipelineState` accumulator and writes its results into the next slot.

See the "Pipeline Stages" section below for detailed stage descriptions.

### Layer 4: Graph Query Layer and Graph Mutation Layer

**Graph Query Layer** — Structured read access to the NetworkX graph. All pipeline stages and the orchestrator read through this layer. Provides grid-aware queries: find constructs by face, position, classification, potency; find nexi by face pair; traverse neighborhoods; compute paths.

**Graph Mutation Layer** — All writes go through this layer. Provides contradiction detection (proposed relation checked against `CONTRADICTION_MAP`), provenance tagging for user extensions, and automatic cache invalidation on mutation.

### Layer 5: Caches

Three lifecycle-managed caches, computed at startup, invalidated on graph mutation, recomputed lazily.

| Cache | Content | Used by |
|---|---|---|
| Embedding Cache | Spectral embedding of all graph nodes (Laplacian eigendecomposition) | Stage 3 (position computation) |
| TF-IDF Cache | TF-IDF vectors for all 1728 construct questions | explore_space tool (question search) |
| Centrality Cache | Betweenness centrality and PageRank for all nodes | Stages 5–7 (tension/spoke weighting) |

### Layer 6: NetworkX + SQLite

**NetworkX** — In-memory directed graph. All nodes and edges loaded at startup. Symmetric relations stored as bidirectional edges. The graph is the authoritative runtime data structure.

**SQLite** — Durable persistence. Two table families: canonical (read-only, protected by triggers) and user (read-write). Canonical data is loaded once and never modified at the DB level. User extensions are persisted and reloaded on restart.

---

## Key Changes from v1

### Structural expansion

| Dimension | v1 | v2 |
|---|---|---|
| Domains | 10 ("branches") | 12 ("faces") |
| Grid size | 10×10 (100 points) | 12×12 (144 points) |
| Total constructs | 1000 | 1728 |
| Coordinate range | 0–9 per axis | 0–11 per axis |
| New domains | — | Ethics, Aesthetics |
| Organizing geometry | Tetractys (triangular hierarchy) | Vector Equilibrium / cuboctahedron (polyhedral equipoise) |
| Outer shell | — | Rhombic dodecahedron (dual of cuboctahedron) |

### Axis meta-meaning

v1 had per-branch axis names with no cross-branch invariant. v2 introduces invariant meta-meaning across all faces:

* **X-axis**: Constitutive character — what kind of thing this is within the domain. x=0 is elemental/foundational; x=11 is comprehensive/expansive.
* **Y-axis**: Dispositional orientation — how the thing moves or engages within the domain. y=0 is stable/grounded; y=11 is fluid/exploratory.

Each face's sub-dimensions are specific instantiations of these meta-axes.

### Polarity convention

v1 had no constraint on which sub-dimensional pole sat at which coordinate extreme. v2 enforces:

* Low (0) = constrained, foundational, structurally anchored
* High (11) = expansive, synthetic, exploratory

This ensures the 4 corner archetypes (Alpha/Beta/Gamma/Delta) hold invariantly across all 12 faces and enables positional correspondence.

### Cube pairing model

The 12 faces are organized as 6 complementary pairs, each pair sharing a cube face:

| Cube Face | Inward (theoretical) | Outward (applied) | Shared concern |
|---|---|---|---|
| 1 | Ontology | Praxeology | Being ↔ Doing |
| 2 | Epistemology | Methodology | Knowing ↔ Proceeding |
| 3 | Axiology | Ethics | Valuing ↔ Judging |
| 4 | Teleology | Heuristics | Purpose ↔ Strategy |
| 5 | Phenomenology | Aesthetics | Experiencing ↔ Recognizing form |
| 6 | Semiotics | Hermeneutics | Encoding ↔ Decoding |

### Nexus stratification

v1 had 45 unique nexus pairs (C(10,2)) with 90 directional participations, all treated uniformly. v2 has 66 unique pairs (C(12,2)) with 132 directional participations, stratified by geometric relationship:

| Kind | Count | Character |
|---|---|---|
| Paired | 6 | Complementary reflection between theoretical/applied counterparts |
| Adjacent | 48 | Proximal concerns on neighboring cube faces |
| Opposite | 12 | Distal concerns across the cube |

Total: 6 + 48 + 12 = 66 unique pairs. Stratification affects gem magnitude computation and tension weighting.

### Positional correspondence replaces cross-face edges

v1 connected constructs across branches with explicit point-to-point edges (cross-branch edges). v2 eliminates these. Inter-face relationships are determined by **positional correspondence** via the polarity convention:

* Same position on two faces = shared structural archetype (compatible)
* Opposite position on two faces = opposed structural archetype (tension)

This is a property of the shared coordinate system, not an edge in the graph. The graph no longer needs O(n^2) cross-face edges. Correspondence is computed at query time from coordinates.

### Harmonization

Paired faces (inside/outside of the same cube face) are structurally tuned to receive each other's activations. When the pipeline activates position (x,y) on one face, the paired face's (x,y) position is a natural correspondent. This is not an algorithm — it is a consequence of the shared surface and polarity convention.

### Terminology

"Branch" becomes "Face." "Plane" becomes "Face." The organizing geometry moves from Tetractys to Vector Equilibrium.

### Question templates

v1 had 100 unique questions per branch (1000 total). v2 has 144 position-specific question templates, each parameterized with `{domain}`, producing 12 domain-specific questions each (1728 total). Templates are organized by zone: 4 corners + 8 edge midpoints + 32 other edge + 36 near-edge interior + 64 deep interior = 144.

---

## Graph Schema

### Node types

| Type | ID format | Count | Description |
|---|---|---|---|
| `face` | `face.{domain}` | 12 | Axiom-level node representing a philosophical domain |
| `construct` | `{domain}.{x}_{y}` | 1728 | A point on a face's 12×12 grid |
| `nexus` | `nexus.{source}.{target}` | 132 | Directional nexus participation (66 pairs × 2 directions) |
| `gem` | `gem.{source}.{target}` | 132 | Condensed state of a directional nexus interaction |
| `central_gem` | `central_gem` | 1 | Convergence point of all inter-face relations |

Total canonical nodes: 12 + 1728 + 132 + 132 + 1 = 2005

### Edge types

**Structural edges (canonical, auto-generated):**

| Relation | From → To | Count | Symmetric | Description |
|---|---|---|---|---|
| `HAS_CONSTRUCT` | face → construct | 1728 | No | Face contains this construct |
| `PRECEDES` | face → face | 11 | No | Causal ordering chain |
| `SPECTRUM_OPPOSITION` | construct ↔ construct | varies | Yes | Opposed edge positions on the same face |
| `NEXUS_SOURCE` | nexus → face | 132 | No | Source face of a directional nexus |
| `NEXUS_TARGET` | nexus → face | 132 | No | Target face of a directional nexus |
| `CENTRAL_GEM_LINK` | gem → central_gem | 132 | No | Gem contributes to central gem |

**Declared edges (canonical or user-authored):**

| Relation | Semantics | Symmetric | Contradiction pair |
|---|---|---|---|
| `COMPATIBLE_WITH` | Constructs that reinforce each other | Yes | TENSIONS_WITH, EXCLUDES |
| `TENSIONS_WITH` | Constructs that create productive tension | Yes | COMPATIBLE_WITH |
| `REQUIRES` | Construct A presupposes construct B | No | EXCLUDES |
| `EXCLUDES` | Constructs that are mutually incompatible | Yes | COMPATIBLE_WITH, REQUIRES |
| `GENERATES` | Construct A gives rise to construct B | Yes | — |
| `RESOLVES` | Construct A resolves a tension in construct B | Yes | — |

### Edge weights

Each relation type has a default weight used for graph distance computation:

| Relation | Weight | Semantics |
|---|---|---|
| HAS_CONSTRUCT | 0.0 | Structural containment (zero cost) |
| PRECEDES | 0.0 | Ordering (zero cost) |
| COMPATIBLE_WITH | 0.2 | Easy traversal between compatible constructs |
| REQUIRES | 0.1 | Very easy — prerequisite is close |
| GENERATES | 0.3 | Moderate — generative relationship |
| NEXUS_SOURCE / NEXUS_TARGET | 0.4 | Cross-face traversal cost |
| CENTRAL_GEM_LINK | 0.5 | Central convergence cost |
| SPECTRUM_OPPOSITION | 0.6 | Substantial — spectrum poles are far apart |
| TENSIONS_WITH | 0.8 | High — tension means distance |
| EXCLUDES | infinity | Impassable — mutual exclusion |

---

## Pipeline Stages

The pipeline runs as a single forward pass through 8 stages. Each stage reads from and writes to a shared `PipelineState` accumulator.

### Stage 1: Intent Parser

**Input:** Natural language intent string or raw coordinate dict.
**Output:** Partial coordinate — a sparse mapping of face names to (x, y, weight) tuples.

For natural language input: uses the GeometricBridge (pre-computed GloVe-derived artifacts) to project the intent into face-relevance scores and axis positions. Tokenizes the intent, looks up each token's pre-computed face similarity vector (20K vocabulary) and axis projection vector (24 dimensions: 2 per face), applies IDF weighting, and computes weighted averages to produce per-face relevance and per-axis positions. Contextual disambiguation resolves polysemous tokens (e.g., "state" in a physics context maps to Ontology, not political science). N-gram phrase matching handles multi-word concepts. Phase-aware weighting adjusts face relevance based on Comprehension/Evaluation/Application phase similarity to the intent. Question position matching boosts faces where the intent's vocabulary aligns with specific grid-position questions.

For coordinate input: validates and passes through directly.

### Stage 2: Coordinate Resolver

**Input:** Partial coordinate (may have gaps — not all 12 faces populated).
**Output:** Full coordinate — all 12 faces populated with (x, y, weight).

Uses constraint satisfaction to fill gaps. Arc consistency propagates constraints from populated faces to empty ones via declared edges (REQUIRES, GENERATES, COMPATIBLE_WITH). Candidate positions are scored by compatibility with already-resolved faces. Gap-filling uses the PRECEDES chain to propagate from neighboring faces.

### Stage 3: Position Computer

**Input:** Full coordinate.
**Output:** Manifold position — spectral embedding centroid plus per-face positions.

Looks up each face's (x, y) in the spectral embedding cache (Laplacian eigendecomposition of the full graph). Computes the weighted centroid across all 12 face positions. The manifold position places the intent in continuous embedding space.

### Stage 4: Construct Resolver

**Input:** Full coordinate.
**Output:** Active constructs per face — the specific grid points activated by the coordinate, with classification and potency.

For each face, identifies the construct at the coordinate's (x, y) position. Assigns classification (corner, edge_midpoint, other_edge, near_edge_interior, deep_interior) and potency (position-derived weight). Returns the 12 active constructs along with their epistemic questions, tags, and positional metadata.

### Stage 5: Tension Analyzer

**Input:** Active constructs, full coordinate.
**Output:** Tensions — potency-weighted tension scores between active constructs.

Three tension sources:

1. **Direct tensions**: Declared TENSIONS_WITH edges between active constructs.
2. **Spectrum tensions**: Active constructs that sit at spectrum-opposed positions on the same face.
3. **Positional tensions**: Via positional correspondence — when active constructs on different faces occupy opposed positions (high constitutive on one, low on another), the polarity convention creates natural tension. Computed from coordinates, not from edges.

Tensions are weighted by both constructs' potency values. Higher-potency constructs (edge/corner positions) produce stronger tensions.

### Stage 6: Nexus/Gem Analyzer

**Input:** Active constructs, full coordinate.
**Output:** Nexus details and gem values for all relevant face pairs.

For each pair of faces that have active constructs: computes the nexus interaction using both faces' active constructs, their potency, and the nexus stratification (paired/adjacent/opposite). Paired nexi produce gems with complementary resonance character. Adjacent and opposite nexi produce gems with varying degrees of tension and affinity.

Gem magnitude is computed from the potency-weighted interaction of the two faces' active positions. Nexus stratification modulates the magnitude: paired nexi amplify (resonance), adjacent nexi pass through, opposite nexi attenuate.

### Stage 7: Spoke Analyzer

**Input:** Gems, nexus details.
**Output:** Per-face spoke profiles and central gem.

For each face, aggregates its 11 gem values into a spoke — a 4-property behavioral signature:

| Property | What it measures |
|---|---|
| Strength | Total outward engagement magnitude |
| Consistency | Variance across the face's 11 gem values (low variance = consistent) |
| Polarity | Whether the face's outward engagement is predominantly resonant or tense |
| Contribution | This face's share of the total system engagement |

The central gem is computed from the convergence of all 12 spokes — the aggregate state when every face's outward profile is held together.

### Stage 8: Construction Bridge

**Input:** All accumulated pipeline state.
**Output:** Construction basis — the full output returned to the client.

Assembles the final output:
* **Coordinate**: The fully resolved 12-face coordinate
* **Active constructs**: Per-face construct with question, classification, potency, sub-dimensional interpretation
* **Tensions**: Ranked list with resolution paths
* **Gems**: Per-nexus interaction summaries
* **Spokes**: Per-face behavioral signatures
* **Central gem**: System-wide coherence measure
* **Construction questions**: The domain-specific questions at each active position, for the client to use in prompt construction
* **Harmonization pairs**: For each of the 6 complementary pairs, the correspondence between the active construct on the theoretical face and its counterpart on the applied face

---

## Semantic Bridge (Intent Parser Backend)

The GeometricBridge provides Stage 1 with pre-computed semantic artifacts derived from GloVe 6B 100d embeddings. This replaces the earlier keyword+TF-IDF approach with geometry-integral parsing that understands face relevance and axis positions from word meaning rather than keyword overlap.

### Artifacts (pre-computed at build time)

| Artifact | Shape | Content |
|---|---|---|
| Face similarity | 20K × 12 | Per-word relevance to each of the 12 faces |
| Axis projections | 20K × 24 | Per-word position on each face's 2 axes (x, y) |
| IDF weights | 20K × 1 | Inverse document frequency for vocabulary weighting |
| Phase similarity | 20K × 3 | Per-word relevance to Comprehension/Evaluation/Application phases |
| Question position map | per-face | Mapping from vocabulary to specific grid positions via question templates |
| Disambiguation table | 15 entries | Context-dependent sense resolution (trigger word → context tokens → face/axis override) |
| N-gram phrases | 92 entries | Multi-word concept embeddings (e.g., "moral obligation", "causal inference") |

### Build process

1. Load GloVe 6B 100d vectors (400K vocabulary, 100 dimensions)
2. Compute face centroids from authored sub-dimension pole labels (e.g., "particular", "universal" for Ontology x-axis)
3. Expand pole vocabulary via 46 synonym clusters (curated per pole)
4. Compute axis direction vectors (high-pole centroid minus low-pole centroid per axis per face)
5. Score all vocabulary words against face centroids using discriminative scoring (affinity to target face minus mean affinity to other faces)
6. Project vocabulary onto axis direction vectors for axis position estimates
7. Expand vocabulary via question template tokens (15K base → 20K with question-guided expansion)
8. Serialize artifacts to `src/advanced_prompting_engine/data/` as compressed numpy arrays

### Runtime (numpy-only)

1. Tokenize intent, apply contextual disambiguation
2. Match n-gram phrases, replace matched spans with phrase embeddings
3. Look up each token's face similarity and axis projection vectors
4. Apply IDF weighting and phase-aware face adjustment
5. Compute weighted average face scores and axis positions
6. Apply question position matching bonus
7. Emit partial coordinate with face weights and (x, y) positions

### Focused Output Mode and Synthesis Layer

Stage 8 (Construction Bridge) includes a synthesis layer that produces a guidance section: dominant dimensions, gap analysis, resonance patterns, and a concise summary. The `interpret_basis` tool and the `focused` output mode return this compact synthesis (~3KB) instead of the full construction basis (~695KB), suitable for direct client consumption.

---

## Mathematical Operations

All mathematical operations live in the `math/` module. No pipeline stage or cache performs raw computation directly.

| Module | Operations | Used by |
|---|---|---|
| `embedding.py` | Spectral embedding via Laplacian eigendecomposition (numpy only) | Embedding Cache, Stage 3 |
| `tfidf.py` | TF-IDF vectorization and cosine similarity (numpy only) | TF-IDF Cache, Stage 1 |
| `distance.py` | Graph distance metrics (weighted shortest path, coordinate distance) | Stages 2, 5 |
| `csp.py` | Constraint satisfaction (arc consistency, candidate scoring) | Stage 2 |
| `tension.py` | Potency-weighted tension propagation (direct, spectrum, positional) | Stage 5 |
| `gem.py` | Gem magnitude computation with nexus stratification modulation | Stage 6 |
| `spoke.py` | Spoke shape computation (strength, consistency, polarity, contribution) | Stage 7 |
| `community.py` | Community detection (Louvain wrapper) | Orchestrator |
| `centrality.py` | Centrality measures (betweenness, PageRank) | Centrality Cache |
| `optimization.py` | Pareto front computation | Orchestrator |

---

## Canonical Content

The engine ships with canonical (read-only) content that is generated at first run and never modified.

### Faces (12 nodes)

The 12 philosophical domains with core questions, sub-dimensions, construction templates, and domain replacement strings. Organized in three phases:

* **Comprehension** (5): Ontology, Epistemology, Axiology, Teleology, Phenomenology
* **Evaluation** (2): Ethics, Aesthetics
* **Application** (5): Praxeology, Methodology, Semiotics, Hermeneutics, Heuristics

Connected by 11 PRECEDES edges forming the causal chain.

### Constructs (1728 nodes)

One construct per grid position per face (144 positions × 12 faces). Each construct carries:

* **Question**: Domain-specific question from the 144 parameterized templates
* **Tags**: Derived from the question text via stop-word removal and stemming
* **Classification**: corner, edge_midpoint, other_edge, near_edge_interior, deep_interior
* **Potency**: Position-derived weight (corners highest, deep interior lowest)

Connected to their face via HAS_CONSTRUCT edges. Connected to spectrum-opposed constructs via SPECTRUM_OPPOSITION edges.

### Question templates (144)

Position-specific templates organized by zone:

| Zone | Template count | Positions |
|---|---|---|
| Corners | 4 | (0,0), (11,0), (0,11), (11,11) |
| Edge midpoints | 8 | (5,0), (6,0), (5,11), (6,11), (0,5), (0,6), (11,5), (11,6) |
| Other edge | 32 | Remaining perimeter positions |
| Near-edge interior | 36 | At least one coordinate is 1 or 10 |
| Deep interior | 64 | Both coordinates in range 2–9 |

Each template contains `{domain}` which is replaced with the face's domain replacement string to produce the final construct question.

### Nexi (132 directional nodes)

One directional nexus node for each ordered pair of faces. Stratified by cube model relationship:

* 6 paired nexus pairs (12 directional) — complementary counterparts
* 48 adjacent nexus pairs (96 directional) — neighboring concerns
* 12 opposite nexus pairs (24 directional) — distant concerns

### Gems (132 nodes)

One gem per directional nexus participation. Connected to the central gem via CENTRAL_GEM_LINK edges.

### Central gem (1 node)

The convergence point of all inter-face relations.

### Cube pairing metadata

The 6 complementary pairs and their cube face assignments are stored as face-level attributes, enabling the harmonization computation in Stage 8.

---

## Canonical Data Protection

Canonical data is protected at the SQLite level:

* Canonical tables have INSERT/UPDATE/DELETE triggers that raise errors after initialization
* User extensions go into separate user tables with provenance tagging
* The NetworkX graph merges both canonical and user data at load time
* User data can never shadow or modify canonical nodes/edges — only extend

---

## Startup Sequence

1. Open or create SQLite database
2. Create tables if needed
3. Check if canonical data needs initialization
4. If first run: generate all canonical nodes and edges, persist to SQLite
5. Load all canonical + user data into NetworkX graph
6. Initialize embedding cache (spectral decomposition)
7. Initialize TF-IDF cache (vectorize all 1728 construct questions)
8. Initialize centrality cache (betweenness + PageRank)
9. Create Graph Query and Mutation layers
10. Create Pipeline Runner
11. Register MCP tools, resources, prompts
12. Begin accepting requests via stdio

---

## Project Structure

```
advanced-prompting-engine/
├── CLAUDE.md
├── docs/
│   ├── DESIGN.md                              # This document
│   ├── CONSTRUCT-v2.md                        # Standalone Construct specification
│   ├── CONSTRUCT-v2-questions.md              # 144 parameterized question templates
│   ├── GEOMETRY-NOTES.md                      # Latent geometric properties
│   ├── specs/
│   │   └── semantic-bridge-algorithms.md      # Algorithm specifications for GeometricBridge
│   └── adr/                                   # Architecture Decision Records
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
│       │   ├── grid.py                        # Grid structure — classification, potency, spectrum generation
│       │   └── schema.py                      # Schema definitions, node/edge types, face definitions
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── embedding.py                   # Spectral embedding cache (lifecycle-managed)
│       │   ├── tfidf.py                       # TF-IDF vector cache (1728 questions, lifecycle-managed)
│       │   └── centrality.py                  # Centrality cache (betweenness, PageRank)
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── runner.py                      # Pipeline orchestration — runs stages 1-8 in sequence
│       │   ├── intent_parser.py               # Stage 1: NL → raw partial coordinate
│       │   ├── coordinate_resolver.py         # Stage 2: CSP, constraint propagation, gap-filling
│       │   ├── position_computer.py           # Stage 3: spectral embedding lookup, centroid
│       │   ├── construct_resolver.py          # Stage 4: active constructs per face
│       │   ├── tension_analyzer.py            # Stage 5: potency-weighted tension + spectrum oppositions
│       │   ├── nexus_gem_analyzer.py          # Stage 6: nexus integration, gem computation
│       │   ├── spoke_analyzer.py              # Stage 7: spoke behavioral signatures, central gem
│       │   └── construction_bridge.py         # Stage 8: construction questions + full output assembly
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   └── multi_pass.py                  # stress_test, triangulate, deepen
│       ├── math/
│       │   ├── __init__.py
│       │   ├── distance.py                    # Graph distance metrics
│       │   ├── embedding.py                   # Spectral embedding (Laplacian, eigendecomposition)
│       │   ├── csp.py                         # Constraint satisfaction
│       │   ├── tension.py                     # Potency-weighted tension propagation
│       │   ├── community.py                   # Community detection
│       │   ├── centrality.py                  # Centrality measures
│       │   ├── tfidf.py                       # TF-IDF implementation (numpy only)
│       │   ├── spoke.py                       # Spoke shape computation
│       │   ├── gem.py                         # Gem magnitude computation
│       │   └── optimization.py                # Pareto front computation
│       ├── data/                               # Pre-computed semantic bridge artifacts (GloVe-derived)
│       └── tools/
│           ├── __init__.py
│           ├── create_prompt_basis.py         # Primary tool — invokes pipeline
│           ├── explore_space.py               # Expert tool — delegates to query layer + orchestrator
│           ├── extend_schema.py               # Authoring tool — delegates to mutation layer
│           └── interpret_basis.py             # Interpretation tool — focused output from construction basis
├── tests/
│   ├── __init__.py
│   ├── test_pipeline/                         # Per-stage unit tests (8 stages)
│   ├── test_math/                             # Mathematical operation tests
│   ├── test_graph/                            # Graph query/mutation/grid tests
│   └── test_tools/                            # MCP tool integration tests
├── scripts/
│   ├── build_semantic_bridge.py               # Build script for GloVe-derived artifacts
│   └── benchmark_8texts.py                    # Literary text benchmark (8 canonical texts, 20 assertions)
├── pyproject.toml
└── README.md
```

---

## Conventions

- Each class in its own file
- Pipeline stages are internal — never exposed as MCP tools
- All graph access goes through Graph Query Layer or Graph Mutation Layer — no direct NetworkX calls elsewhere
- Canonical graph data is read-only at the DB level (SQLite triggers)
- Canonical node IDs are permanent across versions (format: `{domain}.{x}_{y}` for constructs, `nexus.{source}.{target}` for nexi)
- User extensions use provenance tagging, never modify canonical tables
- Caches (embedding, TF-IDF, centrality) are lifecycle-managed: computed at startup, invalidated on graph mutation, recomputed lazily
- Mathematical operations live in `math/` module, imported by pipeline stages and caches
- Grid structure logic (classification, potency derivation, spectrum generation) lives in `graph/grid.py`
- Nexus, gem, and spoke computations are separate math modules (`math/gem.py`, `math/spoke.py`)
- Potency weighting is applied in tension, gem, and spoke computations — never ignored
- Contradiction detection lives in Graph Mutation Layer, not in individual tools
- The Construct specification (`CONSTRUCT-v2.md`) is the source of truth for what faces, points, spectrums, nexi, gems, spokes, and the central gem ARE — use engine-specific language only in engine code, not in the Construct spec
- "Face" terminology replaces "branch" throughout the codebase. Schema constants and API parameters use `face` (not `branch`)
- Positional correspondence is computed from coordinates at query time, not stored as graph edges
- Nexus stratification (paired/adjacent/opposite) modulates gem computation and tension weighting
