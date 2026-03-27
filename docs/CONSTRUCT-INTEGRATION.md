# Construct Integration Mapping

This document maps every element of the Construct (defined in `CONSTRUCT.md`) to its counterpart in the Universal Prompt Creation Engine (defined in `DESIGN.md`). It serves as the change specification for updating DESIGN.md.

---

## Element Mappings

### Plane → Branch

| Construct | Engine |
|---|---|
| A plane is a domain of meaning | A branch is one of 10 philosophical disciplines |
| 10 planes | 10 axiom branches (Ontology, Epistemology, Axiology, Teleology, Phenomenology, Praxeology, Methodology, Semiotics, Hermeneutics, Heuristics) |
| Each plane is a self-consistent field of interpretation | Each branch has a core question and a construction question template |
| Each plane has internal 2D structure | Each branch gains two named sub-dimensions (x-axis and y-axis) |

The mapping is direct and complete. No structural adaptation required.

#### Sub-Dimensions per Branch

Each branch's x-axis and y-axis represent two fundamental tensions:

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

This gives the engine 20 named sub-axes, 40 named edge meanings, and 40 corner extremes.

---

### Point → Construct (Level 2 Node)

| Construct | Engine |
|---|---|
| A point is a specific possibility of observation | A Level 2 construct is a position-determined epistemic node |
| 100 points per plane | 100 constructs per branch |
| Position determines role, potency, relationships | Grid position (x, y) determines classification, potency, spectrum membership |
| The source of each point is a specific possibility | Each construct carries a predefined epistemic question as its content |

**What changes in DESIGN.md:**

Previously: Level 2 nodes were a flat list with open count and `name` as primary identifier.

Now: Level 2 nodes are positioned in a 10x10 grid with exactly 100 per branch. Primary identifier changes from `branch.construct_name` to `branch.x_y`.

Node properties change from:

```
name, branch, description, tags, provenance, mutable
```

To:

```
id (branch.x_y), branch, x, y, classification, potency, question,
description, tags, provenance, mutable, spectrum_ids
```

---

### Point Content → Canonical Shipped Data

| Construct | Engine |
|---|---|
| Pre-existing, pre-temporal points of observation | Pre-populated canonical constructs shipped with the engine |
| The source of each point is a specific possibility | Each point carries the Construct's epistemic question for that grid position, parameterized by branch |
| Points amplify specific knowledge to a utilitarian degree | The question text serves as both content (for TF-IDF matching) and guidance (for construction output) |

**What changes in DESIGN.md:**

Previously: Canonical content was undefined — the Schema Layer was an empty structure awaiting authoring.

Now: The Schema Layer ships with 1000 constructs (100 per branch × 10 branches). Content is derived from the Construct specification's 100 positional epistemic questions, parameterized across branches. The engine is operational on first activation.

---

### Point Classification → Potency Gradient

| Construct classification | Engine mapping | Potency |
|---|---|---|
| Corner (4 per plane) | Maximum-potency organizational bounds | 1.0 |
| Midpoint (8 per plane — dual model) | Spectrum-centering axial pivots | 0.9 |
| Edge — remaining (24 per plane) | High-potency force integrators | 0.8 |
| Center (64 per plane) | Resolution and synthesis nodes | 0.6 |

**What changes in DESIGN.md:**

Previously: All constructs had uniform weight. Potency was not a concept.

Now: The pipeline's Tension Analyzer, Nexus/Gem Analyzer, and Construction Bridge weight computations by potency. Edge constructs amplify tensions. Center constructs dampen them. Corner constructs have maximum amplification.

---

### Spectrum → Auto-Generated Relations

| Construct | Engine |
|---|---|
| 20 spectrums per plane from geometric edge opposition | 20 spectrum edges per branch = 200 total, auto-generated |
| A spectrum is difference as structure | Spectrum edges are typed as geometric structural oppositions, distinct from manually-declared TENSIONS_WITH |

