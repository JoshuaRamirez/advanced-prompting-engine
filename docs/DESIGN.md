# Universal Prompt Creation Engine — Design Specification

## Overview

A universal prompt creation engine delivered as an MCP (Model Context Protocol) server. The engine provides a 10-dimensional philosophical manifold — grounded in classical branches of philosophy — that any client can use to derive a principled construction basis for prompt creation.

The engine does not generate prompts. It measures a client's intent across 10 philosophical axes and returns a precise, dimensionally-situated construction basis from which the client constructs.

## Analog

The engine operates like a **spectrometer**. A spectrometer takes a sample, measures it across multiple spectral bands simultaneously, and returns a spectral signature. The chemist uses that signature to synthesize a compound. The instrument does not synthesize — the chemist does. The instrument provides the measurement that makes principled synthesis possible.

| Spectrometry | This Engine |
|---|---|
| The sample | The client's intent |
| The 10 spectral bands | The 10 philosophical branches |
| The spectral signature | The coordinate — a precise, reproducible reading |
| Absorption peaks | Active constructs — what the sample registers strongly on |
| Spectral interference | Tensions — bands that conflict at this sample's signature |
| Harmonic resonance | Generative combinations — bands that amplify each other |
| The chemist | The client — uses the signature to construct |
| The compound synthesized | The prompt |

---

## Technology Stack

| Component | Technology | Role |
|---|---|---|
| Language | Python 3.10+ | Runtime |
| Graph engine | NetworkX (pure Python, in-memory) | First-class graph algorithms, traversal, community detection, centrality, embedding |
| Linear algebra | numpy | Spectral embedding, distance computation, TF-IDF vectors |
| Persistence | SQLite (Python stdlib) | Durable storage, canonical/user data separation, ACID transactions |
| Protocol | MCP SDK (Python) | JSON-RPC over stdio, tool/resource/prompt exposure |
| Distribution | PyPI via `uvx` | Zero-config activation for MCP clients |

### Installable Dependencies

```
networkx    # graph engine — pure Python
numpy       # linear algebra — eigendecomposition, vectors, distances
mcp         # MCP protocol SDK
```

sqlite3 is in Python stdlib. scipy and scikit-learn are intentionally excluded — all needed operations (TF-IDF, Laplacian computation, cosine similarity) are implemented directly with numpy. See ADR-005.

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

The Construction Bridge parameterizes these with active constructs, tension context, and generative context at runtime.

### Level 2 — Schema Layer

The named constructs that inhabit the axiom branches. The declared contents of the dimensional space. Each construct occupies a position on its parent branch's axis.

- Canonical constructs ship with the engine (immutable, provenance: canonical)
- User constructs are added by clients (mutable, provenance: user)

Properties on a Level 2 node:
- `name`: unique identifier (namespaced: `branch.construct_name`)
- `branch`: parent axiom branch
- `description`: what this construct represents
- `tags`: list of keywords for intent matching
- `provenance`: `canonical` or `user`
- `mutable`: boolean (false for canonical)

### Level 3 — Coordinate Layer

The mathematical structure that allows a client to take a precise, measurable position in the space. Computed on demand from the Schema Layer — never stored.

A coordinate is a 10-dimensional vector:

```json
{
  "ontology":       { "position": "construct_name", "weight": 0.0 },
  "epistemology":   { "position": "construct_name", "weight": 0.0 },
  "axiology":       { "position": "construct_name", "weight": 0.0 },
  "teleology":      { "position": "construct_name", "weight": 0.0 },
  "phenomenology":  { "position": "construct_name", "weight": 0.0 },
  "praxeology":     { "position": "construct_name", "weight": 0.0 },
  "methodology":    { "position": "construct_name", "weight": 0.0 },
  "semiotics":      { "position": "construct_name", "weight": 0.0 },
  "hermeneutics":   { "position": "construct_name", "weight": 0.0 },
  "heuristics":     { "position": "construct_name", "weight": 0.0 }
}
```

Each `position` is a Level 2 construct name. Each `weight` is dimensional emphasis ∈ [0, 1].

