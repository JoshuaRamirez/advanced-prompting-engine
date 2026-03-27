# Spec 08 — Spoke and Central Gem

## Purpose

Defines spoke aggregation, classification thresholds, central gem coherence formula, and how these feed into the construction basis output.

---

## Spoke Aggregation

For each branch, gather all gems where that branch is the source:

```python
def aggregate_spoke(branch: str, all_gems: list[dict]) -> list[dict]:
    return [g for g in all_gems if g["nexus"].startswith(f"nexus.{branch}.")]
```

Each spoke has exactly 9 gems (one to each other branch) when all branches are active. When fewer branches are active, the spoke has fewer gems.

---

## Spoke Shape Computation

From Spec 05, Section 11:

```
strength     = mean(gem_magnitudes)
consistency  = 1 - std(gem_magnitudes) / max(mean, ε)    clamped to [0, 1]
polarity     = conflicting_gem_count / total_gem_count
contribution = sum(this_spoke_gems) / sum(all_spoke_gems)
```

---

## Classification Thresholds

These are fixed conventions, calibrated for a 10-branch system where balanced contribution = 0.1 per branch:

| Threshold | Value | Rationale |
|---|---|---|
| `HIGH_STRENGTH` | 0.5 | Above the midpoint of possible gem magnitude [0, 1] |
| `HIGH_CONSISTENCY` | 0.65 | Std dev is less than 35% of the mean |
| `HIGH_CONTRIBUTION` | 0.15 | 50% above the balanced share of 0.1 |
| `LOW_STRENGTH` | 0.25 | Below a quarter of maximum |

### Classification Rules

Applied in order — first match wins:

```python
def classify_spoke(spoke: dict) -> str:
    s = spoke["strength"]
    c = spoke["consistency"]
    p = spoke["contribution"]

    if s < LOW_STRENGTH:
        return "weakly_integrated"
    if s >= HIGH_STRENGTH and c >= HIGH_CONSISTENCY:
        return "coherent"
    if s >= HIGH_STRENGTH and p >= HIGH_CONTRIBUTION:
        return "dominant"
    if s >= HIGH_STRENGTH and c < HIGH_CONSISTENCY:
        return "fragmented"
    return "moderate"
```

**Note:** Added "moderate" classification for spokes that are above LOW_STRENGTH but below HIGH_STRENGTH — a middle ground not in the original 4-category scheme.

---

## Central Gem Coherence

### Formula

```python
def compute_central_gem(spokes: dict[str, dict]) -> dict:
    contributions = [s["contribution"] for s in spokes.values()]
    consistencies = [s["consistency"] for s in spokes.values()]

    # Coherence = sum of (contribution × consistency) for each spoke
    # Normalized by total consistency weight
    weighted_sum = sum(c * w for c, w in zip(contributions, consistencies))
    weight_total = sum(consistencies)
    coherence = weighted_sum / max(weight_total, 1e-10)

    return {"coherence": coherence, "classification": classify_coherence(coherence)}
```

### Rationale

- A spoke with high consistency contributes meaningfully to coherence
- A spoke with low consistency (fragmented) contributes less — it introduces noise
- A balanced system (all spokes equal contribution, all high consistency) produces maximum coherence
- A dominated system (one spoke contributing most, others weak) produces low coherence even if the dominant spoke is consistent

### Coherence Thresholds

| Range | Classification |
|---|---|
| ≥ 0.08 | highly_coherent |
| ≥ 0.05 | moderately_coherent |
| ≥ 0.02 | weakly_coherent |
| < 0.02 | incoherent |

**Note:** These thresholds are deliberately low because the coherence formula produces small values. With 10 spokes, each contributing ~0.1, weighted by consistency, the maximum coherence is ~0.1 (all spokes perfectly consistent and equally contributing). The thresholds are calibrated to this range.

---

## How Spokes Feed the Construction Bridge

The Construction Bridge (Stage 8) includes spoke data in each branch's construction question entry:

```python
construction_questions[branch] = {
    "template": ...,
    "active_question": ...,
    "opposite_question": ...,
    "classification": ...,
    "potency": ...,
    "spoke_profile": spoke.classification,   # "coherent", "fragmented", etc.
    "spoke_strength": spoke.strength,        # raw strength value
}
```

The spoke classification tells the client how this branch behaves across the system — not just what it contains internally, but how its interactions with other branches are distributed.

---

## Spoke-Level Influence on Central Gem

If a client adjusts one branch's coordinate (e.g., during `stress_test`):

1. That branch's active constructs change
2. Its 9 nexus gems change
3. Its spoke shape changes
4. Its contribution to the central gem changes
5. The central gem coherence shifts

This chain is the mechanism for intentional influence on system-wide coherence via individual branch adjustment.