**What changes in DESIGN.md:**

Previously: All tensions were manually declared TENSIONS_WITH edges or inferred via transitive closure.

Now: 180 spectrum edges are auto-generated from grid geometry at graph initialization (18 per branch; see Spec 02). These coexist with manually-declared edges. A new edge type `SPECTRUM_OPPOSITION` distinguishes geometric from authored tensions.

Relation types table gains:

| Edge Type | Meaning | Source |
|---|---|---|
| `SPECTRUM_OPPOSITION` | Geometric opposition between edge points | Auto-generated from grid geometry |

---

### Nexus → Nexus Node

| Construct | Engine |
|---|---|
| A nexus is a mediating locus between two planes with its own identity | A nexus is a graph node (not an edge) sitting between two branch subgraphs |
| Receives edge energies from both planes | Receives the 36 edge-classified constructs from both connected branches |
| Integrates as harmonic juxtaposition | Computes an integration function over both sets of edge energies |
| Gives transformed energy back to both planes | The computed result (gem) is associated with both branches |
| 90 directional nexi | 90 nexus nodes in the graph, each connecting one branch directionally to another |

**What changes in DESIGN.md:**

Previously: Cross-branch connections were direct construct-to-construct edges. No nexus nodes existed.

Now: 90 nexus nodes are added to the graph. Each nexus node connects to two branch nodes via directed edges. Nexus nodes have properties: `id`, `source_branch`, `target_branch`, `provenance: canonical`.

The graph gains a new node type at a new structural level between Level 1 (axiom branches) and Level 2 (constructs).

---

### Gem → Nexus Computation Output

| Construct | Engine |
|---|---|
| A gem is the condensed state of a nexus interaction | A gem is the computed value produced by a nexus operation |
| Embodies integrated awareness of two domains | Stored as a property of the nexus node or as a separate computed value |
| Can be observed, evaluated, reused | Returned in the construction basis output; available for recursive condensation |

**What changes in DESIGN.md:**

Previously: No concept of gems. Cross-branch analysis returned direct edge-based results.

Now: Each nexus operation produces a gem — a computed value with at minimum a magnitude (strength of integration). Gems are part of the construction basis output. Gems are the entities that condense into center points during recursive embedding.

---

### Spoke → Behavioral Signature

| Construct | Engine |
|---|---|
| A spoke is the complete set of a plane's interactions with all other planes | A spoke is the aggregation of one branch's 9 gem values |
| The distribution has shape: strength, consistency, polarity, contribution | 4 computable properties per spoke |
| A spoke is a behavioral signature | The pipeline computes and returns spoke profiles per branch |

**What changes in DESIGN.md:**

Previously: No spoke concept. No per-branch system-level analysis.

Now: The pipeline gains a spoke computation stage (or sub-stage within the Nexus/Gem Analyzer) that aggregates nexus results into spoke profiles.

Spoke shape properties — all mechanically computable:

| Property | Computation |
|---|---|
| Strength | Mean magnitude of the 9 gems on this spoke |
| Consistency | 1 - normalized standard deviation across the 9 gem magnitudes |
| Polarity | Count of tension-flagged gems / total gems on this spoke |
| Contribution | This spoke's aggregate magnitude / sum of all 10 spokes' aggregates |

Spoke classification from thresholds:
- High strength + high consistency = **coherent**
- High strength + low consistency = **fragmented**
- High strength + high contribution = **dominant**
- Low strength overall = **weakly integrated**

---

### Central Gem → System Coherence

| Construct | Engine |
|---|---|
| Unified convergence of all nexus interactions | A single computed value aggregating all 10 spoke contributions |
| Reflects overall coherence across the system | A coherence score + classification in the construction basis output |
| Singular reference point for total alignment | One node in the graph connected to all 90 nexus nodes |

**What changes in DESIGN.md:**

Previously: No central gem. No system-wide coherence metric.

Now: One central gem node in the graph. Its value is computed from all 10 spoke contributions. Returned in the construction basis as a coherence score.