The `create_prompt_basis` tool accepts either:
- Natural language intent (parsed by Intent Parser)
- A pre-formed coordinate object (bypasses Intent Parser)

---

## The Space

The space is the **relationally-constrained manifold of all constructible philosophical positions across the 10 axiom branches, and the engine exists to situate a client within it.**

### What the Space Does

1. **Bounds** — not every combination of positions across 10 axes is constructible. EXCLUDES edges eliminate entire regions. The space is the cartesian product minus the excluded regions.
2. **Constrains** — within the bounded space, TENSIONS_WITH and REQUIRES edges create topography. Some positions are easy to construct from (low tension, high compatibility), others are costly (high tension, requiring resolution).
3. **Generates** — GENERATES edges identify positions where construct combinations produce emergent quality that neither construct carries alone. The space has peaks.

### Relation Types (Level 3 Edges)

| Edge Type | Meaning | Transitivity |
|---|---|---|
| `COMPATIBLE_WITH` | Two constructs reinforce each other | Transitive |
| `TENSIONS_WITH` | Two constructs pull against each other | Propagates via REQUIRES chains |
| `REQUIRES` | One construct demands another be present | Transitive |
| `EXCLUDES` | Two constructs cannot coexist | Symmetric, not transitive |
| `GENERATES` | Combination produces emergent quality | Not transitive |
| `RESOLVES` | One construct mediates a known tension | Not transitive |
| `PRECEDES` | One construct must be established before another | Transitive |

Edge properties: `relation_type`, `strength` ∈ [0, 1], `directionality`, `provenance`.

---

## External Surface

### MCP Tools (3)

