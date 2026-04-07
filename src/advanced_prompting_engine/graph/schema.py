"""Graph schema definitions — node types, edge types, constants, and pipeline state.

Authoritative source: CONSTRUCT-v2.md (§3–§7, §4.3–§4.4).
Every other module imports from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Grid constant (CONSTRUCT-v2.md §5.1: each face is a 12 × 12 grid)
# ---------------------------------------------------------------------------

GRID_SIZE: int = 12


# ---------------------------------------------------------------------------
# Edge type constants
# ---------------------------------------------------------------------------

# Structural (canonical, auto-generated)
HAS_CONSTRUCT = "HAS_CONSTRUCT"
PRECEDES = "PRECEDES"
SPECTRUM_OPPOSITION = "SPECTRUM_OPPOSITION"
NEXUS_SOURCE = "NEXUS_SOURCE"
NEXUS_TARGET = "NEXUS_TARGET"
CENTRAL_GEM_LINK = "CENTRAL_GEM_LINK"

# Declared (user-authored extensions).
# Note: v2 uses positional correspondence (shared coordinate system via
# polarity convention) instead of declared cross-face edges for primary
# structural relationships. COMPATIBLE_WITH and TENSIONS_WITH are retained
# for user-authored extensions and backward compatibility only.
COMPATIBLE_WITH = "COMPATIBLE_WITH"
TENSIONS_WITH = "TENSIONS_WITH"
REQUIRES = "REQUIRES"
EXCLUDES = "EXCLUDES"
GENERATES = "GENERATES"
RESOLVES = "RESOLVES"

# Symmetric relations — stored as edges in both directions in NetworkX
SYMMETRIC_RELATIONS = frozenset({
    COMPATIBLE_WITH, TENSIONS_WITH, EXCLUDES, GENERATES, SPECTRUM_OPPOSITION,
})

# Edge weights for graph distance computation
EDGE_WEIGHTS: dict[str, float] = {
    COMPATIBLE_WITH: 0.2,
    TENSIONS_WITH: 0.8,
    SPECTRUM_OPPOSITION: 0.6,
    REQUIRES: 0.1,
    EXCLUDES: float("inf"),
    GENERATES: 0.3,
    RESOLVES: 0.2,
    HAS_CONSTRUCT: 0.0,
    PRECEDES: 0.0,
    NEXUS_SOURCE: 0.4,
    NEXUS_TARGET: 0.4,
    CENTRAL_GEM_LINK: 0.5,
}

# Contradiction map — proposed relation → list of contradicting existing relations
CONTRADICTION_MAP: dict[str, list[str]] = {
    COMPATIBLE_WITH: [TENSIONS_WITH, EXCLUDES],
    TENSIONS_WITH: [COMPATIBLE_WITH],
    REQUIRES: [EXCLUDES],
    EXCLUDES: [COMPATIBLE_WITH, REQUIRES],
    GENERATES: [],
    RESOLVES: [],
}


# ---------------------------------------------------------------------------
# Nexus tier classification (CONSTRUCT-v2.md §4.4)
# ---------------------------------------------------------------------------

class NexusTier(Enum):
    """Geometric relationship between two faces in the cube model.

    The cube model stratifies 66 unique nexi into three tiers based on
    the geometric relationship between the domains involved.
    """

    PAIRED = "paired"
    """Inside ↔ outside of same cube face (6 total).
    Complementary reflection — theoretical and practical aspects of the
    same concern."""

    ADJACENT = "adjacent"
    """Domains on different cube faces that share an edge (48 total).
    Proximal relationship — neighboring concerns."""

    OPPOSITE = "opposite"
    """Domains on opposite cube faces (12 total).
    Distal relationship — distant concerns."""


# ---------------------------------------------------------------------------
# Face definitions (CONSTRUCT-v2.md §7)
# ---------------------------------------------------------------------------

ALL_FACES: list[str] = [
    "ontology",
    "epistemology",
    "axiology",
    "teleology",
    "phenomenology",
    "ethics",
    "aesthetics",
    "praxeology",
    "methodology",
    "semiotics",
    "hermeneutics",
    "heuristics",
]

# Complementary pairs: each pair shares a cube face, with an inward
# (theoretical/comprehension) domain and an outward (applied/action) domain.
# (CONSTRUCT-v2.md §4.3)
CUBE_PAIRS: list[tuple[str, str]] = [
    ("ontology", "praxeology"),
    ("epistemology", "methodology"),
    ("axiology", "ethics"),
    ("teleology", "heuristics"),
    ("phenomenology", "aesthetics"),
    ("semiotics", "hermeneutics"),
]

# Sub-dimensions per face (CONSTRUCT-v2.md §7.3)
FACE_DEFINITIONS: dict[str, dict[str, str]] = {
    "ontology": {
        "x_axis_name": "Particular → Universal",
        "x_axis_low": "Particular",
        "x_axis_high": "Universal",
        "y_axis_name": "Static → Dynamic",
        "y_axis_low": "Static",
        "y_axis_high": "Dynamic",
        "core_question": "What entities and relationships fundamentally exist?",
        "construction_template": "What entities and relationships does this prompt assume exist?",
    },
    "epistemology": {
        "x_axis_name": "Empirical → Rational",
        "x_axis_low": "Empirical",
        "x_axis_high": "Rational",
        "y_axis_name": "Certain → Provisional",
        "y_axis_low": "Certain",
        "y_axis_high": "Provisional",
        "core_question": "How do we know domain states, events, and conditions are true or justified?",
        "construction_template": "How does this prompt establish and verify truth?",
    },
    "axiology": {
        "x_axis_name": "Absolute → Relative",
        "x_axis_low": "Absolute",
        "x_axis_high": "Relative",
        "y_axis_name": "Quantitative → Qualitative",
        "y_axis_low": "Quantitative",
        "y_axis_high": "Qualitative",
        "core_question": "By what criteria and standards is worth determined?",
        "construction_template": "What evaluative framework does this prompt apply, and how is it justified?",
    },
    "teleology": {
        "x_axis_name": "Immediate → Ultimate",
        "x_axis_low": "Immediate",
        "x_axis_high": "Ultimate",
        "y_axis_name": "Intentional → Emergent",
        "y_axis_low": "Intentional",
        "y_axis_high": "Emergent",
        "core_question": "What ultimate purposes do each domain, event, or interaction serve?",
        "construction_template": "What outcome is this prompt directed toward?",
    },
    "phenomenology": {
        "x_axis_name": "Objective → Subjective",
        "x_axis_low": "Objective",
        "x_axis_high": "Subjective",
        "y_axis_name": "Surface → Deep",
        "y_axis_low": "Surface",
        "y_axis_high": "Deep",
        "core_question": "How are experiences and interactions represented and realized?",
        "construction_template": "How is the user's experience represented in this prompt's output?",
    },
    "ethics": {
        "x_axis_name": "Deontological → Consequential",
        "x_axis_low": "Deontological",
        "x_axis_high": "Consequential",
        "y_axis_name": "Agent → Act",
        "y_axis_low": "Agent",
        "y_axis_high": "Act",
        "core_question": "What obligations, duties, and moral warrants govern right action?",
        "construction_template": "What moral obligations and permissibility conditions does this prompt impose or assume?",
    },
    "aesthetics": {
        "x_axis_name": "Autonomous → Contextual",
        "x_axis_low": "Autonomous",
        "x_axis_high": "Contextual",
        "y_axis_name": "Sensory → Conceptual",
        "y_axis_low": "Sensory",
        "y_axis_high": "Conceptual",
        "core_question": "What qualities of form, perception, and significance constitute aesthetic recognition?",
        "construction_template": "What aesthetic qualities does this prompt attend to, and through what mode of apprehension?",
    },
    "praxeology": {
        "x_axis_name": "Individual → Coordinated",
        "x_axis_low": "Individual",
        "x_axis_high": "Coordinated",
        "y_axis_name": "Reactive → Proactive",
        "y_axis_low": "Reactive",
        "y_axis_high": "Proactive",
        "core_question": "How are actions, behaviors, and intentions structured?",
        "construction_template": "What actions and behaviors does this prompt structure?",
    },
    "methodology": {
        "x_axis_name": "Analytic → Synthetic",
        "x_axis_low": "Analytic",
        "x_axis_high": "Synthetic",
        "y_axis_name": "Deductive → Inductive",
        "y_axis_low": "Deductive",
        "y_axis_high": "Inductive",
        "core_question": "What processes and methodologies govern construction and evolution?",
        "construction_template": "What method of reasoning or inquiry does this prompt employ?",
    },
    "semiotics": {
        "x_axis_name": "Explicit → Implicit",
        "x_axis_low": "Explicit",
        "x_axis_high": "Implicit",
        "y_axis_name": "Syntactic → Semantic",
        "y_axis_low": "Syntactic",
        "y_axis_high": "Semantic",
        "core_question": "How are signals, events, and data meaningfully communicated?",
        "construction_template": "How does this prompt signal and encode meaning?",
    },
    "hermeneutics": {
        "x_axis_name": "Literal → Figurative",
        "x_axis_low": "Literal",
        "x_axis_high": "Figurative",
        "y_axis_name": "Author-intent → Reader-response",
        "y_axis_low": "Author-intent",
        "y_axis_high": "Reader-response",
        "core_question": "What frameworks govern interpretation and understanding of events, signals, and gestures?",
        "construction_template": "How should ambiguity and interpretation be handled?",
    },
    "heuristics": {
        "x_axis_name": "Systematic → Intuitive",
        "x_axis_low": "Systematic",
        "x_axis_high": "Intuitive",
        "y_axis_name": "Conservative → Exploratory",
        "y_axis_low": "Conservative",
        "y_axis_high": "Exploratory",
        "core_question": "What practical strategies guide the handling of complexities and challenges?",
        "construction_template": "What strategies does this prompt use when facing the unknown?",
    },
}

# Phase assignment per face (CONSTRUCT-v2.md §4.3)
# Comprehension faces are inward (theoretical), evaluation and application
# faces are outward (applied/action).
FACE_PHASES: dict[str, str] = {
    "ontology": "comprehension",
    "epistemology": "comprehension",
    "axiology": "comprehension",
    "teleology": "comprehension",
    "phenomenology": "comprehension",
    "ethics": "evaluation",
    "aesthetics": "evaluation",
    "praxeology": "application",
    "methodology": "application",
    "semiotics": "application",
    "hermeneutics": "application",
    "heuristics": "application",
}

# Domain replacements for question parameterization (CONSTRUCT-v2.md §7)
DOMAIN_REPLACEMENTS: dict[str, str] = {
    "ontology": "ontological existence",
    "epistemology": "epistemological truth",
    "axiology": "axiological evaluation",
    "teleology": "teleological purpose",
    "phenomenology": "phenomenological experience",
    "ethics": "ethical obligation",
    "aesthetics": "aesthetic recognition",
    "praxeology": "praxeological action",
    "methodology": "methodological practice",
    "semiotics": "semiotic meaning",
    "hermeneutics": "hermeneutic interpretation",
    "heuristics": "heuristic strategy",
}


# ---------------------------------------------------------------------------
# Pipeline state (CONSTRUCT-v2.md — 8-stage forward pass)
# ---------------------------------------------------------------------------

@dataclass
class PipelineState:
    """Accumulating state passed through all 8 pipeline stages."""

    # Input
    raw_input: str | dict

    # Stage 1: Intent Parser
    partial_coordinate: dict | None = None

    # Stage 2: Coordinate Resolver
    coordinate: dict | None = None

    # Stage 3: Position Computer
    manifold_position: dict | None = None

    # Stage 4: Construct Resolver
    active_constructs: dict | None = None

    # Stage 5: Tension Analyzer
    tensions: dict | None = None

    # Stage 6: Nexus/Gem Analyzer
    gems: list | None = None
    nexus_details: list | None = None

    # Stage 6b: Harmonization (cube-pair coordinate correspondence)
    harmonization_pairs: list | None = None

    # Stage 7: Spoke Analyzer
    spokes: dict | None = None
    central_gem: dict | None = None

    # Stage 8: Construction Bridge
    construction_basis: dict | None = None
