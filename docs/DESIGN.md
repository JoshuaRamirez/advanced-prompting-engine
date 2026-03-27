# Universal Prompt Creation Engine — Design Specification

## Overview

A universal prompt creation engine delivered as an MCP (Model Context Protocol) server. The engine provides a 10-dimensional philosophical manifold — grounded in a Construct of 10 planes, each a 10x10 grid of epistemic observation points — that any client can use to derive a principled construction basis for prompt creation.

The engine does not generate prompts. It measures a client's intent across 10 philosophical axes and returns a precise, dimensionally-situated construction basis from which the client constructs.

The Construct specification is defined in `CONSTRUCT.md`. The mapping of Construct elements to engine components is defined in `CONSTRUCT-INTEGRATION.md`.

## Analog

The engine operates like a **spectrometer**. A spectrometer takes a sample, measures it across multiple spectral bands simultaneously, and returns a spectral signature. The chemist uses that signature to synthesize a compound. The instrument does not synthesize — the chemist does. The instrument provides the measurement that makes principled synthesis possible.

| Spectrometry | This Engine |
|---|---|
| The sample | The client's intent |
| The 10 spectral bands | The 10 philosophical branches (planes) |
| The spectral signature | The coordinate — a precise, reproducible grid position per branch |
| Absorption peaks | Active constructs — what the sample registers strongly on |
| Spectral interference | Tensions — geometric spectrum oppositions and declared conflicts |
| Harmonic resonance | Generative combinations — constructs that amplify each other |
| Nexus interactions | How different spectral bands influence each other |
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

### Deployment Topology

Single Python process. No external service dependencies. No daemon. No port. No network listener.

```
┌─────────────────────────────────────┐
│  Single Python process              │
│  ├── NetworkX (in-process compute)  │
│  ├── numpy (in-process math)        │
│  ├── SQLite (in-process, one file)  │
│  └── MCP SDK (stdin/stdout)         │
└─────────────────────────────────────┘
         ↕ stdio (JSON-RPC)
┌─────────────────────────────────────┐
│  MCP Client (any)                   │
└─────────────────────────────────────┘
```

---

## The 3-Level Schema

The graph has an internal meta-structure. Each level is a schema for the level below it.

### Level 1 — Axiom Layer

The philosophical axes. Immutable. Universal. Each defines a core question that every prompt must answer implicitly or explicitly. These are the laws of the space itself — not what things exist, but what kinds of things can exist.

Each axiom branch corresponds to one **plane** in the Construct (see `CONSTRUCT.md`).

The 10 axiom branches:

#### 1. Epistemology (Knowledge, Belief, Justification)
- **Core Question**: How do we know domain states, events, and conditions are true or justified?
- **Content**: Foundational principles for establishing truth — criteria for correctness, validation methods, authoritative sources. Mechanisms for knowledge propagation and validation.

#### 2. Teleology (Purpose, Ends, Goal-directedness)
- **Core Question**: What ultimate purposes do each domain, event, or interaction serve?
- **Content**: Intentionality behind interactions and events. Teleological justification for behaviors, communications, and state transitions.

#### 3. Ontology (Being, Existence, Categories of Reality)
- **Core Question**: What entities and relationships fundamentally exist?
- **Content**: Essential entities, structures, boundaries, and hierarchical relationships. The essence of components and their categorical nature.

#### 4. Axiology (Value — Ethical, Aesthetic, Practical)
- **Core Question**: What is the value inherent in each choice?
- **Content**: Value criteria — ethical correctness, system integrity, trust, maintainability. Axiological guidelines for evaluating decisions.

#### 5. Phenomenology (Experience, Consciousness)
- **Core Question**: How are experiences and interactions represented and realized?
- **Content**: Experiential structures, consciousness representation, interaction flow management. How raw input becomes conscious experience without loss of intent.

#### 6. Praxeology (Human Action, Purposeful Behavior)
- **Core Question**: How are actions, behaviors, and intentions structured?
- **Content**: Action-oriented structures and intentional interactions. The praxeological logic underpinning behavior invocation and delegation mechanisms.

#### 7. Methodology (Methods of Inquiry or Practice)
- **Core Question**: What processes and methodologies govern construction and evolution?
- **Content**: Methodologies for designing, constructing, testing, and maintaining components. Workflows, decision-making protocols, and iteration guidelines.

#### 8. Semiotics (Signs, Meaning, Communication)
- **Core Question**: How are signals, events, and data meaningfully communicated?
- **Content**: Communicative mechanisms, signs, and signals. Semantic conventions for signals, payload structures, and consistent interpretation of meaning.

#### 9. Hermeneutics (Interpretation)
- **Core Question**: What frameworks govern interpretation and understanding of events, signals, and gestures?
- **Content**: Interpretative frameworks for events, meanings, and structural updates. How ambiguity and interpretation are managed consistently.

#### 10. Heuristics (Practical Problem-solving Strategies)
- **Core Question**: What practical strategies guide the handling of complexities and challenges?
- **Content**: Heuristic methods for problem-solving, resolution, and managing operational complexities. Adaptive strategies, fallback solutions, and pragmatic approaches.

#### Inter-Branch Ordering

The branches have a causal/logical flow that constrains how Level 2 constructs relate across branches:

