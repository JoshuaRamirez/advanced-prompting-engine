# Advanced Prompting Engine

[![CI](https://github.com/JoshuaRamirez/advanced-prompting-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/JoshuaRamirez/advanced-prompting-engine/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/advanced-prompting-engine)](https://pypi.org/project/advanced-prompting-engine/)
[![Python](https://img.shields.io/pypi/pyversions/advanced-prompting-engine)](https://pypi.org/project/advanced-prompting-engine/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A universal prompt creation engine delivered as an MCP server. Measures intent across 10 philosophical dimensions and returns a construction basis from which the client constructs prompts.

The engine does not generate prompts. It provides the dimensional foundation — active constructs, spectrum opposites, tensions, gems, spokes, and construction questions — that make prompt construction principled rather than heuristic.

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

The engine positions your intent in a 10-dimensional philosophical manifold:

| Branch | Sub-dimensions |
|---|---|
| Ontology | Particular ↔ Universal, Static ↔ Dynamic |
| Epistemology | Empirical ↔ Rational, Certain ↔ Provisional |
| Axiology | Intrinsic ↔ Instrumental, Individual ↔ Collective |
| Teleology | Immediate ↔ Ultimate, Intentional ↔ Emergent |
| Phenomenology | Objective ↔ Subjective, Surface ↔ Deep |
| Praxeology | Individual ↔ Coordinated, Reactive ↔ Proactive |
| Methodology | Analytic ↔ Synthetic, Deductive ↔ Inductive |
| Semiotics | Explicit ↔ Implicit, Syntactic ↔ Semantic |
| Hermeneutics | Literal ↔ Figurative, Author-intent ↔ Reader-response |
| Heuristics | Systematic ↔ Intuitive, Conservative ↔ Exploratory |

Each branch is a 10x10 grid of 100 epistemic observation points. Position determines classification (corner/midpoint/edge/center), potency, and spectrum membership. The engine computes tensions, gems (inter-branch integrations), spokes (per-branch behavioral signatures), and a central gem coherence score.

## Tools

| Tool | Purpose |
|---|---|
| `create_prompt_basis` | Primary — intent or coordinate in, construction basis out |
| `explore_space` | Expert — graph traversal, stress testing, triangulation |
| `extend_schema` | Authoring — add constructs and relations with contradiction detection |

## Example

```python
# Pre-formed coordinate — place each branch precisely
coordinate = {
    "ontology": {"x": 0, "y": 0, "weight": 1.0},      # corner: particular + static
    "epistemology": {"x": 1, "y": 0, "weight": 0.8},    # edge: empirical + certain
    "methodology": {"x": 0, "y": 0, "weight": 0.8},     # corner: analytic + deductive
    "teleology": {"x": 8, "y": 0, "weight": 0.9},       # edge: near-ultimate + intentional
    # ... all 10 branches
}

# Returns: active constructs, spectrum opposites, tensions,
# gems, spokes, central gem, and 10 construction questions
result = create_prompt_basis(coordinate=coordinate)
```

The construction basis tells you what your prompt assumes exists (ontology), how it establishes truth (epistemology), what it values (axiology), what it's directed toward (teleology), and so on — each with a known opposite that defines what the prompt is NOT.

## Architecture

- **Stack:** Python + NetworkX + numpy + SQLite + MCP SDK
- **Graph:** 1101 nodes, 1629 edges (10 branches × 100 constructs + 90 nexi + 1 central gem)
- **Pipeline:** 8 stages (Intent Parser → Coordinate Resolver → Position Computer → Construct Resolver → Tension Analyzer → Nexus/Gem Analyzer → Spoke Analyzer → Construction Bridge)
- **Deployment:** Single process, stdio transport, no daemon, no external dependencies

## Documentation

- `docs/DESIGN.md` — Full design specification
- `docs/CONSTRUCT.md` — The Construct specification (what planes, points, spectrums, nexi, gems, spokes ARE)
- `docs/CONSTRUCT-INTEGRATION.md` — How Construct elements map to engine components
- `docs/adr/` — 12 Architecture Decision Records
- `docs/specs/` — 12 implementation specifications

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
