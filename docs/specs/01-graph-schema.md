# Spec 01 — Graph Schema

## Purpose

Defines every node type, edge type, property, ID format, and provenance rule in the graph. This is the structural foundation — all other specs reference these definitions.

---

## Node Types

### 1. Branch Node (Level 1 — Axiom)

Represents one of the 10 philosophical planes.

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Branch name: `ontology`, `epistemology`, etc. |
| `type` | string | yes | Always `"branch"` |
| `tier` | int | yes | Always `1` |
| `core_question` | string | yes | The branch's fundamental question |
| `construction_template` | string | yes | The parameterizable construction question |
| `x_axis_name` | string | yes | Name of the x sub-dimension (e.g., `"Particular → Universal"`) |
| `y_axis_name` | string | yes | Name of the y sub-dimension (e.g., `"Static → Dynamic"`) |
| `x_axis_low` | string | yes | Label for x=0 (e.g., `"Particular"`) |
| `x_axis_high` | string | yes | Label for x=9 (e.g., `"Universal"`) |
| `y_axis_low` | string | yes | Label for y=0 (e.g., `"Static"`) |
| `y_axis_high` | string | yes | Label for y=9 (e.g., `"Dynamic"`) |
| `causal_order` | int | yes | Position in the inter-branch causal sequence (0-9) |
| `provenance` | string | yes | Always `"canonical"` |
| `mutable` | bool | yes | Always `false` |

**Count:** 10

### 2. Construct Node (Level 2 — Schema)

Represents one observation point on a branch's 10x10 grid.

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Format: `"{branch}.{x}_{y}"` (e.g., `"epistemology.3_0"`) |
| `type` | string | yes | Always `"construct"` |
| `tier` | int | yes | Always `2` |
| `branch` | string | yes | Parent branch ID |
| `x` | int | yes | Grid x-coordinate (0-9) |
| `y` | int | yes | Grid y-coordinate (0-9) |
| `classification` | string | yes | One of: `"corner"`, `"midpoint"`, `"edge"`, `"center"` |
| `potency` | float | yes | Position-derived: corner=1.0, midpoint=0.9, edge=0.8, center=0.6 |
| `question` | string | yes | The epistemic question for this grid position, parameterized by branch (from Spec 03a) |
| `question_revisited` | string | no | A second epistemic question for positions that are revisited in the source (Q87 for (4,4), Q100 for (9,9)). Null for all other positions. |
| `condensed_gems` | list[dict] | no | Gems condensed into this point via recursive embedding (deepen operation). Each entry: `{source_nexus, magnitude, source_planes, generation}`. Empty list by default. Overlay, never replace — base construct is preserved. |
| `description` | string | yes | Expanded description combining positional role with branch domain |
| `tags` | list[str] | yes | Keywords extracted from the question for TF-IDF matching |
| `spectrum_ids` | list[str] | yes | IDs of spectrums this point participates in (0 for center, 1-2 for edge) |
| `provenance` | string | yes | `"canonical"` or `"user"` |
| `mutable` | bool | yes | `false` for canonical, `true` for user |

**Count:** 1000 canonical (100 per branch × 10 branches). User constructs add to this.

**ID Format:** `{branch}.{x}_{y}` — e.g., `epistemology.3_0`, `ontology.0_0`, `heuristics.9_9`

### 3. Nexus Node

Represents a mediating locus between two branches. A place of interaction with its own identity.

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Format: `"nexus.{source}.{target}"` (e.g., `"nexus.epistemology.methodology"`) |
| `type` | string | yes | Always `"nexus"` |
| `source_branch` | string | yes | The branch this nexus originates from |
| `target_branch` | string | yes | The branch this nexus connects to |
| `content` | string | yes | Philosophical description of what this branch-pair interaction means |
| `provenance` | string | yes | Always `"canonical"` |
| `mutable` | bool | yes | Always `false` |

**Count:** 90 directional nexus nodes (10 branches × 9 outward connections each). These correspond to 45 unique plane pairs, each represented by 2 directional nexi. Per the Full Specification (CONSTRUCT.md §9.5), the distinction between 45 unique nexus entities and 90 directional participations should be preserved rather than collapsed.

**ID Format:** `nexus.{source_branch}.{target_branch}` — directional. `nexus.epistemology.methodology` ≠ `nexus.methodology.epistemology`. The pair shares a unique nexus site, but each directional participation is a separate node because each branch contributes differently.

### 4. Central Gem Node

