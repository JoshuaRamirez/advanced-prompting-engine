"""Tests for foundation-precedence flag computation.

Covers the two check kinds (foundation_missing, triad_cascade) and the
no-flag case.
"""

from __future__ import annotations

import pytest

from advanced_prompting_engine.math.precedence import (
    compute_precedence_flags,
    FOUNDATION_FACES,
    EVALUATIVE_FACES,
    HIGH_THRESHOLD,
    LOW_THRESHOLD,
)


def _coord(**weights: float) -> dict:
    """Build a coordinate dict mapping face -> {weight: ...}."""
    all_faces = [
        "ontology", "epistemology", "axiology", "teleology",
        "phenomenology", "ethics", "aesthetics", "praxeology",
        "methodology", "semiotics", "hermeneutics", "heuristics",
    ]
    return {
        face: {"x": 5, "y": 5, "weight": weights.get(face, 0.3)}
        for face in all_faces
    }


class TestFoundationMissing:
    def test_ethics_dominant_no_foundation(self):
        coord = _coord(
            ethics=0.72, axiology=0.30, teleology=0.25,
            ontology=0.08, epistemology=0.09,
        )
        flags = compute_precedence_flags(coord)
        types = [f["type"] for f in flags]
        assert "foundation_missing" in types
        fm = next(f for f in flags if f["type"] == "foundation_missing" and f["face"] == "ethics")
        assert fm["activation"] == 0.72
        assert fm["foundations"]["ontology"] == 0.08
        assert "ontology" in fm["message"] and "epistemology" in fm["message"]

    def test_axiology_dominant_with_foundation_present_no_flag(self):
        coord = _coord(
            axiology=0.70, ontology=0.55, epistemology=0.25,
            ethics=0.50, teleology=0.40,
        )
        flags = compute_precedence_flags(coord)
        # Ontology at 0.55 is above LOW_THRESHOLD — no foundation_missing flag
        assert not any(f["type"] == "foundation_missing" for f in flags)

    def test_only_epistemology_present_no_flag(self):
        coord = _coord(
            ethics=0.60, axiology=0.30,
            ontology=0.10, epistemology=0.45,  # epistemology above threshold
        )
        flags = compute_precedence_flags(coord)
        assert not any(f["type"] == "foundation_missing" for f in flags)


class TestTriadCascade:
    def test_axiology_high_teleology_low(self):
        coord = _coord(
            axiology=0.70, ethics=0.40, teleology=0.10,
            ontology=0.55, epistemology=0.50,  # foundations present to isolate cascade check
        )
        flags = compute_precedence_flags(coord)
        cascade = [f for f in flags if f["type"] == "triad_cascade"]
        assert any(f["missing_upstream"] == "teleology" and f["dominant"] == "axiology" for f in cascade)

    def test_ethics_high_teleology_low(self):
        coord = _coord(
            axiology=0.30, ethics=0.65, teleology=0.10,
            ontology=0.55, epistemology=0.50,
        )
        flags = compute_precedence_flags(coord)
        cascade = [f for f in flags if f["type"] == "triad_cascade"]
        assert any(f["missing_upstream"] == "teleology" and f["dominant"] == "ethics" for f in cascade)

    def test_axiology_dominant_ethics_low_teleology_ok(self):
        coord = _coord(
            axiology=0.70, ethics=0.10, teleology=0.40,
            ontology=0.55, epistemology=0.50,
        )
        flags = compute_precedence_flags(coord)
        cascade = [f for f in flags if f["type"] == "triad_cascade"]
        assert any(f["missing_upstream"] == "ethics" and f["dominant"] == "axiology" for f in cascade)

    def test_triad_in_order_no_flag(self):
        # teleology > ethics > axiology — proper grounding
        coord = _coord(
            teleology=0.70, ethics=0.55, axiology=0.40,
            ontology=0.50, epistemology=0.45,
        )
        flags = compute_precedence_flags(coord)
        assert not any(f["type"] == "triad_cascade" for f in flags)


class TestNoFlagCases:
    def test_empty_coordinate(self):
        assert compute_precedence_flags({}) == []

    def test_all_mid_no_flags(self):
        coord = _coord()  # all at default 0.3
        assert compute_precedence_flags(coord) == []

    def test_engineering_prompt_pattern(self):
        # Engineering: semiotics/ontology/methodology dominant, ethics low,
        # teleology mid. No incoherence.
        coord = _coord(
            semiotics=0.70, ontology=0.65, methodology=0.60,
            ethics=0.15, axiology=0.25, teleology=0.35,
            epistemology=0.40,
        )
        assert compute_precedence_flags(coord) == []


class TestIntegrationWithPipeline:
    def test_ethics_heavy_prompt_surfaces_foundation_warning(self):
        """Field-observation scenario: ethics-heavy prompt with weak
        ontology/epistemology should produce a foundation_missing flag."""
        coord = _coord(
            ethics=0.70, axiology=0.30, teleology=0.28,
            ontology=0.10, epistemology=0.12,  # both below 0.2
            semiotics=0.25, hermeneutics=0.22,
        )
        flags = compute_precedence_flags(coord)
        # Expect at least the ethics foundation_missing flag
        ethics_fm = [f for f in flags if f.get("type") == "foundation_missing" and f.get("face") == "ethics"]
        assert len(ethics_fm) == 1
        assert "incoherent" in ethics_fm[0]["message"].lower()


class TestConstants:
    def test_foundation_faces_set(self):
        assert FOUNDATION_FACES == frozenset({"ontology", "epistemology"})

    def test_evaluative_faces_set(self):
        assert EVALUATIVE_FACES == frozenset({"axiology", "ethics", "teleology"})

    def test_thresholds_consistent_with_skill(self):
        # Skill uses Low<0.2, High>0.55 — these constants must match
        assert LOW_THRESHOLD == 0.2
        assert HIGH_THRESHOLD == 0.55
