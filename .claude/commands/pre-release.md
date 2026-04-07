# Pre-Release Check

Run a comprehensive pre-release validation for the advanced-prompting-engine package. This checks everything needed before creating a GitHub release.

## Steps

### 1. Version Consistency
Check that the version matches across all locations:
- `pyproject.toml` → `version`
- `src/advanced_prompting_engine/__init__.py` → `__version__`
- `CHANGELOG.md` → has a section for this version
- `CHANGELOG.md` → has a comparison link for this version

Report any mismatches as blockers.

### 2. Test Suite
Run `python3 -m pytest tests/ -v --tb=short` and report the result. Any failure is a blocker.

### 3. Build Verification
Run `python3 -m build` to verify the package builds into a wheel and sdist. Report sizes. Any build failure is a blocker.

### 4. Import Chain
Run `python3 -c "from advanced_prompting_engine.server import create_server; print('OK')"` to verify the full import chain.

### 5. Content Audit
Check these files for stale references that don't match the current version:
- `README.md` — node/edge counts, face/branch terminology, dimension count, grid sizes, doc references
- `CLAUDE.md` — same checks
- `pyproject.toml` description

Flag any stale content as a warning.

### 6. Git State
- Run `git status` — working tree must be clean
- Run `git log --oneline -5` — show recent commits
- Check if branch is ahead of origin (unpushed commits)

### 7. Dependency Check
- Verify no imports of deleted modules exist in any `.py` file under `src/`
- Check for stale `__pycache__` files for deleted modules

### 8. Integration Smoke Test
Run a quick end-to-end test:
```python
import tempfile, os, networkx as nx
from advanced_prompting_engine.graph.canonical import build_canonical_graph
from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.pipeline.runner import PipelineRunner

nodes, edges = build_canonical_graph()
G = nx.DiGraph()
for n in nodes: G.add_node(n['id'], **n)
for e in edges: G.add_edge(e['source_id'], e['target_id'], **e)
ec = EmbeddingCache(); ec.initialize(G)
tc = TfidfCache(); tc.initialize(G)
pipeline = PipelineRunner(G, GraphQueryLayer(G), ec, tc)
result = pipeline.run("Test intent for release validation")
```
Verify the result has: coordinate (12 faces), active_constructs, tensions, gems (132), spokes (12), central_gem, harmonization_pairs (6), construction_questions (12).

### 9. Summary
Report a table:
| Check | Status |
|---|---|
| Version consistency | PASS/FAIL |
| Tests | PASS/FAIL (count) |
| Build | PASS/FAIL |
| Import chain | PASS/FAIL |
| Content audit | PASS/WARN/FAIL |
| Git state | PASS/WARN |
| Dependencies | PASS/FAIL |
| Integration | PASS/FAIL |

State clearly: **READY FOR RELEASE** or **NOT READY** with blockers listed.
