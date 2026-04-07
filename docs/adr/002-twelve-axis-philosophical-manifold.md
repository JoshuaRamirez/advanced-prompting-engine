# ADR-002: 12-Axis Philosophical Manifold

**Date**: 2026-04-03
**Status**: Accepted
**Supersedes**: ADR-002 (10-Axis Philosophical Manifold)

## Context

The original engine used 10 classical philosophical branches as its axiom layer. Analysis of the branch set revealed that Axiology (the study of value) was carrying triple duty: evaluative theory, moral judgment, and aesthetic judgment. Ethics and Aesthetics were implicit within Axiology rather than independently represented, compressing three distinct concerns into one axis.

Simultaneously, the organizing geometry (Tetractys) imposed a hierarchical triangular structure where some branches were structurally privileged over others. This contradicted the principle that no philosophical domain should have geometric priority.

The v2 Construct specification (`CONSTRUCT-v2.md`) addresses both problems: it expands the axiom layer from 10 to 12 domains and replaces the Tetractys with the Vector Equilibrium (cuboctahedron) as the organizing geometry.

## Decision

Use **12 philosophical domains** organized as faces of the Construct, arranged according to Vector Equilibrium geometry:

**Comprehension** (understanding the world):
1. Ontology — what entities and relationships fundamentally exist
2. Epistemology — how truth and justification are established
3. Axiology — by what criteria and standards worth is determined
4. Teleology — what ultimate purposes are served
5. Phenomenology — how experience is represented and realized

**Evaluation** (judging within the world):
6. Ethics — what obligations, duties, and moral warrants govern right action
7. Aesthetics — what qualities of form and significance constitute aesthetic recognition

**Application** (acting in the world):
8. Praxeology — how actions and intentions are structured
9. Methodology — what processes govern construction and evolution
10. Semiotics — how signals and data are meaningfully communicated
11. Hermeneutics — what frameworks govern interpretation and understanding
12. Heuristics — what practical strategies guide handling of complexity

### Organizing Geometry

The 12 domains are organized by three interlocking geometric models:

| Geometry | Role | What it describes |
|---|---|---|
| Cube (6 faces x inside/outside) | Pairing and harmonization | Which domains are complementary counterparts |
| Cuboctahedron (12 vertices) | Equipoise and connection | Equal structural weight, latent 3D positioning |
| Rhombic dodecahedron (12 faces) | Outer shell and tiling | Recursive embedding via space-filling |

### Cube Pairing Model

The 12 domains form 6 complementary pairs, each pair sharing a cube face with one domain facing inward (theoretical/comprehension) and one facing outward (applied/action):

| Cube Face | Inward (theoretical) | Outward (applied) | Shared concern |
|---|---|---|---|
| 1 | Ontology | Praxeology | Being <-> Doing |
| 2 | Epistemology | Methodology | Knowing <-> Proceeding |
| 3 | Axiology | Ethics | Valuing <-> Judging |
| 4 | Teleology | Heuristics | Purpose <-> Strategy |
| 5 | Phenomenology | Aesthetics | Experiencing <-> Recognizing form |
| 6 | Semiotics | Hermeneutics | Encoding <-> Decoding |

Paired faces share a surface: the same coordinate system, the same polarity convention, the same structural archetype at each position. Harmonization between paired faces arises from this shared surface, not from an imposed algorithm.

### Rhombic Dodecahedron as Outer Shell

The dual of the cuboctahedron. Each domain IS a face of the rhombic dodecahedron. The rhombic dodecahedron is space-filling (it tiles 3D with no gaps), providing the geometric basis for recursive embedding (Construct within Construct).

## Rationale

- Splitting Ethics and Aesthetics out of Axiology gives each its own 144-point grid, eliminating the overloading problem. Axiology is reframed as evaluative theory proper (criteria and standards of worth), no longer conflated with moral or aesthetic judgment.
- The Vector Equilibrium (cuboctahedron) is the only polyhedron where every vertex is equidistant from the center and from its neighbors. No domain is structurally privileged. This replaces the Tetractys hierarchy with genuine equipoise.
- The cube pairing model provides a principled basis for harmonization: paired faces are theoretical and practical reflections of the same concern, structurally tuned through shared coordinates.
- 12 vertices on the cuboctahedron = 12 domains. The geometry and the content match without forcing.
- The causal ordering (PRECEDES chain) expands naturally to include Ethics and Aesthetics as an evaluation phase between comprehension and application.

## Consequences

- **Positive**: No domain is geometrically privileged — the Vector Equilibrium enforces equipoise
- **Positive**: Ethics and Aesthetics are first-class domains with full 12x12 grids, not compressed sub-concerns of Axiology
- **Positive**: The cube pairing model provides principled harmonization between complementary domains
- **Positive**: The rhombic dodecahedron's space-filling property enables recursive embedding
- **Positive**: 1728 total constructs (12 faces x 144 points) provide finer-grained coverage than the prior 1000
- **Negative**: 12 axes increase coordinate object size from 10 entries to 12 — still manageable but larger
- **Negative**: The set remains fixed — adding a 13th domain is a breaking change requiring a different polyhedron
- **Negative**: Three geometric models (cube, cuboctahedron, rhombic dodecahedron) must be understood together — higher conceptual overhead than the single Tetractys
- **Trade-off**: The cuboctahedron is latent (it emerges from equal inter-face weighting, not computed in early pipeline stages). This simplifies implementation but means the 3D geometry is deferred.
- **Counts**: 1728 constructs, 66 unique nexi (132 directional participations), 132 gems, 12 spokes, 1 central gem