```
Ontology          → what exists
    │
Epistemology      → how we know what exists
    │
Axiology          → what's worth knowing/doing
    │
Teleology         → toward what end
    │
Phenomenology     → how it's experienced
    │
Praxeology        → how it's enacted
    │
Methodology       → how practice is systematized
    │
Semiotics         → how meaning is communicated
    │
Hermeneutics      → how meaning is interpreted
    │
Heuristics        → how practice adapts to the unknown
```

This ordering is encoded in the graph as Level 1 PRECEDES edges.

#### Sub-Dimensions per Branch

Each branch has two internal sub-dimensions corresponding to the x and y axes of its Construct grid. These define a 2D field of tension within each branch:

| Branch | x-axis (0 → 9) | y-axis (0 → 9) |
|---|---|---|
| Ontology | Particular → Universal | Static → Dynamic |
| Epistemology | Empirical → Rational | Certain → Provisional |
| Axiology | Intrinsic → Instrumental | Individual → Collective |
| Teleology | Immediate → Ultimate | Intentional → Emergent |
| Phenomenology | Objective → Subjective | Surface → Deep |
| Praxeology | Individual → Coordinated | Reactive → Proactive |
| Methodology | Analytic → Synthetic | Deductive → Inductive |
| Semiotics | Explicit → Implicit | Syntactic → Semantic |
| Hermeneutics | Literal → Figurative | Author-intent → Reader-response |
| Heuristics | Systematic → Intuitive | Conservative → Exploratory |

#### Construction Question Templates

Each axiom branch carries a parameterizable question template as a node property. These are canonical and immutable — authored as part of the Axiom Layer:

| Branch | Template |
|---|---|
| Ontology | What entities and relationships does this prompt assume exist? |
| Epistemology | How does this prompt establish and verify truth? |
| Axiology | What does this prompt value, and by what criteria does it evaluate? |
| Teleology | What outcome is this prompt directed toward? |
| Phenomenology | How is the user's experience represented in this prompt's output? |
| Praxeology | What actions and behaviors does this prompt structure? |
| Methodology | What method of reasoning or inquiry does this prompt employ? |
| Semiotics | How does this prompt signal and encode meaning? |
| Hermeneutics | How should ambiguity and interpretation be handled? |
| Heuristics | What strategies does this prompt use when facing the unknown? |

The Construction Bridge parameterizes these with active constructs, spectrum opposites, tension context, spoke profiles, and generative context at runtime.

### Level 2 — Schema Layer

The observation points that inhabit each branch's 10x10 grid. Each point is a **specific possibility of observation** — a site where potential becomes articulated. See `CONSTRUCT.md` for the full point specification.

Each branch contains exactly **100 constructs** arranged in a 10x10 grid addressed by (x, y) coordinates.

#### Point Classification

| Classification | Positions | Count per branch | Potency |
|---|---|---|---|
| Corner | (0,0), (9,0), (0,9), (9,9) | 4 | 1.0 |
| Midpoint | (4,0), (9,4), (4,9), (0,4) | 4 | 0.95 |
| Edge (remaining) | All other perimeter positions | 28 | 0.85 |
| Center | All interior positions | 64 | 0.5 |

The 36 edge points (corners + midpoints + remaining edge) encapsulate the 64 center points. Edge points define the field boundary; center points exist within it.

The 4 corners are organizational bounds for the 32 non-corner edge points. Corners carry maximum potency as combined extremes of both sub-dimensions.

#### Construct Properties

Properties on a Level 2 node:

| Property | Type | Description |
|---|---|---|
| `id` | string | Unique identifier: `branch.x_y` (e.g., `epistemology.3_0`) |
| `branch` | string | Parent axiom branch |
| `x` | int (0-9) | Grid x-coordinate (position on first sub-dimension) |
| `y` | int (0-9) | Grid y-coordinate (position on second sub-dimension) |
| `classification` | string | `corner`, `midpoint`, `edge`, or `center` |
| `potency` | float | Position-derived: 1.0, 0.95, 0.85, or 0.5 |
| `question` | string | The Construct's epistemic question for this grid position, parameterized by branch |
| `description` | string | Expanded description combining positional role with branch domain |
| `tags` | list[str] | Keywords for TF-IDF intent matching |
| `spectrum_ids` | list[str] | IDs of spectrums this point participates in |
| `provenance` | string | `canonical` or `user` |
| `mutable` | boolean | `false` for canonical constructs |

#### Canonical Content

The 1000 canonical constructs are derived from the Construct specification's 100 positional epistemic questions, parameterized across the 10 branches. See ADR-010.

Each grid position carries a structurally-defined epistemic question. The same structural question at the same position adapts to each branch's philosophical domain:

- Position (0,0) on Ontology: *"What foundational possibility anchors the origin of ontological existence?"*
- Position (0,0) on Epistemology: *"What foundational possibility anchors the origin of epistemological truth?"*

The questions serve triple duty: they are **content** (TF-IDF vectorizable), **structure** (grid-positioned with classification and potency), and **guidance** (epistemic probes that direct prompt construction).

#### Spectrums

Each branch contains **20 spectrums** auto-generated from grid geometry — structured oppositions between pairs of edge points:

- 10 spectrums from diagonal pairings: (0,0)↔(9,9), (0,1)↔(9,8), ..., (0,9)↔(9,0)
- 10 spectrums from cross-diagonal pairings: (1,0)↔(8,9), (2,0)↔(7,9), ..., (8,0)↔(1,9)

Total: **200 spectrums** across all 10 branches. These exist by virtue of grid geometry — no manual authoring required.

### Level 3 — Coordinate Layer

The mathematical structure that allows a client to take a precise, measurable position in the space. Computed on demand from the Schema Layer — never stored.

A coordinate is a 10-dimensional vector of grid positions:

```json
{
  "ontology":       { "x": 0, "y": 0, "weight": 0.0 },
  "epistemology":   { "x": 0, "y": 0, "weight": 0.0 },
  "axiology":       { "x": 0, "y": 0, "weight": 0.0 },
  "teleology":      { "x": 0, "y": 0, "weight": 0.0 },
  "phenomenology":  { "x": 0, "y": 0, "weight": 0.0 },
  "praxeology":     { "x": 0, "y": 0, "weight": 0.0 },
  "methodology":    { "x": 0, "y": 0, "weight": 0.0 },
  "semiotics":      { "x": 0, "y": 0, "weight": 0.0 },
  "hermeneutics":   { "x": 0, "y": 0, "weight": 0.0 },
  "heuristics":     { "x": 0, "y": 0, "weight": 0.0 }
}
```

Each position is an (x, y) grid coordinate. Each `weight` is dimensional emphasis ∈ [0, 1]. The position carries structural information: classification, potency, spectrum membership, sub-dimensional meaning.

The `create_prompt_basis` tool accepts either:
- Natural language intent (mapped to grid positions via TF-IDF colocation)
- A pre-formed coordinate object with (x, y) positions per branch

---

## The Space

The space is the **relationally-constrained manifold of all constructible philosophical positions across the 10 axiom branches, and the engine exists to situate a client within it.**

### What the Space Does

1. **Bounds** — not every combination of positions across 10 grids is constructible. EXCLUDES edges eliminate entire regions. Edge points encapsulate center points — the extremes define the envelope.
2. **Constrains** — within the bounded space, TENSIONS_WITH, SPECTRUM_OPPOSITION, and REQUIRES edges create topography. Some positions are easy to construct from (low tension, high compatibility), others are costly (high tension, requiring resolution). Potency amplifies or dampens these effects.
3. **Generates** — GENERATES edges and cross-community constructs identify positions where combinations produce emergent quality. The space has peaks.
4. **Integrates** — nexi mediate inter-branch interactions, producing gems. Spokes aggregate gems into behavioral signatures. The central gem reflects system-wide coherence.

### Relation Types

| Edge Type | Meaning | Source | Transitivity |
|---|---|---|---|
| `COMPATIBLE_WITH` | Two constructs reinforce each other | Declared | Transitive |
| `TENSIONS_WITH` | Two constructs pull against each other | Declared | Propagates via REQUIRES chains |
| `SPECTRUM_OPPOSITION` | Geometric opposition between edge points | Auto-generated from grid | Symmetric, not transitive |
| `REQUIRES` | One construct demands another be present | Declared | Transitive |
| `EXCLUDES` | Two constructs cannot coexist | Declared | Symmetric, not transitive |
| `GENERATES` | Combination produces emergent quality | Declared | Not transitive |
| `RESOLVES` | One construct mediates a known tension | Declared | Not transitive |
| `PRECEDES` | One construct must be established before another | Declared | Transitive |

Edge properties: `relation_type`, `strength` ∈ [0, 1], `directionality`, `provenance`, `source` (declared or geometric).

---

## Inter-Branch Architecture: Nexi, Gems, Spokes

Cross-branch connections are mediated through a nexus-gem-spoke architecture. See ADR-011 and ADR-012.

### Nexi (90 nodes)

A nexus is a **mediating locus between two branches** — a graph node (not an edge) sitting in the subspace between two branch subgraphs. See `CONSTRUCT.md` for the full nexus specification.

- Each branch connects to each of the other 9 branches via a unique directional nexus
- 10 branches × 9 connections = **90 nexi**
- Each nexus receives the 36 edge-point energies from both connected branches
- Each nexus computes an integration — the harmonic juxtaposition of both sets of extremes
- Each nexus produces a **gem**

Nexus node properties: `id` (`nexus.source_branch.target_branch`), `source_branch`, `target_branch`, `provenance: canonical`.

### Gems (90 values)

A gem is the **condensed state of a nexus interaction** — the product, not the process. See `CONSTRUCT.md`.

- Each nexus produces one gem
- A gem has at minimum a `magnitude` (strength of integration)
- Gems are returned in the construction basis output
- Gems are the entities available for recursive condensation into center points of uninvolved branches

### Spokes (10 profiles)

A spoke is the **complete set of one branch's interactions with all other branches** — a behavioral signature. See ADR-012.

Each spoke contains 9 gems (one from each nexus) plus the shared central gem = 10 gems per spoke.

A spoke's distribution has measurable shape:

