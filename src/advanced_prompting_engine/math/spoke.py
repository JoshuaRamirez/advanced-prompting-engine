"""Spoke shape computation and central gem coherence.

Authoritative source: CONSTRUCT-v2.md §9.4-9.6, DESIGN.md.
5 classifications: coherent, dominant, fragmented, moderate, weakly_integrated.
12 spokes, 11 gems each. Empty spoke guard for edge cases.
"""

from __future__ import annotations

import numpy as np

# Spoke thresholds (calibrated for 12-face system)
SPOKE_THRESHOLDS = {
    "high_strength": 0.5,
    "high_consistency": 0.65,
    "high_contribution": 0.12,  # 1/12 baseline ≈ 0.083
    "low_strength": 0.25,
}


def compute_spoke_shape(gems: list[dict]) -> dict:
    """Compute the 4 spoke properties from gem magnitudes."""
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
    consistency = max(0.0, min(1.0, consistency))

    tension_count = sum(1 for g in gems if g.get("type") == "conflicting")
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
    """Aggregate all spoke contributions into central gem coherence.

    Coherence measures differentiation across spoke strengths via the
    coefficient of variation (CV = std / mean). Higher CV means the intent
    has clear dimensional preferences (some spokes strong, others weak).
    Low CV means all spokes are nearly identical (no differentiation).
    """
    strengths = np.array([s.get("strength", 0.0) for s in spokes.values()])

    if len(strengths) == 0 or np.mean(strengths) < 1e-10:
        return {
            "coherence": 0.0,
            "classification": "incoherent",
        }

    cv = float(np.std(strengths) / max(np.mean(strengths), 1e-10))

    return {
        "coherence": cv,
        "classification": classify_coherence(cv),
    }


def classify_coherence(cv: float) -> str:
    """Classify central gem coherence from coefficient of variation.

    Higher CV = more spoke differentiation = more coherent intent signal.
    """
    if cv >= 0.5:
        return "highly_coherent"
    if cv >= 0.3:
        return "moderately_coherent"
    if cv >= 0.1:
        return "weakly_coherent"
    return "incoherent"
