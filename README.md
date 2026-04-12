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

## Example: Natural Language Intent

```
create_prompt_basis(intent="Design an ethical framework for autonomous vehicle decision-making")
```

The engine locates this intent across all 12 philosophical dimensions and returns:

```json
{
  "coordinate": {
    "epistemology":  {"x": 4, "y": 4, "weight": 0.76},
    "ontology":      {"x": 6, "y": 5, "weight": 0.73},
    "praxeology":    {"x": 7, "y": 4, "weight": 0.72},
    "heuristics":    {"x": 5, "y": 3, "weight": 0.66},
    "phenomenology": {"x": 7, "y": 4, "weight": 0.61},
    "ethics":        {"x": 6, "y": 4, "weight": 0.53},
    "...": "...all 12 faces with (x,y) position and relevance weight"
  },
  "harmonization": [
    {"pair": ["ontology", "praxeology"], "resonance": 0.15},
    {"pair": ["axiology", "ethics"],     "resonance": 0.05},
    "...6 complementary pairs with resonance scores"
  ],
  "spokes": {
    "ontology":      {"classification": "weakly_integrated", "strength": 0.042},
    "epistemology":  {"classification": "weakly_integrated", "strength": 0.039},
    "...": "...per-face behavioral signatures"
  },
  "central_gem": {"coherence": 0.69, "classification": "highly_coherent"},
  "construction_questions": {
    "ethics": {
      "template": "What moral obligations does this prompt impose or assume?",
      "position_summary": "balanced Deontological/Consequential + moderately Agent-focused",
      "meaning_mechanism": "composition",
      "phase": "evaluation"
    },
    "...": "...12 position-specific philosophical questions to guide prompt construction"
  }
}
```

The output tells you: this intent is primarily about knowledge validation (epistemology 0.76), what entities exist (ontology 0.73), and action structure (praxeology 0.72). Ethics registers at 0.53 — present but not dominant. The harmonization shows ontology and praxeology resonate strongly (0.15) — the theoretical "what exists" aligns with the practical "how to act."

## Example: Pre-formed Coordinate

For precise control, pass a coordinate directly:

```python
coordinate = {
    "ontology": {"x": 0, "y": 0, "weight": 1.0},      # corner: particular + static
    "ethics": {"x": 0, "y": 11, "weight": 0.9},         # corner: deontological + act
    "methodology": {"x": 0, "y": 0, "weight": 0.8},     # corner: analytic + deductive
    # ...all 12 faces with x (0-11), y (0-11), weight (0-1)
}
result = create_prompt_basis(coordinate=coordinate)
```

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