| Property | Computation | What it reveals |
|---|---|---|
| **Strength** | `mean(gem_magnitudes)` | Overall magnitude of this branch's interactions |
| **Consistency** | `1 - (std(gem_magnitudes) / max(mean, epsilon))` | Whether interaction quality is uniform or scattered |
| **Polarity** | `tension_flagged_gems / total_gems` | Ratio of conflicting to harmonious interactions |
| **Contribution** | `sum(this_spoke) / sum(all_spokes)` | This branch's share of system-wide coherence |

Spoke classification:

| Condition | Classification |
|---|---|
| High strength + high consistency | **Coherent** |
| High strength + low consistency | **Fragmented** |
| High strength + high contribution | **Dominant** |
| Low strength overall | **Weakly integrated** |

### Central Gem (1 node)

The unified convergence of all nexus interactions. Connected to all 90 nexus nodes. Its value aggregates all 10 spoke contributions into a system-wide coherence score.

The central gem reflects whether the entire coordinate position is harmonious across all 10 branches simultaneously.

### Dual View

The same 90 nexi support two complementary views:

| View | Structure | Unit | Question |
|---|---|---|---|
| **Network** | Fully connected graph | Nexus | What happens between these two branches? |
| **Radial** | 10 spokes converging to center | Spoke | What is the total behavior of this branch across the system? |

Both views are computed and returned in the construction basis.

---

## External Surface

### MCP Tools (3)

| Tool | Purpose | When |
|---|---|---|
| `create_prompt_basis` | Full pipeline — intent in, construction basis out. Accepts natural language or pre-formed coordinate with (x,y) positions. | Primary use. Every time. |
| `explore_space` | Direct graph traversal, neighborhood inspection, path finding, stress testing, triangulation | When the client wants to understand the space itself |
| `extend_schema` | Add constructs, relations with contradiction detection | When the client has domain knowledge to contribute |

### MCP Prompts (4)

| Name | Sequence | Output |
|---|---|---|
| `orient` | Reads axiom_manifest + coordinate_schema + schema_manifest | Client understands the space |
| `build_construction_basis` | build_coordinate → validate → compute | Complete construction foundation |
| `compare_positions` | validate × 2 → compute_distance → triangulate | Dimensional relationship between two intents |
| `resolve_and_construct` | compute_basis → resolve_tensions → get_generative | Construction basis with tensions resolved |

### MCP Resources (3)

| Name | Contents |
|---|---|
| `axiom_manifest` | The Level 1 axiom layer — the 10 branches, core questions, sub-dimensions |
| `schema_manifest` | Current state of Level 2 — all grids, constructs, spectrums, nexi |
| `coordinate_schema` | Formal schema of a valid coordinate object with (x,y) positions |

---

## Internal Architecture

```
EXTERNAL (3 tools + 4 prompts + 3 resources)
┌──────────────────────────────────────────────────────┐
│  create_prompt_basis · explore_space · extend_schema  │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────┴───────────────────────────────────┐
│  Multi-Pass Orchestrator                              │
│  stress_test, triangulate, deepen                     │
├───────────────────────────────────────────────────────┤
│  Pipeline (8 stages — single forward pass)            │
│  Intent Parser → Coordinate Resolver → Position Comp  │
│  → Construct Resolver → Tension Analyzer              │
│  → Nexus/Gem Analyzer → Spoke Analyzer                │
│  → Construction Bridge                                │
├───────────────────────────────────────────────────────┤
│  Graph Query Layer          Graph Mutation Layer       │
│  list, get, find,           add, validate,            │
│  subgraph, path,            contradict check,         │
│  grid, spoke, nexus         grid-position validate    │
├───────────────────────────────────────────────────────┤
│  Embedding Cache            TF-IDF Cache              │
│  spectral, lifecycle-       construct question         │
│  managed, auto-invalidate   vectors, pre-computed     │
├───────────────────────────────────────────────────────┤
│  NetworkX (compute)         SQLite (persist)           │
│  1101 nodes, ~1479 edges    canonical | user tables    │
└───────────────────────────────────────────────────────┘
```

### Graph Query Layer

Internal API that all pipeline operators and external tools use to access graph data. No direct NetworkX access elsewhere in the codebase.

| Method | Returns |
|---|---|
| `list_branches()` | All Level 1 axiom branch nodes |
| `list_constructs(branch, provenance?, classification?)` | Level 2 constructs, filterable by provenance and classification |
| `get_construct(branch, x, y)` | Full construct at grid position with properties and edges |
| `get_construct_by_id(id)` | Full construct by ID (`branch.x_y`) |
| `list_relation_types()` | All valid relation types |
| `get_edges(node, relation_type?)` | Edges from a node, optionally filtered by type |
| `get_spectrum_opposite(branch, x, y)` | The opposite edge point for a given position |
| `get_edge_constructs(branch)` | All 36 edge-classified constructs for a branch |
| `get_nexus(source_branch, target_branch)` | The nexus node between two branches |
| `get_spoke(branch)` | All 9 nexi originating from a branch + central gem |
| `find_path(source, target, weight_fn?)` | Shortest path with optional weight function |
| `find_all_paths(source, target, max_depth?)` | All paths up to depth |
| `get_subgraph(nodes)` | Induced subgraph for a set of nodes |

### Graph Mutation Layer

Internal API for schema authoring with integrity enforcement.