| Tool | Purpose | When |
|---|---|---|
| `create_prompt_basis` | Full pipeline — intent in, construction basis out. Accepts natural language or pre-formed coordinate. | Primary use. Every time. |
| `explore_space` | Direct graph traversal, neighborhood inspection, path finding, stress testing, triangulation | When the client wants to understand the space itself |
| `extend_schema` | Add dimensions, constructs, relations with contradiction detection | When the client has domain knowledge to contribute |

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
| `axiom_manifest` | The Level 1 axiom layer — the 10 branches and their core questions |
| `schema_manifest` | Current state of Level 2 — all declared dimensions, constructs, relation types |
| `coordinate_schema` | Formal schema of a valid coordinate object |

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
│  stress_test, triangulate — invokes pipeline          │
│  multiple times, compares results                     │
├───────────────────────────────────────────────────────┤
│  Pipeline (7 operators — single forward pass)         │
│  Intent Parser → Coordinate Resolver → Position Comp  │
│  → Construct Resolver → Tension Analyzer              │
│  → Generative Analyzer → Construction Bridge          │
├───────────────────────────────────────────────────────┤
│  Graph Query Layer          Graph Mutation Layer       │
│  list, get, find,           add, validate,            │
│  subgraph, path             contradict check          │
├───────────────────────────────────────────────────────┤
│  Embedding Cache            TF-IDF Cache              │
│  spectral, lifecycle-       construct vectors,        │
│  managed, auto-invalidate   pre-computed at load      │
├───────────────────────────────────────────────────────┤
│  NetworkX (compute)         SQLite (persist)           │
│                             canonical | user tables    │
└───────────────────────────────────────────────────────┘
```

### Graph Query Layer

Internal API that all pipeline operators and external tools use to access graph data. No direct NetworkX access elsewhere in the codebase.

| Method | Returns |
|---|---|
| `list_branches()` | All Level 1 axiom branch nodes |
| `list_constructs(branch, provenance?)` | Level 2 constructs in a branch, optionally filtered by provenance |
| `get_construct(name)` | Full construct with properties and all edges |
| `list_relation_types()` | All valid relation types |
| `get_edges(node, relation_type?)` | Edges from a node, optionally filtered by type |
| `find_path(source, target, weight_fn?)` | Shortest path with optional weight function |
| `find_all_paths(source, target, max_depth?)` | All paths up to depth |
| `get_subgraph(nodes)` | Induced subgraph for a set of nodes |

### Graph Mutation Layer

Internal API for schema authoring with integrity enforcement.

| Method | Behavior |
|---|---|
| `add_construct(branch, name, tags, description, provenance)` | Validates branch exists, checks ID collision, writes to graph and user SQLite table, invalidates embedding cache |
| `add_relation(source, target, relation_type, strength)` | Validates nodes exist, checks for contradictory inverse edges, returns `ContradictionWarning` if found, writes to graph and user SQLite table, invalidates embedding cache |
| `add_dimension(name, category, polarity)` | Level 1 extension — validates against axiom constraints |
| `validate_mutation(proposed_change)` | Dry-run validation without write |

Contradiction map:

| Proposed | Contradicts |
|---|---|
| `COMPATIBLE_WITH` | existing `TENSIONS_WITH` between same pair |
| `TENSIONS_WITH` | existing `COMPATIBLE_WITH` between same pair |
| `REQUIRES` | existing `EXCLUDES` between same pair |
| `EXCLUDES` | existing `REQUIRES` between same pair |

### Embedding Cache

Pre-computed spectral embedding of the full graph. Lifecycle-managed.

- Computed at server startup via graph Laplacian eigendecomposition (numpy, no scipy)
- Cached in memory as dict of `{construct_name: np.ndarray}`
- Graph hash (node count + edge count + edge list checksum) checked before each pipeline run
- Recomputed only when graph has mutated (user added constructs/relations)
- Embedding dimensionality: min(20, n_nodes - 1) non-trivial eigenvectors

```
L = np.diag(A.sum(axis=1)) - A   # Laplacian from numpy adjacency
eigenvalues, eigenvectors = np.linalg.eigh(L)
embedding[node_i] = eigenvectors[i, 1:k+1]
```

### TF-IDF Cache

Pre-computed term frequency–inverse document frequency vectors for construct descriptions. Used by the Intent Parser for natural language → construct matching.

- Computed at server startup from all Level 2 construct descriptions and tags
- Implemented directly with numpy (~50 lines) — no scikit-learn dependency
- Cached as matrix of `(n_constructs, vocabulary_size)` float vectors
- Cosine similarity: `np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))`
- Invalidated and recomputed on graph mutation (same lifecycle as Embedding Cache)

---

## Pipeline Detail

### Data Flow Trace

```
Stage 0  INPUT           string | coordinate object
            │
Stage 1  Intent Parser   string → Dict[branch, Optional[{position, weight, confidence}]]
            │                     partial coordinate (some axes null)
            │
Stage 2  Coord Resolver  partial → Dict[branch, {position, weight}]
            │                     complete coordinate (all 10 axes)
            │
Stage 3  Position Comp   discrete coord → {centroid: float[], per_branch: {primary, embedding, nearby[]}}
            │                     continuous embedding space
            │
Stage 4  Construct Res   continuous → Dict[branch, List[construct]]
            │                     back to discrete, enriched with neighbors
            │
Stage 5  Tension Anal    construct sets → {magnitude: float, direct: [], cascading: [], resolutions: []}
            │                     scalar tensions with cascade paths
            │
Stage 6  Generative An   constructs + tensions → {declared: [], emergent: [], leverage: []}
            │                     combinations and structural importance
            │
Stage 7  Constr Bridge   all accumulated → {coordinate, constructs, tensions, generative, questions{}}
            │                     structured construction basis
            │
         OUTPUT          construction basis with 10 parameterized questions