---

### Wheel → Dual View of Nexi

| Construct | Engine |
|---|---|
| Network view: nexus-centric, pairwise | Nexus-level results in the construction basis — per-pair interaction details |
| Radial view: spoke-centric, per-domain | Spoke-level profiles in the construction basis — per-branch behavioral signatures |

**What changes in DESIGN.md:**

Previously: Only network-level (pairwise) cross-branch analysis.

Now: Both views are computed and returned. The construction basis output includes both nexus-level detail and spoke-level profiles.

---

### Recursive Embedding → Iterative Pipeline

| Construct | Engine |
|---|---|
| Gems condense into center points of uninvolved planes | A gem value is projected as a coordinate position on a third branch |
| Creates recombinant interaction at different scales | The pipeline can run iteratively: pass 1 produces gems → gems condense to new positions → pass 2 runs at deeper integration |

**What changes in DESIGN.md:**

Previously: The Multi-Pass Orchestrator supported stress_test and triangulate. No recursive mechanism.

Now: The Multi-Pass Orchestrator gains a `deepen` operation that:
1. Takes a construction basis from a completed pipeline pass
2. Selects gems for condensation
3. Projects each selected gem into a center-point position on an uninvolved branch
4. Runs the pipeline again with the modified coordinate
5. Returns the deeper construction basis

---

### Coordinate Object Change

Previously:
```json
{ "epistemology": { "position": "construct_name", "weight": 0.8 } }
```

Now:
```json
{ "epistemology": { "x": 3, "y": 0, "weight": 0.8 } }
```

Position is a grid coordinate, not a name. The coordinate carries structural information: classification, potency, spectrum membership, sub-dimensional meaning.

The `create_prompt_basis` tool accepts either:
- Natural language intent (mapped to grid positions via TF-IDF colocation)
- A pre-formed coordinate with (x, y) positions per branch

---

### Construction Basis Output Change

Previously included:
- Coordinate
- Active constructs (by name)
- Tensions (declared + inferred)
- Generative combinations
- 10 construction questions

Now additionally includes:
- Active constructs with grid position, classification, potency, and predefined question
- Spectrum opposites for each active position (the opposite edge point and its question)
- Structural profile (edge/center ratio, mean potency)
- Gem values for active nexus interactions
- Spoke profiles for each branch (strength, consistency, polarity, contribution, classification)
- Central gem coherence score and classification
- Nexus-level detail (network view) alongside spoke-level profiles (radial view)

---

## DESIGN.md Section Impact Map

Every section of DESIGN.md and its required change:

| Section | Line | Change required |
|---|---|---|
| Overview | 3 | Add: "grounded in a Construct of 10 planes, each a 10x10 grid of epistemic observation points" |
| Analog | 9 | No change — spectrometer analog holds |
| Technology Stack | 26 | No change — same stack |
| Deployment Topology | 47 | No change — same topology |
| **Level 1 — Axiom Layer** | 71 | Add: sub-dimensions per branch table, construction question templates already present |
| **Level 2 — Schema Layer** | 164 | **Major rewrite** — flat list → 10x10 grid, add classification, potency, point content, spectrum membership, new node properties, fixed cardinality (100 per branch, 1000 total) |
| **Level 3 — Coordinate Layer** | 179 | **Rewrite** — position changes from construct_name to (x, y), add structural semantics of position |
| **The Space** | 208 | Add: 200 auto-generated spectrums, potency topography, edge encapsulation |
| Relation Types | 218 | Add: SPECTRUM_OPPOSITION edge type |
| **External Surface** | 234 | No tool changes; output format changes documented here or in Construction Output |
| **Internal Architecture** | 263 | **Major rewrite** — add nexus/gem layer, spoke computation stage, central gem node, recursive embedding in orchestrator |
| Graph Query Layer | 294 | Add: grid-aware queries (list_by_classification, get_spectrum_opposite, get_spoke) |
| Graph Mutation Layer | 309 | Add: grid-position validation on construct addition |
| Embedding Cache | 329 | Minor — embedding now operates over grid-structured graph with nexus nodes |
| TF-IDF Cache | 345 | Minor — vectors built from predefined questions, not arbitrary descriptions |
| **Pipeline Data Flow** | 359 | **Rewrite** — coordinate is (x, y) not name, add spoke computation, add gem computation |
| **Stage 1 — Intent Parser** | 388 | Rewrite — matches against predefined questions in TF-IDF space, outputs grid positions |
| Stage 2 — Coordinate Resolver | 405 | Minor — CSP operates on grid positions, candidate scoring uses potency |
| **Stage 3 — Position Computer** | 418 | Rewrite — embedding lookup uses grid-structured graph including nexus nodes |
| **Stage 4 — Construct Resolver** | 428 | Rewrite — activation by embedding neighborhood, classification and potency attached |
| **Stage 5 — Tension Analyzer** | 441 | Rewrite — add spectrum oppositions, potency-weighted tension magnitude |
| **Stage 6 — Nexus/Gem Analyzer** | 459 | **Major rewrite** — add nexus computation producing gems, spoke aggregation producing behavioral signatures, central gem computation |
| **Stage 7 — Construction Bridge** | 469 | Rewrite — output includes predefined questions, spectrum opposites, spoke profiles, central gem |
| **Multi-Pass Orchestrator** | 483 | Add: `deepen` operation for recursive gem condensation |
| Mathematical Operations | 509 | Add: spoke shape computation (mean, std dev, ratio), gem magnitude computation, central gem aggregation |
| **Data Integrity** | 612 | Rewrite canonical table structure — nodes now have grid position, 1000 shipped constructs, 90 nexus nodes, 1 central gem node |
| Enrichment Use Cases | 653 | Minor — user extensions target grid positions or add new nexus edges |
| **Construction Output** | 675 | **Major rewrite** — new output format with grid positions, questions, spectrums, gems, spokes, central gem |
| **Performance Characteristics** | 753 | Update — shipped graph is now 1056 nodes, ~1544 edges; add spoke computation time |

### Summary of Change Severity

| Severity | Sections |
|---|---|
| **No change** | Overview (minor add), Analog, Technology Stack, Deployment Topology, External Surface (tools unchanged) |
| **Minor update** | Stage 2, Embedding Cache, TF-IDF Cache, Enrichment Use Cases |
| **Rewrite** | Level 2, Level 3, The Space, Pipeline Data Flow, Stages 1/3/4/5/7, Multi-Pass Orchestrator, Construction Output |
| **Major rewrite** | Internal Architecture, Stage 6 (gains nexus/gem/spoke), Data Integrity (new node types and counts) |

---

## Shipped Graph Summary (Post-Integration)

| Node type | Count | Source |
|---|---|---|
| Axiom branch nodes (Level 1) | 10 | Canonical |
| Construct nodes (Level 2) | 1000 | Canonical (10 branches × 100 grid positions) |
| Nexus nodes | 90 | Canonical (directional, one per branch pair) |
| Central gem node | 1 | Canonical |
| **Total nodes** | **1101** | |

| Edge type | Count | Source |
|---|---|---|
| HAS_CONSTRUCT (branch → construct) | 1000 | Canonical |
| PRECEDES (branch → branch) | 9 | Canonical |
| SPECTRUM_OPPOSITION (construct ↔ construct) | 180 | Auto-generated from grid geometry (18 per branch) |
| NEXUS_SOURCE (nexus → source branch) | 90 | Canonical |
| NEXUS_TARGET (nexus → target branch) | 90 | Canonical |
| CENTRAL_GEM_LINK (central gem → nexus) | 90 | Canonical |
| **Total edges** | **1459** | |

User extensions add to this via the Graph Mutation Layer with provenance tagging. Canonical data remains immutable.