| Method | Behavior |
|---|---|
| `add_construct(branch, x, y, question, tags, description, provenance)` | Validates grid position is valid, checks ID collision, writes to graph and user SQLite table, invalidates caches |
| `add_relation(source, target, relation_type, strength)` | Validates nodes exist, checks for contradictory inverse edges, returns `ContradictionWarning` if found, writes to graph and user SQLite table, invalidates caches |
| `validate_mutation(proposed_change)` | Dry-run validation without write |

Contradiction map:

| Proposed | Contradicts |
|---|---|
| `COMPATIBLE_WITH` | existing `TENSIONS_WITH` between same pair |
| `TENSIONS_WITH` | existing `COMPATIBLE_WITH` between same pair |
| `REQUIRES` | existing `EXCLUDES` between same pair |
| `EXCLUDES` | existing `REQUIRES` between same pair |

### Embedding Cache

Pre-computed spectral embedding of the full graph (including nexus nodes). Lifecycle-managed.

- Computed at server startup via graph Laplacian eigendecomposition (numpy, no scipy)
- Cached in memory as dict of `{node_id: np.ndarray}`
- Graph hash (node count + edge count + edge list checksum) checked before each pipeline run
- Recomputed only when graph has mutated (user added constructs/relations)
- Embedding dimensionality: min(20, n_nodes - 1) non-trivial eigenvectors

```
A = nx.to_numpy_array(G)
L = np.diag(A.sum(axis=1)) - A
eigenvalues, eigenvectors = np.linalg.eigh(L)
embedding[node_i] = eigenvectors[i, 1:k+1]
```

### TF-IDF Cache

Pre-computed TF-IDF vectors for all 1000 construct questions. Used by the Intent Parser for natural language → grid position matching via vector colocation.

- Computed at server startup from all Level 2 construct `question` and `tags` fields
- Implemented directly with numpy (~50 lines) — no scikit-learn dependency
- Cached as matrix of `(1000, vocabulary_size)` float vectors
- Client intent is projected into the same vector space; cosine similarity determines which grid positions activate
- Invalidated and recomputed on graph mutation (same lifecycle as Embedding Cache)

---

## Pipeline Detail

The pipeline has **8 stages** (expanded from 7 to include nexus/gem and spoke analysis).

### Data Flow Trace

```
Stage 0  INPUT           string | coordinate object
            │
Stage 1  Intent Parser   string → Dict[branch, Optional[{x, y, weight, confidence}]]
            │                     partial coordinate (some axes null)
            │
Stage 2  Coord Resolver  partial → Dict[branch, {x, y, weight}]
            │                     complete coordinate (all 10 axes)
            │
Stage 3  Position Comp   grid coord → {centroid: float[], per_branch: {primary, embedding, nearby[]}}
            │                     continuous embedding space
            │
Stage 4  Construct Res   continuous → Dict[branch, List[{x, y, classification, potency, question}]]
            │                     back to discrete, enriched with neighbors
            │
Stage 5  Tension Anal    construct sets → {magnitude, direct[], cascading[], spectrums[], resolutions[]}
            │                     scalar tensions with cascade paths + spectrum oppositions
            │
Stage 6  Nexus/Gem Anal  active constructs → {gems[], nexus_details[]}
            │                     gem values for each active branch-pair nexus
            │
Stage 7  Spoke Analyzer  gems → {spokes[], central_gem}
            │                     behavioral signatures + system coherence
            │
Stage 8  Constr Bridge   all accumulated → full construction basis output
            │
         OUTPUT          construction basis with grid positions, questions, spectrums,
                         gems, spokes, central gem, and 10 parameterized questions
```

### Stage 1 — Intent Parser

Transforms natural language to a raw partial coordinate of grid positions. Two-tier matching against the 1000 predefined epistemic questions:

1. **Tag overlap** (fast, high confidence): Each construct carries `tags[]`. Tokenize input, score overlap per construct per branch.
2. **TF-IDF cosine similarity** (catches synonyms): Pre-computed TF-IDF vectors for all construct questions. Cosine similarity against input vector in shared vector space.

Combined score: `tag_score * 0.6 + tfidf_score * 0.4`

The highest-scoring construct per branch (if above `MATCH_THRESHOLD`) determines the (x, y) position for that branch.

**Weight vs confidence are separate derivations:**
- `confidence` = match quality (combined score)
- `weight` = token emphasis (proportion of matched tokens that matched this branch relative to all matched tokens)

If the input is a pre-formed coordinate object with (x, y) positions, this stage is bypassed entirely.

### Stage 2 — Coordinate Resolver

Fills null axes and validates the partial coordinate via Constraint Satisfaction Problem (CSP):

1. **Exclusion check**: Verify no EXCLUDES edges between specified positions
2. **Requirements check**: Verify all REQUIRES chains from specified positions are satisfied
3. **Candidate generation**: For each null axis, enumerate valid grid positions (no EXCLUDES violations, all REQUIRES satisfied)
4. **Candidate scoring**: COMPATIBLE_WITH count × 1.0 + REQUIRES pull × 2.0 + potency bonus (edge positions score higher)
5. **Tiebreaker**: Betweenness centrality from pre-computed centrality cache
6. **Auto-fill weight**: Base 0.15, ceiling 0.4, scaled by compatibility pull ratio