```

### Stage 1 — Intent Parser

Transforms natural language to a raw partial coordinate. Two-tier matching:

1. **Tag overlap** (fast, high confidence): Each Level 2 construct carries `tags[]`. Tokenize input (lowercase, stem, remove stop words), score overlap per construct per branch.
2. **TF-IDF cosine similarity** (slower, catches synonyms): Pre-computed TF-IDF vectors for construct descriptions. Cosine similarity against input vector.

Combined score: `tag_score * 0.6 + tfidf_score * 0.4`

Constructs scoring above `MATCH_THRESHOLD` per branch are assigned. Branches with no match remain null.

**Weight vs confidence are separate derivations:**
- `confidence` = match quality (combined score)
- `weight` = token emphasis (proportion of matched tokens that matched this branch relative to all matched tokens)

If the input is a pre-formed coordinate object, this stage is bypassed entirely.

### Stage 2 — Coordinate Resolver

Fills null axes and validates the partial coordinate via Constraint Satisfaction Problem (CSP):

1. **Exclusion check**: Verify no EXCLUDES edges between specified positions
2. **Requirements check**: Verify all REQUIRES chains from specified positions are satisfied
3. **Candidate generation**: For each null axis, enumerate valid constructs (no EXCLUDES violations, all REQUIRES satisfied)
4. **Candidate scoring**: Count of COMPATIBLE_WITH edges to specified positions × 1.0 + REQUIRES pull × 2.0
5. **Tiebreaker**: Betweenness centrality from pre-computed centrality cache
6. **Auto-fill weight**: Base 0.15, ceiling 0.4, scaled by compatibility pull ratio

Output: Complete 10-axis coordinate with weights. No nulls. All constraints satisfied.

### Stage 3 — Position Computer

Projects the discrete coordinate into continuous embedding space:

1. Look up each construct's pre-computed spectral embedding vector
2. Compute weighted centroid: `P = Σᵢ wᵢ · embedding(dᵢ) / Σᵢ wᵢ`
3. Compute distance from centroid to every construct in the graph

Output: Continuous manifold position with per-branch neighborhood distances.

### Stage 4 — Construct Resolver

Determines the full set of active constructs per branch:

1. Primary construct = the coordinate's specified position (always active)
2. Nearby constructs in embedding space within activation threshold are also activated
3. Activation threshold is adaptive: 60% of mean nearest-neighbor distance within each branch

Dense branches (many constructs close together) → tighter threshold.
Sparse branches (few constructs far apart) → wider threshold.

Output: Dict of active construct lists per branch (1-3 per branch typically).

### Stage 5 — Tension Analyzer

Computes direct and cascading tensions:

**Direct**: For every pair of active constructs across all branches, check for TENSIONS_WITH edges. Record pair and edge strength.

**Cascading**: For every active construct, follow REQUIRES chains outward (transitive closure). At each hop, check for TENSIONS_WITH edges to any other active construct. Apply decay per hop:

```
tension_at_hop_n = direct_tension_strength × decay^n
```

Decay factor derived from mean REQUIRES edge strength in the graph. Cascade stops when magnitude < 0.05 (negligible threshold).

**Resolution paths**: For each tension, check if any construct in the graph has RESOLVES edges to both endpoints.

Output: Total magnitude scalar + list of direct tensions + list of cascading tensions with chain paths + list of resolution paths.

### Stage 6 — Generative Analyzer

Discovers declared and emergent generative combinations:

1. **Declared**: Check for GENERATES edges between active construct pairs
2. **Community detection**: Run Louvain on the subgraph of active constructs. Cross-community pairs indicate high diversity → potential generativity
3. **Centrality**: Compute betweenness centrality (bridge constructs) and PageRank (influence hubs) for active constructs within the full graph

Output: Declared generative combinations + emergent cross-community pairs + structural leverage points.

### Stage 7 — Construction Bridge

Transforms all accumulated analysis into actionable construction questions:

1. For each of the 10 axiom branches, look up the construction question template
2. Substitute active constructs for that branch
3. If tensions touch this branch, append tension context
4. If generative combinations touch this branch, append generative opportunity context
5. Assemble the full construction basis output

Output: The final `create_prompt_basis` response — coordinate, active constructs, tensions, generative combinations, and 10 parameterized construction questions.

---

## Multi-Pass Orchestrator

Operations that invoke the pipeline multiple times. These live above the pipeline, not inside it. Accessed via `explore_space` tool or MCP prompt workflows.

### stress_test(coordinate)

Perturbs each axis to its nearest alternative construct. Runs the pipeline for each perturbation. Compares tension deltas and generative deltas against the baseline.

Returns:
- Baseline construction basis
- Breakpoints: perturbations that increase tension by > 0.3
- Improvements: perturbations that decrease tension by > 0.2

Computational cost: ~10 axes × ~10 alternatives = ~100 pipeline runs.

### triangulate(coordinate_a, coordinate_b)

Runs the pipeline twice with different coordinates. Computes the intersection of active construct sets, shared tensions, shared generative combinations, and the coordinate distance between the two positions.

Returns:
- Per-branch construct intersection
- Coordinate distance (weighted sum of per-axis distances)
- Shared tensions and shared generative combinations

---

## Mathematical Operations

### Vector Construction (Intent Parser)

```
C = [(d₁, w₁), (d₂, w₂), ..., (d₁₀, w₁₀)]
where dᵢ ∈ {constructs in branch i} ∪ {∅}
and   wᵢ ∈ [0, 1]
```

### TF-IDF Matching (Intent Parser)

Implemented with numpy only:
```
TF(term, doc) = count(term in doc) / len(doc)
IDF(term) = log(N / docs_containing(term))
similarity = dot(tfidf_intent, tfidf_construct) / (norm(a) * norm(b))
```

### Constraint Propagation (Coordinate Resolver)

Boolean constraint satisfaction:
```
For each unspecified axis i:
  Candidates(i) = {c ∈ constructs(branch_i) |
    ∀ specified (dⱼ): ¬EXCLUDES(c, dⱼ)
    ∧ all REQUIRES chains from specified positions are satisfied
  }