The singular convergence point of all nexus interactions.

| Property | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Always `"central_gem"` |
| `type` | string | yes | Always `"central_gem"` |
| `content` | string | yes | Description of universal convergence |
| `provenance` | string | yes | Always `"canonical"` |
| `mutable` | bool | yes | Always `false` |

**Count:** 1

---

## Node Count Summary

| Type | Count | Provenance |
|---|---|---|
| Branch | 10 | Canonical |
| Construct | 1000 | Canonical (user adds more) |
| Nexus | 90 | Canonical |
| Central Gem | 1 | Canonical |
| **Total** | **1101** | |

---

## Edge Types

### 1. HAS_CONSTRUCT

Connects a branch to its 100 grid constructs.

| Property | Type | Value |
|---|---|---|
| `relation` | string | `"HAS_CONSTRUCT"` |
| `source_type` | string | `"branch"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"directed"` (branch → construct) |
| `provenance` | string | `"canonical"` |

**Count:** 1000 (100 per branch × 10 branches)

### 2. PRECEDES

Encodes the causal ordering between branches.

| Property | Type | Value |
|---|---|---|
| `relation` | string | `"PRECEDES"` |
| `source_type` | string | `"branch"` |
| `target_type` | string | `"branch"` |
| `directionality` | string | `"directed"` (earlier → later in causal order) |
| `provenance` | string | `"canonical"` |

**Count:** 9 (sequential pairs: ontology→epistemology, epistemology→axiology, etc.)

### 3. SPECTRUM_OPPOSITION

Geometric opposition between two edge points on the same branch. Auto-generated from grid geometry.

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"SPECTRUM_OPPOSITION"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"symmetric"` |
| `spectrum_id` | string | Unique spectrum identifier: `"{branch}.spectrum_{n}"` |
| `strength` | float | Always `0.6` (geometric, not authored) |
| `question` | string or null | Epistemic question describing this spectrum's opposition (from Spec 03a Q37-Q55, parameterized by branch). Null for spectrums not covered by source questions. |
| `source` | string | `"geometric"` |
| `provenance` | string | `"canonical"` |

**Count:** 180 (18 unique edge↔edge reflection pairs per branch × 10 branches; see Spec 02 for precise algorithm)

**Constraint:** Both endpoints must be edge-classified constructs (corner, midpoint, or edge) on the same branch.

### 4. NEXUS_SOURCE

Connects a nexus to its source branch.

| Property | Type | Value |
|---|---|---|
| `relation` | string | `"NEXUS_SOURCE"` |
| `source_type` | string | `"nexus"` |
| `target_type` | string | `"branch"` |
| `directionality` | string | `"directed"` (nexus → branch) |
| `provenance` | string | `"canonical"` |

**Count:** 90

### 5. NEXUS_TARGET

Connects a nexus to its target branch.

| Property | Type | Value |
|---|---|---|
| `relation` | string | `"NEXUS_TARGET"` |
| `source_type` | string | `"nexus"` |
| `target_type` | string | `"branch"` |
| `directionality` | string | `"directed"` (nexus → branch) |
| `provenance` | string | `"canonical"` |

**Count:** 90

### 6. CENTRAL_GEM_LINK

Connects the central gem to each nexus.

| Property | Type | Value |
|---|---|---|
| `relation` | string | `"CENTRAL_GEM_LINK"` |
| `source_type` | string | `"central_gem"` |
| `target_type` | string | `"nexus"` |
| `directionality` | string | `"directed"` (central gem → nexus) |
| `provenance` | string | `"canonical"` |

**Count:** 90

### 7. COMPATIBLE_WITH

Declared compatibility between two constructs (same or different branches).

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"COMPATIBLE_WITH"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"symmetric"` |
| `strength` | float | ∈ [0, 1] |
| `source` | string | `"declared"` |
| `provenance` | string | `"canonical"` or `"user"` |

**Count:** Variable (authored)
**Transitivity:** Yes

### 8. TENSIONS_WITH

Declared tension between two constructs.

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"TENSIONS_WITH"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"symmetric"` |
| `strength` | float | ∈ [0, 1] |
| `source` | string | `"declared"` |
| `provenance` | string | `"canonical"` or `"user"` |

**Count:** Variable (authored)
**Transitivity:** Propagates via REQUIRES chains

### 9. REQUIRES

Declared dependency — one construct demands another be present.

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"REQUIRES"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"directed"` (source requires target) |
| `strength` | float | ∈ [0, 1] |
| `source` | string | `"declared"` |
| `provenance` | string | `"canonical"` or `"user"` |

