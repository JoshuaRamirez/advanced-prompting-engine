"""Spoke shape computation and central gem coherence.

Authoritative source: Spec 05 §11-12, Spec 08.
5 classifications: coherent, dominant, fragmented, moderate, weakly_integrated.
Empty spoke guard: returns strength=0, consistency=1.0 for empty gem list.
"""

from __future__ import annotations

import numpy as np

# Spoke thresholds (Spec 08, calibrated for 10-branch system)
SPOKE_THRESHOLDS = {
    "high_strength": 0.5,
    "high_consistency": 0.65,
    "high_contribution": 0.15,
    "low_strength": 0.25,
}


def compute_spoke_shape(gems: list[dict]) -> dict:
    """Compute the 4 spoke properties from gem magnitudes."""
    # Empty guard (numpy.mean([]) = nan)
    if len(gems) == 0:
        return {
            "strength": 0.0,
            "consistency": 1.0,
            "polarity": 0.0,
            "gems": [],
        }

    magnitudes = np.array([g["magnitude"] for g in gems])

    strength = float(np.mean(magnitudes))

    std = float(np.std(magnitudes))
    consistency = 1.0 - (std / max(strength, 1e-10))
    consistency = max(0.0, min(1.0, consistency))  # clamp to [0, 1]

    tension_count = sum(1 for g in gems if g["type"] == "conflicting")
    polarity = tension_count / max(len(gems), 1)

    return {
        "strength": strength,
        "consistency": consistency,
        "polarity": polarity,
        "gems": gems,
    }


def compute_contributions(spokes: dict[str, dict]) -> dict[str, dict]:
    """Add contribution property to each spoke."""
    total_strength = sum(s["strength"] for s in spokes.values())
    for spoke in spokes.values():
        spoke["contribution"] = spoke["strength"] / max(total_strength, 1e-10)
    return spokes


def classify_spoke(spoke: dict) -> str:
    """Classify spoke into one of 5 categories."""
    s = spoke["strength"]
    c = spoke["consistency"]
    p = spoke.get("contribution", 0.0)

    if s < SPOKE_THRESHOLDS["low_strength"]:
        return "weakly_integrated"
    if s >= SPOKE_THRESHOLDS["high_strength"] and c >= SPOKE_THRESHOLDS["high_consistency"]:
        return "coherent"
    if s >= SPOKE_THRESHOLDS["high_strength"] and p >= SPOKE_THRESHOLDS["high_contribution"]:
        return "dominant"
    if s >= SPOKE_THRESHOLDS["high_strength"] and c < SPOKE_THRESHOLDS["high_consistency"]:
        return "fragmented"
    return "moderate"


def compute_central_gem(spokes: dict[str, dict]) -> dict:
    """Aggregate all spoke contributions into central gem coherence."""
    contributions = [s.get("contribution", 0.0) for s in spokes.values()]
    consistencies = [s.get("consistency", 0.0) for s in spokes.values()]

    # Coherence = weighted mean of contributions weighted by consistency
    weighted_sum = sum(c * w for c, w in zip(contributions, consistencies))
    weight_total = sum(consistencies)
    coherence = weighted_sum / max(weight_total, 1e-10)

    return {
        "coherence": coherence,
        "classification": classify_coherence(coherence),
    }


def classify_coherence(coherence: float) -> str:
    """Classify central gem coherence. Thresholds deliberately low (max ~0.1)."""
    if coherence >= 0.08:
        return "highly_coherent"
    if coherence >= 0.05:
        return "moderately_coherent"
    if coherence >= 0.02:
        return "weakly_coherent"
    return "incoherent"