```

Candidate scoring: `COMPATIBLE_WITH_count × 1.0 + REQUIRES_count × 2.0`

### Graph Distance Metric (Position Computer)

Weighted path distance:
```
d_rel(a, b) = min Σ edge_weight(eᵢ) along all paths from a to b

where edge_weight:
  COMPATIBLE_WITH = 0.2  (low friction)
  TENSIONS_WITH   = 0.8  (high friction)
  REQUIRES        = 0.1  (structural dependency)
  EXCLUDES        = ∞    (unreachable)
```

Coordinate distance:
```
D(C₁, C₂) = Σᵢ wᵢ · d_rel(C₁.dᵢ, C₂.dᵢ)
```

### Spectral Embedding (Position Computer)

Graph Laplacian eigendecomposition (numpy, no scipy):
```
A = nx.to_numpy_array(G)
L = np.diag(A.sum(axis=1)) - A
eigenvalues, eigenvectors = np.linalg.eigh(L)
k = min(20, n - 1)
embedding[node_i] = eigenvectors[i, 1:k+1]
```

### Tension Magnitude (Tension Analyzer)

```
T_direct(C) = Σ strength(e) for all TENSIONS_WITH edges between active constructs
T_cascade(C) = Σ strength(e) · decay^(hops) for propagated tensions via REQUIRES chains
T(C) = T_direct(C) + T_cascade(C)

decay = mean(strength(e) for all REQUIRES edges in graph)
cascade terminates when magnitude < 0.05
```

### Community Detection (Generative Analyzer)

Louvain modularity optimization (pure Python in NetworkX 2.8+):
```
Q = (1/2m) Σᵢⱼ [Aᵢⱼ - (kᵢkⱼ/2m)] · δ(cᵢ, cⱼ)
```

### Centrality Analysis (Generative Analyzer)

Betweenness centrality for bridge constructs. PageRank for influence hubs. Both native NetworkX.

### Transitive Closure (Multiple Operators)

```
TC(R) = R ∪ R² ∪ R³ ∪ ... ∪ Rⁿ
```

Computes indirect relationships not explicitly declared. Applied to COMPATIBLE_WITH and REQUIRES edges.

### Pareto Optimization (Multi-Pass Orchestrator)

```
Minimize: T(C)                    (tension)
Maximize: |generative_edges(C)|   (generative surface)
Subject to: verify_compatibility(C) = True
```

Computed by enumerating perturbations via stress_test, not by continuous optimization.

---

## Data Integrity

### Canonical vs User Data

Data is separated at the persistence layer and merged at query time.

```
SQLite:
  canonical_nodes    (read-only, enforced by DB trigger)
  canonical_edges    (read-only, enforced by DB trigger)
  user_nodes         (read-write)
  user_edges         (read-write, FK → canonical_nodes OR user_nodes)
