# Advanced Prompting Engine

[![CI](https://github.com/JoshuaRamirez/advanced-prompting-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/JoshuaRamirez/advanced-prompting-engine/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/advanced-prompting-engine)](https://pypi.org/project/advanced-prompting-engine/)
[![Python](https://img.shields.io/pypi/pyversions/advanced-prompting-engine)](https://pypi.org/project/advanced-prompting-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A universal prompt creation engine delivered as an MCP server. Measures intent across 12 philosophical dimensions and returns a construction basis from which the client constructs prompts.

The engine does not generate prompts. It provides the dimensional foundation — active constructs, spectrum opposites, tensions, gems, spokes, harmonization pairs, and construction questions — that make prompt construction principled rather than heuristic.

## Quick Start

```bash
# Install
pip install advanced-prompting-engine

# Or run directly via uvx
uvx advanced-prompting-engine
```

### MCP Configuration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "advanced-prompting-engine": {
      "command": "uvx",
      "args": ["advanced-prompting-engine"]
    }
  }
}
```

## What It Does

The engine positions your intent in a 12-dimensional philosophical manifold:

| Face | Sub-dimensions | Phase |
|---|---|---|
| Ontology | Particular ↔ Universal, Static ↔ Dynamic | Comprehension |
| Epistemology | Empirical ↔ Rational, Certain ↔ Provisional | Comprehension |
| Axiology | Absolute ↔ Relative, Quantitative ↔ Qualitative | Comprehension |
| Teleology | Immediate ↔ Ultimate, Intentional ↔ Emergent | Comprehension |
| Phenomenology | Objective ↔ Subjective, Surface ↔ Deep | Comprehension |
| Ethics | Deontological ↔ Consequential, Agent ↔ Act | Evaluation |
| Aesthetics | Autonomous ↔ Contextual, Sensory ↔ Conceptual | Evaluation |
| Praxeology | Individual ↔ Coordinated, Reactive ↔ Proactive | Application |
| Methodology | Analytic ↔ Synthetic, Deductive ↔ Inductive | Application |
| Semiotics | Explicit ↔ Implicit, Syntactic ↔ Semantic | Application |
| Hermeneutics | Literal ↔ Figurative, Author-intent ↔ Reader-response | Application |
| Heuristics | Systematic ↔ Intuitive, Conservative ↔ Exploratory | Application |

Each face is a 12x12 grid of 144 epistemic observation points. Position determines classification (corner/midpoint/edge/center), potency, and spectrum membership. The 12 faces are organized as 6 complementary pairs (cube model) with harmonization through shared surfaces. The engine computes tensions via positional correspondence, gems (inter-face integrations) with cube tier modulation, spokes (per-face behavioral signatures), and a central gem coherence score.

## Tools

| Tool | Purpose |
|---|---|
| `create_prompt_basis` | Primary — intent or coordinate in, construction basis out |
| `explore_space` | Expert — graph traversal, stress testing, triangulation |
| `extend_schema` | Authoring — add constructs and relations with contradiction detection |

## Example

```python
# Pre-formed coordinate — place each face precisely
coordinate = {
    "ontology": {"x": 0, "y": 0, "weight": 1.0},      # corner: particular + static
    "epistemology": {"x": 1, "y": 0, "weight": 0.8},    # edge: empirical + certain
    "axiology": {"x": 5, "y": 5, "weight": 0.5},        # center: balanced evaluation
    "teleology": {"x": 8, "y": 0, "weight": 0.9},       # edge: near-ultimate + intentional
    "phenomenology": {"x": 5, "y": 5, "weight": 0.3},   # center: balanced experience
    "ethics": {"x": 0, "y": 11, "weight": 0.9},         # corner: deontological + act
    "aesthetics": {"x": 5, "y": 5, "weight": 0.2},      # center: balanced aesthetics
    "praxeology": {"x": 5, "y": 5, "weight": 0.3},      # center: balanced action
    "methodology": {"x": 0, "y": 0, "weight": 0.8},     # corner: analytic + deductive
    "semiotics": {"x": 5, "y": 5, "weight": 0.2},       # center: balanced semiotics
    "hermeneutics": {"x": 5, "y": 5, "weight": 0.2},    # center: balanced interpretation
    "heuristics": {"x": 5, "y": 5, "weight": 0.2},      # center: balanced strategy
}

# Returns: active constructs, spectrum opposites, tensions,
# gems, spokes, central gem, harmonization pairs, and 12 construction questions
result = create_prompt_basis(coordinate=coordinate)
```

The construction basis tells you what your prompt assumes exists (ontology), how it establishes truth (epistemology), by what standards it evaluates (axiology), what moral obligations it implies (ethics), what aesthetic qualities it attends to (aesthetics), and so on — each with a known opposite that defines what the prompt is NOT.

## Architecture

- **Stack:** Python + NetworkX (topology) + numpy (computation) + SQLite (persistence) + MCP SDK
- **Graph:** 1873 nodes, 2279 edges (12 faces × 144 constructs + 132 nexi + 1 central gem)
- **Pipeline:** 8 stages (Intent Parser → Coordinate Resolver → Position Computer → Construct Resolver → Tension Analyzer → Nexus/Gem Analyzer → Spoke Analyzer → Construction Bridge)
- **Geometry:** Vector Equilibrium (cuboctahedron) as latent inter-face topology, cube model for 6 complementary pairs
- **Deployment:** Single process, stdio transport, no daemon, no external dependencies

## Documentation

- `docs/DESIGN.md` — Full design specification
- `docs/CONSTRUCT-v2.md` — The Construct specification (what faces, points, spectrums, nexi, gems, spokes ARE)
- `docs/CONSTRUCT-v2-questions.md` — 144 construction question templates by zone
- `docs/adr/` — 12 Architecture Decision Records

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting instructions.

## License

MIT