Output: Complete 10-axis coordinate with (x, y) positions and weights. No nulls. All constraints satisfied.

### Stage 3 — Position Computer

Projects the discrete grid coordinate into continuous embedding space:

1. Look up each construct's pre-computed spectral embedding vector by grid position
2. Compute weighted centroid: `P = Σᵢ wᵢ · embedding(branch.x_y) / Σᵢ wᵢ`
3. Compute distance from centroid to every construct in the graph (including nexus nodes)

Output: Continuous manifold position with per-branch neighborhood distances.

### Stage 4 — Construct Resolver

Determines the full set of active constructs per branch:

1. Primary construct = the coordinate's specified (x, y) position (always active)
2. Nearby constructs in embedding space within activation threshold are also activated
3. Activation threshold is adaptive: 60% of mean nearest-neighbor distance within each branch
4. Each active construct carries its classification, potency, and predefined question

Output: Dict of active construct lists per branch. Each entry includes grid position, classification, potency, and the epistemic question.

### Stage 5 — Tension Analyzer

Computes direct tensions, cascading tensions, and spectrum oppositions:

**Direct**: For every pair of active constructs across all branches, check for TENSIONS_WITH edges. Weight by potency product of the pair.

**Spectrum oppositions**: For every active edge construct, retrieve its geometric opposite. The spectrum opposition is structural — it exists by grid geometry. Report the active question and the opposite question.

**Cascading**: Follow REQUIRES chains outward. At each hop, check for TENSIONS_WITH edges. Apply decay per hop:

```
tension_at_hop_n = direct_tension_strength × potency_product × decay^n
```

Decay factor derived from mean REQUIRES edge strength. Cascade stops when magnitude < 0.05.

**Resolution paths**: For each tension, check for RESOLVES edges.

Output: Total magnitude + direct tensions + spectrum oppositions + cascading tensions + resolution paths.

### Stage 6 — Nexus/Gem Analyzer

Computes inter-branch integration for all active branch pairs:

1. For each pair of branches that have active constructs, locate the nexus node
2. Gather the edge constructs (36 per branch) from both branches
3. Compute the gem magnitude: integration function over both sets of edge energies, weighted by which edge constructs are active vs. inactive
4. Flag the gem as harmonious or conflicting based on the tension state between the two branches

Output: List of gems with magnitudes and harmony flags. List of nexus details (which branches, which edge constructs contributed).

### Stage 7 — Spoke Analyzer

Aggregates nexus results into per-branch behavioral signatures:

1. For each branch, gather its 9 gems (one from each nexus originating at this branch)
2. Compute the 4 spoke shape properties: strength, consistency, polarity, contribution
3. Derive spoke classification from thresholds
4. Aggregate all 10 spoke contributions into the central gem coherence score

Output: 10 spoke profiles + central gem coherence score and classification.

### Stage 8 — Construction Bridge

Transforms all accumulated analysis into the construction basis output:

1. For each of the 10 axiom branches:
   - Look up the construction question template
   - Attach the active construct's predefined epistemic question
   - Attach the spectrum opposite's predefined question
   - Attach the spoke profile for this branch
   - If tensions touch this branch, attach tension context
   - If generative combinations touch this branch, attach generative context
2. Attach the central gem coherence score
3. Assemble the full output

Output: The final `create_prompt_basis` response.

---

## Multi-Pass Orchestrator

Operations that invoke the pipeline multiple times. These live above the pipeline, not inside it. Accessed via `explore_space` tool or MCP prompt workflows.

### stress_test(coordinate)

Perturbs each axis to nearby grid positions. Runs the pipeline for each perturbation. Compares tension deltas, spoke shape changes, and central gem shifts against the baseline.

Returns: baseline + breakpoints + improvements + spoke stability analysis.

### triangulate(coordinate_a, coordinate_b)

Runs the pipeline twice. Computes intersection of active constructs, shared tensions, spoke profile comparison, and coordinate distance.

### deepen(construction_basis)

Recursive gem condensation:

1. Takes a completed construction basis
2. Selects gems for condensation
3. Projects each gem into a center-point position on an uninvolved branch
4. Runs the pipeline again with the modified coordinate
5. Returns the deeper construction basis

Each pass produces a construction basis at a deeper level of philosophical integration.

---

## Mathematical Operations

### Vector Construction (Intent Parser)

```
C = [(x₁, y₁, w₁), (x₂, y₂, w₂), ..., (x₁₀, y₁₀, w₁₀)]
where (xᵢ, yᵢ) ∈ {0..9} × {0..9}
and   wᵢ ∈ [0, 1]
```

### TF-IDF Matching (Intent Parser)

The 1000 predefined questions are vectorized into TF-IDF space. The client's intent is projected into the same space. Cosine similarity determines colocation:

```
TF(term, doc) = count(term in doc) / len(doc)
IDF(term) = log(N / docs_containing(term))
similarity = dot(tfidf_intent, tfidf_construct) / (norm(a) * norm(b))
```

### Constraint Propagation (Coordinate Resolver)

Boolean constraint satisfaction with potency-weighted scoring:

```
For each unspecified axis i:
  Candidates(i) = {(x,y) ∈ grid(branch_i) |
    ∀ specified (xⱼ,yⱼ): ¬EXCLUDES((x,y), (xⱼ,yⱼ))
    ∧ all REQUIRES chains satisfied
  }
  Score(x,y) = COMPATIBLE_count × 1.0 + REQUIRES_count × 2.0 + potency(x,y) × 0.5
```

### Graph Distance Metric (Position Computer)

Weighted path distance:

```
d_rel(a, b) = min Σ edge_weight(eᵢ) along all paths from a to b

where edge_weight:
  COMPATIBLE_WITH     = 0.2
  TENSIONS_WITH       = 0.8
  SPECTRUM_OPPOSITION = 0.6
  REQUIRES            = 0.1
  EXCLUDES            = ∞
```

Coordinate distance:

```
D(C₁, C₂) = Σᵢ wᵢ · d_rel(C₁.(xᵢ,yᵢ), C₂.(xᵢ,yᵢ))
```

### Spectral Embedding (Position Computer)

Graph Laplacian eigendecomposition over the full graph (1101 nodes including nexus nodes):

```
A = nx.to_numpy_array(G)
L = np.diag(A.sum(axis=1)) - A
eigenvalues, eigenvectors = np.linalg.eigh(L)
k = min(20, n - 1)
embedding[node_i] = eigenvectors[i, 1:k+1]
```

### Potency-Weighted Tension (Tension Analyzer)

```
T_direct(C) = Σ strength(e) × potency(a) × potency(b)
              for all TENSIONS_WITH edges between active constructs a, b

T_spectrum(C) = Σ 0.6 × potency(active) × potency(opposite)
                for all SPECTRUM_OPPOSITION pairs where one endpoint is active

T_cascade(C) = Σ strength(e) × potency_product × decay^(hops)

T(C) = T_direct(C) + T_spectrum(C) + T_cascade(C)
```

### Gem Magnitude (Nexus/Gem Analyzer)

```
gem(A→B) = f(edge_energies_A, edge_energies_B, active_constructs)
```

The gem computation integrates the 36 edge-point potencies from both branches, weighted by which edge constructs are currently active in the coordinate. The specific integration function is an open design item (see ADR-011 consequences).

### Spoke Shape (Spoke Analyzer)

```
strength(spoke)     = mean(gem_magnitudes)
consistency(spoke)  = 1 - std(gem_magnitudes) / max(mean(gem_magnitudes), ε)
polarity(spoke)     = tension_flagged_count / 9
contribution(spoke) = sum(spoke_gems) / sum(all_gems)
```

### Central Gem Coherence

```
coherence = weighted_mean(spoke_contributions)
          = Σ spoke_contribution × spoke_consistency / 10
```

### Community Detection (Generative Analyzer within Construct Resolver)

Louvain modularity optimization (pure Python in NetworkX 2.8+):

```
Q = (1/2m) Σᵢⱼ [Aᵢⱼ - (kᵢkⱼ/2m)] · δ(cᵢ, cⱼ)
```

### Centrality Analysis

Betweenness centrality for bridge constructs. PageRank for influence hubs. Both native NetworkX.

### Transitive Closure

```
TC(R) = R ∪ R² ∪ R³ ∪ ... ∪ Rⁿ
```

Applied to COMPATIBLE_WITH and REQUIRES edges.

### Pareto Optimization (Multi-Pass Orchestrator)

```
Minimize: T(C)
Maximize: |generative_edges(C)|
Subject to: verify_compatibility(C) = True
```

---

## Data Integrity

### Canonical vs User Data

Data is separated at the persistence layer and merged at query time.

```
SQLite:
  canonical_nodes    (read-only, enforced by DB trigger)
    — 10 branch nodes
    — 1000 construct nodes (10 branches × 100 grid positions)
    — 90 nexus nodes
    — 1 central gem node
  canonical_edges    (read-only, enforced by DB trigger)
    — 1000 HAS_CONSTRUCT edges
    — 9 PRECEDES edges
    — 200 SPECTRUM_OPPOSITION edges
    — 90 NEXUS_SOURCE edges
    — 90 NEXUS_TARGET edges
    — 90 CENTRAL_GEM_LINK edges
  user_nodes         (read-write)
  user_edges         (read-write, FK → canonical OR user nodes)
```

### Integrity Rules

| Rule | Enforcement |
|---|---|
| Canonical nodes cannot be modified or deleted | `mutable: False`, DB-level write protection |
| User nodes can connect to canonical nodes freely | Cross-provenance edges are valid |
| Canonical edges cannot be removed | Provenance check on edge deletion |
| User can add edges between canonical nodes | Cross-provenance edges are legitimate |
| Contradiction detection at authoring time | Inverse relation check via Graph Mutation Layer |
| Version stability | Canonical node IDs are permanent across versions (`branch.x_y`) |

### Version Migration

On server startup after upgrade:
1. Version manifest compares user edge references against new canonical IDs
2. Orphaned edges are flagged, not deleted
3. User decides remap or removal

### Provenance-Scoped Queries

Every operation supports a `provenance` filter:
- `canonical` — shipped graph only
- `user` — user extensions only
- `merged` (default) — full combined space

---

## Enrichment Use Cases