```

### Integrity Rules

| Rule | Enforcement |
|---|---|
| Canonical nodes cannot be modified or deleted | `mutable: False`, DB-level write protection |
| User nodes can connect to canonical nodes freely | Cross-provenance edges are valid |
| Canonical edges cannot be removed | Provenance check on edge deletion |
| User can add edges between canonical nodes | Cross-provenance Tier 3 edges are legitimate |
| Contradiction detection at authoring time | Inverse relation check via Graph Mutation Layer |
| Version stability | Canonical node IDs are permanent across versions |

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
| **Reactive** | Gap discovered during active use | Intent Parser returns unknown values |
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
    "ontology":     { "position": "...", "weight": 0.0 },
    "epistemology":  { "position": "...", "weight": 0.0 },
    "axiology":      { "position": "...", "weight": 0.0 },
    "teleology":     { "position": "...", "weight": 0.0 },
    "phenomenology": { "position": "...", "weight": 0.0 },
    "praxeology":    { "position": "...", "weight": 0.0 },
    "methodology":   { "position": "...", "weight": 0.0 },
    "semiotics":     { "position": "...", "weight": 0.0 },
    "hermeneutics":  { "position": "...", "weight": 0.0 },
    "heuristics":    { "position": "...", "weight": 0.0 }
  },
  "active_constructs": {
    "ontology":     ["..."],
    "epistemology":  ["..."],
    "axiology":      ["..."],
    "teleology":     ["..."],
    "phenomenology": ["..."],
    "praxeology":    ["..."],
    "methodology":   ["..."],
    "semiotics":     ["..."],
    "hermeneutics":  ["..."],
    "heuristics":    ["..."]
  },
  "tensions": [
    {
      "between": ["construct_a", "construct_b"],
      "magnitude": 0.0,
      "type": "declared | inferred_cascade",
      "chain": ["..."],
      "resolution_paths": ["..."]
    }
  ],
  "generative_combinations": [
    {
      "constructs": ["construct_a", "construct_b"],
      "quality": "...",
      "source": "declared | community_detected"
    }
  ],
  "structural_leverage": [
    {
      "construct": "...",
      "role": "bridge | influence_hub",
      "score": 0.0
    }
  ],
  "construction_questions": {
    "ontology": {
      "question": "What entities and relationships does this prompt assume exist?",
      "active": ["..."],
      "context": "...",
      "tension_note": "...",
      "generative_note": "..."
    },
    "epistemology": { "...": "..." },
    "axiology": { "...": "..." },
    "teleology": { "...": "..." },
    "phenomenology": { "...": "..." },
    "praxeology": { "...": "..." },
    "methodology": { "...": "..." },
    "semiotics": { "...": "..." },
    "hermeneutics": { "...": "..." },
    "heuristics": { "...": "..." }
  }
}
```

The construction questions are the **bridge** between dimensional analysis and prompt construction. Each question is parameterized by the active constructs at the computed coordinate position. The client reads 10 questions and constructs a prompt that answers them.

---

## Performance Characteristics

| Operation | Expected scale | Expected time |
|---|---|---|
| Spectral embedding (startup) | ~500 nodes, 500×500 matrix | ~10ms |
| TF-IDF pre-computation (startup) | ~500 construct descriptions | ~20ms |
| Community detection | ~500 nodes | ~5ms |
| CSP coordinate resolution | 10 branches × ~50 constructs | ~1ms |
| Single pipeline run | All 7 stages | ~50-100ms |
| Stress test (multi-pass) | ~100 pipeline runs | ~5-10s |
| Memory footprint | Graph + embeddings + TF-IDF vectors | < 50MB |
