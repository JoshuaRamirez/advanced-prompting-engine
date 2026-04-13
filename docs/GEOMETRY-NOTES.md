# Geometric Properties of the Construct

This document records structural properties of the 12-face Construct that arise from its design decisions. These properties are not imposed — they emerge from the choice of 12 domains and the cube pairing model. They represent latent geometric capacity that future versions may exploit.

## Derived Numbers

| Value | Derivation | Role in current system |
|---|---|---|
| 12 | Number of philosophical domains | Faces, spokes, vertices of organizing polyhedron |
| 144 | 12 × 12 grid per face | Points per face, construction questions per face |
| 1728 | 12 × 144 | Total constructs (observation points across the manifold) |
| 66 | C(12,2) | Unique face pairs (nexi) |
| 132 | 12 × 11 | Directional nexus participations (gems) |
| 6 | 12 / 2 | Complementary pairs (cube faces) |
| 48 | 12 × 4 | Corners (structural anchors, 4 groups of 12) |
| 24 | 12 × 2 | Sub-dimensional extremes (axis endpoints) |
| 22 | Edge-to-edge reflections on 12×12 grid | Spectrums per face |
| 264 | 22 × 12 | Total spectrums across the Construct |

## Polyhedral Relationships

The Construct's inter-face topology involves three nested geometric structures. Each describes the same 12-domain system from a different perspective.

### The Cube (explicit)

The 6 complementary pairs are the 6 faces of a cube. Each cube face has an inward (theoretical) and outward (applied) domain:

- Ontology ↔ Praxeology (Being ↔ Doing)
- Epistemology ↔ Methodology (Knowing ↔ Proceeding)
- Axiology ↔ Ethics (Valuing ↔ Judging)
- Teleology ↔ Heuristics (Purpose ↔ Strategy)
- Phenomenology ↔ Aesthetics (Experiencing ↔ Recognizing form)
- Semiotics ↔ Hermeneutics (Encoding ↔ Decoding)

The cube produces the nexus stratification: paired (same face), adjacent (sharing an edge), opposite (across the cube).

Properties of the cube relevant to future development:
- 6 faces, 8 vertices, 12 edges
- Each vertex is the meeting point of 3 cube faces (3 complementary pairs)
- The 8 vertices represent 8 unique triads of paired concerns
- The 12 edges connect pairs that share one cube face — these are the "adjacent" nexi at the structural level

### The Cuboctahedron (latent)

The cuboctahedron has exactly 12 vertices — one per domain. It is the shape formed when all vertices are equidistant from a center point and from their neighbors. It emerges naturally from the equal-weight commitment (no face is privileged).

Properties available but not currently computed:
- 12 vertices, 24 edges, 14 faces (8 triangular + 6 square)
- Each vertex has exactly 4 neighbors — each domain has 4 primary geometric connections
- The 24 edges correspond to the 24 sub-dimensional extremes (12 faces × 2 axes)
- The 8 triangular faces define 8 triads of mutually adjacent domains
- The 6 square faces define 6 quartets of domains forming cycles
- The cuboctahedron is the intersection of a cube and its dual (the octahedron)

The cuboctahedron's 4-neighbor structure could provide a geometric basis for determining which 4 faces are each face's primary connections — beyond what the cube stratification currently defines.

### The Rhombic Dodecahedron (latent)

The dual of the cuboctahedron. Each vertex of the cuboctahedron corresponds to a face of the rhombic dodecahedron.

- 12 rhombic faces — each domain IS a face of this solid
- 14 vertices — correspond to the cuboctahedron's 14 faces (8 triad-points + 6 quartet-points)
- 24 edges — shared with the cuboctahedron's edge count

Key property: **the rhombic dodecahedron tiles 3D space with no gaps.** Copies of it pack perfectly. This provides the geometric basis for recursive embedding — a Construct can nest inside a larger tessellation of the same shape.

### The Octahedron (implicit)

The dual of the cube. Where the cube has 6 faces, the octahedron has 6 vertices. The 6 complementary pairs can be described equivalently as the 6 vertices of an octahedron. The cube and octahedron are two views of the same pairing structure.

Properties:
- 6 vertices (one per complementary pair), 8 faces, 12 edges
- Each face of the octahedron is a triangle connecting 3 pairs
- The 8 octahedral faces correspond to the 8 cube vertices — groups of 3 pairs that share a structural meeting point

## Structural Capacities Not Yet Used

### Vertex triads (8 groups of 3 pairs)

The cube has 8 vertices. Each vertex is where 3 cube faces meet — meaning 3 complementary pairs converge. These 8 convergence points define natural groupings:

Each triad contains 6 domains (3 theoretical + 3 applied) that share a structural meeting point. These groupings could define higher-order interaction zones — regions of the manifold where 3 pairs simultaneously resonate.

### Edge quartets (12 groups of 4 domains)

The cube has 12 edges. Each edge connects 2 vertices. The 4 domains on the 2 cube faces sharing that edge form a quartet — 2 theoretical + 2 applied domains with a specific geometric relationship. These quartets are intermediate between pairs and the full manifold.

### Recursive embedding via space-filling

The rhombic dodecahedron's space-filling property means the Construct can be treated as a tile in a larger structure. Multiple Constructs — perhaps representing different levels of abstraction, different domains of application, or different temporal states — could tile together with no gaps. The connection points between tiles are the vertices and edges of the rhombic dodecahedron.

### 4-neighbor topology from the cuboctahedron

Each domain has 4 primary geometric neighbors in the cuboctahedron. This is a stronger topological constraint than the cube stratification (which gives 1 paired + 8 adjacent + 2 opposite = 11 connections of 3 types). The 4-neighbor structure could define a primary interaction network where propagation, influence, or resonance follows cuboctahedral edges rather than all 66 nexi equally.

### Triangular and square face groupings

The cuboctahedron's 14 faces (8 triangles + 6 squares) partition the 12 domains into overlapping groups:
- Each triangle contains 3 mutually adjacent domains — a natural triad for three-way interaction
- Each square contains 4 domains forming a cycle — a natural quartet for circular influence

These groupings are available for any future feature that needs to reason about domain clusters smaller than the full manifold but larger than pairs.

## Dimensional Staging

The Construct is built in stages:

1. **2D**: Each face is a flat 12×12 grid. All current computation happens here.
2. **2D-in-3D**: The 12 flat faces positioned and oriented in 3D space according to the cuboctahedral/rhombic dodecahedral geometry. Faces have position and angle but no depth. The skeletal connections (nexi) run between faces through 3D space.
3. **3D**: The flat faces extruded into volumetric meaning. The skeleton becomes a solid.

The current system implements stage 1 fully and stage 2 implicitly (through the cube model's nexus stratification). Stage 3 and the full cuboctahedral positioning are deferred.