**Count:** Variable (authored)
**Transitivity:** Yes

### 10. EXCLUDES

Declared mutual exclusion — two constructs cannot coexist.

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"EXCLUDES"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"symmetric"` |
| `source` | string | `"declared"` |
| `provenance` | string | `"canonical"` or `"user"` |

**Count:** Variable (authored)
**Transitivity:** No

### 11. GENERATES

Declared generative combination — two constructs together produce emergent quality.

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"GENERATES"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` |
| `directionality` | string | `"symmetric"` |
| `quality` | string | Description of what the combination generates |
| `source` | string | `"declared"` |
| `provenance` | string | `"canonical"` or `"user"` |

**Count:** Variable (authored)
**Transitivity:** No

### 12. RESOLVES

Declared resolution — one construct mediates a known tension between two others.

| Property | Type | Description |
|---|---|---|
| `relation` | string | `"RESOLVES"` |
| `source_type` | string | `"construct"` |
| `target_type` | string | `"construct"` (one of the two tension endpoints) |
| `directionality` | string | `"directed"` (resolver → tension endpoint) |
| `resolves_tension_between` | list[str] | IDs of the two constructs whose tension this resolves |
| `source` | string | `"declared"` |
| `provenance` | string | `"canonical"` or `"user"` |

**Count:** Variable (authored)
**Transitivity:** No

---

## Edge Count Summary (Canonical)

| Type | Count | Source |
|---|---|---|
| HAS_CONSTRUCT | 1000 | Structural |
| PRECEDES | 9 | Structural |
| SPECTRUM_OPPOSITION | 180 | Geometric (18 per branch × 10; see Spec 02) |
| NEXUS_SOURCE | 90 | Structural |
| NEXUS_TARGET | 90 | Structural |
| CENTRAL_GEM_LINK | 90 | Structural |
| COMPATIBLE_WITH | Variable | Authored |
| TENSIONS_WITH | Variable | Authored |
| REQUIRES | Variable | Authored |
| EXCLUDES | Variable | Authored |
| GENERATES | Variable | Authored |
| RESOLVES | Variable | Authored |
| **Fixed total** | **1696** | (1000 + 9 + 180 + 90 + 90 + 90) |
| **Authored total** | **TBD** | |

---

## Provenance Model

| Provenance | Mutable | Who creates | What can reference |
|---|---|---|---|
| `canonical` | No | Shipped with engine | Anything |
| `user` | Yes | Client via `extend_schema` | Canonical nodes, user nodes |

### Rules

1. Canonical nodes cannot be modified or deleted — enforced at DB level (SQLite triggers)
2. Canonical edges cannot be removed — enforced at DB level
3. User nodes can connect to canonical nodes via any declared edge type
4. User can add edges between two canonical nodes (new relationships, not modifications)
5. User-created edges carry `provenance: "user"` and are mutable
6. All queries default to `provenance: "merged"` (canonical + user) but can be filtered

### Contradiction Detection

When a user proposes an edge, the Graph Mutation Layer checks:

| Proposed edge | Contradiction if exists |
|---|---|
| `COMPATIBLE_WITH(A, B)` | `TENSIONS_WITH(A, B)` or `EXCLUDES(A, B)` |
| `TENSIONS_WITH(A, B)` | `COMPATIBLE_WITH(A, B)` |
| `REQUIRES(A, B)` | `EXCLUDES(A, B)` |
| `EXCLUDES(A, B)` | `COMPATIBLE_WITH(A, B)` or `REQUIRES(A, B)` |

If contradiction detected: return `ContradictionWarning` with existing edge and proposed edge. User decides: cancel, override, or add resolution path.

---

## Valid Edge Connections

| Edge type | Source node type | Target node type |
|---|---|---|
| HAS_CONSTRUCT | branch | construct |
| PRECEDES | branch | branch |
| SPECTRUM_OPPOSITION | construct (edge-class) | construct (edge-class, same branch) |
| NEXUS_SOURCE | nexus | branch |
| NEXUS_TARGET | nexus | branch |
| CENTRAL_GEM_LINK | central_gem | nexus |
| COMPATIBLE_WITH | construct | construct |
| TENSIONS_WITH | construct | construct |
| REQUIRES | construct | construct |
| EXCLUDES | construct | construct |
| GENERATES | construct | construct |
| RESOLVES | construct | construct |
