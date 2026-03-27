# ADR-009: Grid-Structured Schema Layer

**Date**: 2026-03-27
**Status**: Accepted
**Supersedes**: Portions of ADR-002 (construct count was open; now fixed)

## Context

The original Schema Layer (Level 2) stored constructs as flat lists of variable length per branch. Construct identity was a name string (`branch.construct_name`). Position within a branch carried no structural meaning — constructs were unordered.

The Construct specification (see `CONSTRUCT.md`) defines a 10x10 grid per plane where position determines role, potency, and relationships. This introduces a fundamentally richer internal geometry for each branch.

The question: should the Schema Layer adopt this grid structure?

## Decision

Replace flat construct lists with **10x10 grids**. Each branch contains exactly **100 constructs** arranged in a grid addressed by (x, y) coordinates. Position determines classification, potency, and spectrum membership.

### Point Classification

| Classification | Positions | Count | Potency |
|---|---|---|---|
| Corner | (0,0), (9,0), (0,9), (9,9) | 4 | 1.0 |
| Midpoint | (4,0), (9,4), (4,9), (0,4) | 4 | 0.95 |
| Edge (remaining) | All other perimeter positions | 28 | 0.85 |
| Center | All interior positions | 64 | 0.5 |

### Sub-Dimensions

Each branch's grid has two named sub-axes (x and y), representing two fundamental tensions internal to that philosophical discipline. These are defined per branch in `CONSTRUCT-INTEGRATION.md`.

### Coordinate Object

The coordinate position changes from a construct name to grid coordinates:

```json
{ "epistemology": { "x": 3, "y": 0, "weight": 0.8 } }
```

### Construct Identity

Node ID changes from `branch.construct_name` to `branch.x_y` (e.g., `epistemology.3_0`).

## Rationale

- Position carries structural meaning — classification, potency, spectrum membership, sub-dimensional semantics. Flat lists discard this entirely.
- Fixed cardinality (100 per branch, 1000 total) makes all branches isomorphic in structure, enabling cross-branch geometric comparison.
- The 36/64 edge/center split provides a built-in potency gradient that shapes tension and generative computation without additional configuration.
- 200 spectrums (20 per branch) are auto-generated from grid geometry — no manual edge authoring needed for these.
- Two sub-dimensions per branch expand each branch from a single axis to a 2D field, increasing the expressiveness of each coordinate position from 1 degree of freedom to 2.
- Grid positions enable the Construct's edge encapsulation property: edges define the bounds of what the center can resolve.

## Consequences

- **Positive**: Every construct carries structural semantics from its position — no additional metadata needed
- **Positive**: Cross-branch comparison becomes geometric — same position on two branches is structurally equivalent
- **Positive**: 200 spectrums exist for free from grid geometry
- **Positive**: Potency gradient shapes computation without configuration
- **Negative**: Fixed at 100 per branch — adding a 101st construct to a branch is not possible without extending the grid (e.g., 11x10), which breaks isomorphism
- **Negative**: The 100 questions per branch must be authored to match the structural role of their grid position — corner constructs must be corner-worthy concepts
- **Negative**: Node ID changes from human-readable names to coordinate-based IDs (`epistemology.3_0` vs `epistemology.empirical_verification`) — less self-documenting at the ID level
- **Trade-off**: Structural richness vs. authoring constraint. Every position demands content that matches its structural role. This is intentional — the structure IS the authoring specification.