### Enrichment Modes

| Mode | Nature | Trigger |
|---|---|---|
| **Intentional** | Client arrives with domain knowledge to add | Deliberate extension before use |
| **Reactive** | Gap discovered during active use | Intent Parser returns low-confidence matches |
| **Corrective** | Contradiction or inconsistency surfaces | Graph Mutation Layer returns ContradictionWarning |
| **Reconciliatory** | Version upgrade breaks references | Migration check flags orphaned edges |

### Contradiction Resolution

When a user adds an edge that contradicts a canonical edge:
1. Graph Mutation Layer detects the contradiction
2. Returns `ContradictionWarning` with existing canonical edge and proposed user edge
3. User chooses: cancel, override with reason, or add a resolution path
4. If override: edge written with `contradicts_canonical: True` flag
5. If resolution path: new construct created that RESOLVES the tension

---

## Construction Output

The `create_prompt_basis` tool returns:

```json
{
  "coordinate": {
    "ontology":       { "x": 0, "y": 0, "weight": 0.0 },
    "epistemology":   { "x": 0, "y": 0, "weight": 0.0 },
    "axiology":       { "x": 0, "y": 0, "weight": 0.0 },
    "teleology":      { "x": 0, "y": 0, "weight": 0.0 },
    "phenomenology":  { "x": 0, "y": 0, "weight": 0.0 },
    "praxeology":     { "x": 0, "y": 0, "weight": 0.0 },
    "methodology":    { "x": 0, "y": 0, "weight": 0.0 },
    "semiotics":      { "x": 0, "y": 0, "weight": 0.0 },
    "hermeneutics":   { "x": 0, "y": 0, "weight": 0.0 },
    "heuristics":     { "x": 0, "y": 0, "weight": 0.0 }
  },
  "active_constructs": {
    "epistemology": [
      {
        "position": [3, 0],
        "classification": "edge",
        "potency": 0.85,
        "question": "What initiating polarity lies within..."
      }
    ]
  },
  "spectrum_opposites": [
    {
      "branch": "epistemology",
      "active": { "position": [3, 0], "question": "..." },
      "opposite": { "position": [6, 9], "question": "..." }
    }
  ],
  "structural_profile": {
    "edge_count": 0,
    "center_count": 0,
    "edge_ratio": 0.0,
    "mean_potency": 0.0
  },
  "tensions": [
    {
      "between": ["branch.x_y", "branch.x_y"],
      "magnitude": 0.0,
      "type": "declared | spectrum_geometric | inferred_cascade",
      "potency_product": 0.0,
      "resolution_paths": []
    }
  ],
  "generative_combinations": [
    {
      "constructs": ["branch.x_y", "branch.x_y"],
      "source": "declared | community_detected"
    }
  ],
  "gems": [
    {
      "nexus": "nexus.epistemology.methodology",
      "magnitude": 0.0,
      "type": "harmonious | conflicting"
    }
  ],
  "spokes": {
    "epistemology": {
      "strength": 0.0,
      "consistency": 0.0,
      "polarity": 0.0,
      "contribution": 0.0,
      "classification": "coherent | fragmented | dominant | weakly_integrated",
      "gems": []
    }
  },
  "central_gem": {
    "coherence": 0.0,
    "classification": "..."
  },
  "construction_questions": {
    "epistemology": {
      "template": "How does this prompt establish and verify truth?",
      "active_question": "What initiating polarity lies within...",
      "opposite_question": "What reversal of directional...",
      "classification": "edge",
      "potency": 0.85,
      "spoke_profile": "coherent",
      "spoke_strength": 0.0
    }
  }
}
```

The construction questions are the **bridge** between dimensional analysis and prompt construction. Each entry includes the branch template, the active construct's predefined epistemic question, the spectrum opposite's question, the position's classification and potency, and the spoke profile for that branch. The client reads these and constructs a prompt informed by the dimensional foundation.

---

## Performance Characteristics

| Operation | Expected scale | Expected time |
|---|---|---|
| Spectral embedding (startup) | 1101 nodes, ~1101×1101 matrix | ~50ms |
| TF-IDF pre-computation (startup) | 1000 construct questions | ~30ms |
| Community detection | 1101 nodes | ~10ms |
| CSP coordinate resolution | 10 branches × 100 grid positions | ~2ms |
| Nexus/gem computation | 90 nexi | ~5ms |
| Spoke computation | 10 spokes × 4 properties | ~1ms |
| Single pipeline run | All 8 stages | ~100-150ms |
| Stress test (multi-pass) | ~100 pipeline runs | ~10-15s |
| Memory footprint | Graph + embeddings + TF-IDF vectors | < 75MB |

### Shipped Graph Size

| Node type | Count |
|---|---|
| Axiom branch nodes | 10 |
| Construct nodes | 1000 |
| Nexus nodes | 90 |
| Central gem node | 1 |
| **Total** | **1101** |

| Edge type | Count |
|---|---|
| HAS_CONSTRUCT | 1000 |
| PRECEDES | 9 |
| SPECTRUM_OPPOSITION | 200 |
| NEXUS_SOURCE | 90 |
| NEXUS_TARGET | 90 |
| CENTRAL_GEM_LINK | 90 |
| **Total** | **~1479** |
