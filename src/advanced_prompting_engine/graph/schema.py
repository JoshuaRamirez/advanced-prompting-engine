"""Graph schema definitions — node types, edge types, constants, and pipeline state.

Authoritative source: Spec 01 (graph-schema.md), CONSTRUCT-INTEGRATION.md.
Every other module imports from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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

# Declared (canonical or user-authored)
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

# Edge weights for graph distance computation (Spec 05 §4)
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

# Contradiction map (Spec 12) — proposed relation → list of contradicting existing relations
CONTRADICTION_MAP: dict[str, list[str]] = {
    COMPATIBLE_WITH: [TENSIONS_WITH, EXCLUDES],
    TENSIONS_WITH: [COMPATIBLE_WITH],
    REQUIRES: [EXCLUDES],
    EXCLUDES: [COMPATIBLE_WITH, REQUIRES],
    GENERATES: [],
    RESOLVES: [],
}


# ---------------------------------------------------------------------------
# Branch definitions
# ---------------------------------------------------------------------------

ALL_BRANCHES: list[str] = [
    "ontology",
    "epistemology",
    "axiology",
    "teleology",
    "phenomenology",
    "praxeology",
    "methodology",
    "semiotics",
    "hermeneutics",
    "heuristics",
]

# Sub-dimensions per branch (CONSTRUCT-INTEGRATION.md)
BRANCH_DEFINITIONS: dict[str, dict[str, str]] = {
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
        "x_axis_name": "Intrinsic → Instrumental",
        "x_axis_low": "Intrinsic",
        "x_axis_high": "Instrumental",
        "y_axis_name": "Individual → Collective",
        "y_axis_low": "Individual",
        "y_axis_high": "Collective",
        "core_question": "What is the value inherent in each choice?",
        "construction_template": "What does this prompt value, and by what criteria does it evaluate?",
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

# Domain replacements for question parameterization (Spec 03)
DOMAIN_REPLACEMENTS: dict[str, str] = {
    "ontology": "ontological existence",
    "epistemology": "epistemological truth",
    "axiology": "axiological value",
    "teleology": "teleological purpose",
    "phenomenology": "phenomenological experience",
    "praxeology": "praxeological action",
    "methodology": "methodological practice",
    "semiotics": "semiotic meaning",
    "hermeneutics": "hermeneutic interpretation",
    "heuristics": "heuristic strategy",
}


# ---------------------------------------------------------------------------
# Pipeline state (Spec 06)
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

    # Stage 7: Spoke Analyzer
    spokes: dict | None = None
    central_gem: dict | None = None

    # Stage 8: Construction Bridge
    construction_basis: dict | None = None
