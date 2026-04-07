# ADR-011: Nexus-Gem-Spoke Inter-Face Architecture

**Date**: 2026-03-27
**Status**: Accepted

## Context

The original design connected faces via direct construct-to-construct edges. Cross-face relationships were flat — an edge from one face's construct to another face's construct, with no mediating entity and no aggregation per face.

The Construct specification defines a richer inter-face architecture:
- **Nexi**: mediating loci between planes that receive, integrate, and give back
- **Gems**: the condensed results of nexus interactions
- **Spokes**: per-plane aggregations of all gems, forming behavioral signatures
- **Central gem**: system-wide convergence of all spokes
- **Two views**: network (pair-level, nexus-centric) and radial (face-level, spoke-centric)

The question: should the engine adopt this architecture for cross-face connections?

## Decision

**Yes.** Replace direct construct-to-construct cross-face edges with the nexus-gem-spoke architecture.

### Nexi (132 nodes)

Each nexus is a **graph node** (not an edge) sitting in the subspace between two faces. There are 132 directional nexi — each plane has 11 outward connections, and each connection is unique (A→B is distinct from B→A because each plane contributes differently).

The 66 unique nexi are stratified via the cube model into three tiers based on geometric relationship:

| Tier | Count | Relationship |
|---|---|---|
| Paired | 6 | Opposite faces of the cube — maximal contrast |
| Adjacent | 48 | Faces sharing a cube edge — moderate proximity |
| Opposite | 12 | Faces sharing a cube vertex — diagonal relation |
| **Total** | **66** | |

A nexus:
- Receives the 36 edge-point energies from both connected faces
- Computes an integration (the harmonic juxtaposition of both sets of extremes)
- Produces a gem (the resolved expression of the interaction)

### Gems (132 values)

A gem is the **computed output** of a nexus operation. It is:
- A resolved value with at minimum a magnitude (strength of integration)
- Storable, queryable, and reusable
- The entity that condenses into center points during recursive embedding
- Distinct from the nexus: the nexus is the locus, the gem is the product

### Spokes (12 profiles)

A spoke is the **complete set of one face's 11 gems** plus the shared central gem. It is a behavioral signature — not just a set but a distribution with measurable shape:

| Property | Computation |
|---|---|
| Strength | Mean magnitude of the 11 gems |
| Consistency | 1 - normalized standard deviation across the 11 gem magnitudes |
| Polarity | Tension-flagged gem count / total gem count |
| Contribution | This spoke's aggregate / sum of all spokes' aggregates |

A spoke can be classified:
- High strength + high consistency = **coherent**
- High strength + low consistency = **fragmented**
- High strength + high contribution = **dominant**
- Low strength overall = **weakly integrated**

### Central Gem (1 value)

A single node connected to all 132 nexus nodes. Its value aggregates all 12 spoke contributions into a system-wide coherence score.

### Dual View

The same 132 nexi support two valid views:

| View | Unit | Question |
|---|---|---|
| Network | Nexus | What happens between these two faces? |
| Radial | Spoke | What is the total behavior of this face across the system? |

Both are computed and returned in the construction basis.

## Rationale

- Nexi as nodes (not edges) have **identity** — they can carry properties, be queried, and participate in recursive embedding. Direct edges cannot.
- The gem/nexus distinction separates **process** (the locus of interaction) from **product** (the resolved expression). This enables the product to be reused without re-running the process.
- Spokes provide **per-face system-level analysis** that the network view cannot naturally surface. A spoke reveals whether a face is coherent, fragmented, dominant, or weakly integrated — none of which is visible from pairwise nexus results alone.
- The spoke is a **higher-order computation unit** — a computable object with measurable shape, not just a grouping. This unlocks per-plane scoring, cross-plane comparison, imbalance detection, and intentional central gem influence.
- The central gem provides a **single system-wide coherence metric** — answerable in one number whether the coordinate position is harmonious across all 12 faces.
- The dual view (network + radial) gives clients two complementary lenses on the same data.
- Nexus stratification via the cube model provides structural meaning to each nexus tier — paired nexi carry maximal contrast, adjacent nexi carry moderate proximity, opposite nexi carry diagonal relation — enabling tier-aware weighting in gem and spoke computations.

## Consequences

- **Positive**: 132 nexus nodes give inter-face connections identity, queryability, and reusability
- **Positive**: Gems as separate values enable recursive embedding without re-computation
- **Positive**: Spokes enable per-face scoring, cross-face comparison, and imbalance detection
- **Positive**: Central gem provides a single coherence metric for the entire coordinate
- **Positive**: Dual view serves both micro (pair) and macro (domain) analysis needs
- **Positive**: Nexus stratification (6 paired + 48 adjacent + 12 opposite) provides tier-aware structure for weighting and analysis
- **Negative**: 132 additional nodes + 1 central gem node increase graph size and computation
- **Resolved**: The gem computation function is now formally defined in Spec 05 §10 (harmonic mean of weighted edge energy ratios, with active constructs receiving 2x potency boost)
- **Negative**: Spoke classification thresholds (what constitutes "coherent" vs "fragmented") must be calibrated empirically or by convention
- **Trade-off**: Architectural richness vs. computational complexity. The additional nodes and computations are bounded (132 nexi, 12 spokes, 1 central gem) and the math is simple (means, standard deviations, ratios). The richness of output justifies the complexity.
