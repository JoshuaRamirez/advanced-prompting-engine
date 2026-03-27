# ADR-012: Spoke as Computable Behavioral Signature

**Date**: 2026-03-27
**Status**: Accepted

## Context

ADR-011 introduces spokes as per-branch aggregations of gems. However, the spoke could be treated as either:

1. A passive grouping — just the 9 gems belonging to one branch, collected for convenience
2. An active computational unit — a distribution with measurable shape that produces its own classification and score

The Construct specification and subsequent analysis define the spoke as a **behavioral signature** — not a grouping but a distribution that reveals how one domain behaves across the entire system.

The question: should the spoke be a first-class computable output in the pipeline?

## Decision

**Yes.** The spoke is a **first-class computable object** with 4 measurable properties and a derived classification. It is computed per branch and returned in the construction basis output.

### The 4 Properties

| Property | What it measures | Formula |
|---|---|---|
| **Strength** | Overall magnitude of this branch's interactions | `mean(gem_magnitudes)` |
| **Consistency** | Uniformity of interaction quality | `1 - (std(gem_magnitudes) / max(mean(gem_magnitudes), epsilon))` |
| **Polarity** | Ratio of conflicting to harmonious interactions | `tension_flagged_gems / total_gems` |
| **Contribution** | This branch's share of system coherence | `sum(this_spoke_gems) / sum(all_spoke_gems)` |

### Derived Classification

| Condition | Classification |
|---|---|
| High strength + high consistency | **Coherent** — this branch integrates smoothly with the system |
| High strength + low consistency | **Fragmented** — this branch is strongly engaged but unevenly |
| High strength + high contribution | **Dominant** — this branch disproportionately drives system state |
| Low strength overall | **Weakly integrated** — this branch has minimal system participation |

### Output Format

```json
{
  "epistemology": {
    "spoke": {
      "strength": 0.73,
      "consistency": 0.81,
      "polarity": 0.22,
      "contribution": 0.12,
      "classification": "coherent",
      "gems": [
        { "target": "ontology", "magnitude": 0.8, "type": "harmonious" },
        { "target": "methodology", "magnitude": 0.9, "type": "harmonious" },
        { "target": "praxeology", "magnitude": 0.4, "type": "conflicting" }
      ]
    }
  }
}
```

## Rationale

- A passive grouping tells you what gems exist. A behavioral signature tells you what the **distribution means** — coherent, fragmented, dominant, or weakly integrated. This is the difference between data and insight.
- All 4 properties are mechanically computable from gem magnitudes using basic statistics (mean, standard deviation, ratio, sum). No LLM inference required.
- The spoke classification enables per-branch scoring that the construction basis output can include as a first-class element. A client receiving `"epistemology": { "classification": "fragmented" }` immediately knows this branch needs attention.
- Cross-spoke comparison becomes possible because all 10 spokes have identical structure (9 gems + 1 central). Questions like "which branch contributes most?" or "which branch introduces the most tension?" are answerable by comparing spoke properties.
- Spoke-level analysis enables **imbalance detection** — uneven interaction distributions, conflicting signals, weak integration — that nexus-level analysis cannot cleanly surface.
- Spoke profiles feed the central gem computation. Each spoke's contribution property determines its weight in the central gem aggregation. This makes the central gem's coherence score traceable to individual branch behaviors.
- Intentional influence becomes possible: adjust a branch's internal coordinate → observe spoke shape change → observe central gem shift. This is the mechanism for the Multi-Pass Orchestrator's stress testing at the spoke level.

## Consequences

- **Positive**: Per-branch behavioral signatures in the construction basis output — actionable, scorable, comparable
- **Positive**: Imbalance detection across branches — a construction-relevant signal unavailable from nexus-level analysis
- **Positive**: Central gem coherence becomes traceable to individual spoke contributions
- **Positive**: Cross-branch comparison by spoke properties enables systematic analysis of which branches dominate, conflict, or harmonize
- **Positive**: All computations are basic statistics — mean, std dev, ratio — no new mathematical dependencies
- **Negative**: Classification thresholds ("high strength" = what value?) need calibration — either empirical from graph analysis or by convention
- **Negative**: Adds 10 spoke computations (one per branch) to every pipeline run — bounded overhead (~10 mean/std calculations)
- **Trade-off**: The spoke is a derived, aggregate view — it abstracts away nexus-level detail. Clients who need pairwise detail must also consult the network view. The spoke complements but does not replace the nexus view.
