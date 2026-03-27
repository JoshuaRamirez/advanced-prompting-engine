# ADR-011: Nexus-Gem-Spoke Inter-Branch Architecture

**Date**: 2026-03-27
**Status**: Accepted

## Context

The original design connected branches via direct construct-to-construct edges. Cross-branch relationships were flat — an edge from one branch's construct to another branch's construct, with no mediating entity and no aggregation per branch.

The Construct specification defines a richer inter-branch architecture:
- **Nexi**: mediating loci between planes that receive, integrate, and give back
- **Gems**: the condensed results of nexus interactions
- **Spokes**: per-plane aggregations of all gems, forming behavioral signatures
- **Central gem**: system-wide convergence of all spokes
- **Two views**: network (pair-level, nexus-centric) and radial (branch-level, spoke-centric)

The question: should the engine adopt this architecture for cross-branch connections?

## Decision

**Yes.** Replace direct construct-to-construct cross-branch edges with the nexus-gem-spoke architecture.

### Nexi (90 nodes)

Each nexus is a **graph node** (not an edge) sitting in the subspace between two branches. There are 90 directional nexi — each plane has 9 outward connections, and each connection is unique (A→B is distinct from B→A because each plane contributes differently).

A nexus:
- Receives the 36 edge-point energies from both connected branches
- Computes an integration (the harmonic juxtaposition of both sets of extremes)
- Produces a gem (the resolved expression of the interaction)

### Gems (90 values)

A gem is the **computed output** of a nexus operation. It is:
- A resolved value with at minimum a magnitude (strength of integration)
- Storable, queryable, and reusable
- The entity that condenses into center points during recursive embedding
- Distinct from the nexus: the nexus is the locus, the gem is the product

### Spokes (10 profiles)

A spoke is the **complete set of one branch's 9 gems** plus the shared central gem. It is a behavioral signature — not just a set but a distribution with measurable shape:

| Property | Computation |
|---|---|
| Strength | Mean magnitude of the 9 gems |
| Consistency | 1 - normalized standard deviation across the 9 gem magnitudes |
| Polarity | Tension-flagged gem count / total gem count |
| Contribution | This spoke's aggregate / sum of all spokes' aggregates |

A spoke can be classified:
- High strength + high consistency = **coherent**
- High strength + low consistency = **fragmented**
- High strength + high contribution = **dominant**
- Low strength overall = **weakly integrated**

### Central Gem (1 value)

A single node connected to all 90 nexus nodes. Its value aggregates all 10 spoke contributions into a system-wide coherence score.

### Dual View

The same 90 nexi support two valid views:

| View | Unit | Question |
|---|---|---|
| Network | Nexus | What happens between these two branches? |
| Radial | Spoke | What is the total behavior of this branch across the system? |

Both are computed and returned in the construction basis.

## Rationale

- Nexi as nodes (not edges) have **identity** — they can carry properties, be queried, and participate in recursive embedding. Direct edges cannot.
- The gem/nexus distinction separates **process** (the locus of interaction) from **product** (the resolved expression). This enables the product to be reused without re-running the process.
- Spokes provide **per-branch system-level analysis** that the network view cannot naturally surface. A spoke reveals whether a branch is coherent, fragmented, dominant, or weakly integrated — none of which is visible from pairwise nexus results alone.
- The spoke is a **higher-order computation unit** — a computable object with measurable shape, not just a grouping. This unlocks per-plane scoring, cross-plane comparison, imbalance detection, and intentional central gem influence.
- The central gem provides a **single system-wide coherence metric** — answerable in one number whether the coordinate position is harmonious across all 10 branches.
- The dual view (network + radial) gives clients two complementary lenses on the same data.

## Consequences

- **Positive**: 90 nexus nodes give inter-branch connections identity, queryability, and reusability
- **Positive**: Gems as separate values enable recursive embedding without re-computation
- **Positive**: Spokes enable per-branch scoring, cross-branch comparison, and imbalance detection
- **Positive**: Central gem provides a single coherence metric for the entire coordinate
- **Positive**: Dual view serves both micro (pair) and macro (domain) analysis needs
- **Negative**: 90 additional nodes + 1 central gem node increase graph size and computation
- **Resolved**: The gem computation function is now formally defined in Spec 05 §10 (harmonic mean of weighted edge energy ratios, with active constructs receiving 2x potency boost)
- **Negative**: Spoke classification thresholds (what constitutes "coherent" vs "fragmented") must be calibrated empirically or by convention
- **Trade-off**: Architectural richness vs. computational complexity. The additional nodes and computations are bounded (90 nexi, 10 spokes, 1 central gem) and the math is simple (means, standard deviations, ratios). The richness of output justifies the complexity.
