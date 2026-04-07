# Results: V2 Construct Rebuild

**Work Effort:** [WorkEffort-V2Rebuild.md](WorkEffort-V2Rebuild.md)

## Evidence Log

### 2026-04-03 — Specification Complete
- CONSTRUCT-v2.md: 15 sections, 18 core commitments, verified clean across 3 passes
- CONSTRUCT-v2-questions.md: 144 templates verified — all positions covered, no gaps, no duplicates, all parameterized
- Nexus counts verified: 6 paired + 48 adjacent + 12 opposite = 66

### 2026-04-03 — Obsolete Docs Cleaned
- Deleted: CONSTRUCT.md, CONSTRUCT-INTEGRATION.md, 12 spec files
- Recreated: ADR-002, ADR-009, ADR-010, DESIGN.md
- Updated: ADR-011, ADR-012

### 2026-04-04 — Data Layer Complete
- schema.py: `python3 -c` verified — 12 faces, 12 definitions, grid size 12, 6 cube pairs
- grid.py: `python3 -c` verified — correct classification (corner/midpoint/edge/center), 22 spectrums, degree labels, 12x12 potency matrix
- canonical.py: `python3 -c` verified — 144 questions, 66 nexus pairs, 1873 nodes, 2279 edges

### 2026-04-06 — Store Updated
- store.py: type constraint changed from 'branch' to 'face'

### 2026-04-06 — Graph Access, Caches, Math, Pipeline, Server Complete
- query.py + mutation.py: rewritten, imports verified
- embedding.py + centrality.py: stubbed (unnecessary in v2)
- tfidf.py: updated branch→face
- Math: 5 modules deleted, tension/gem rewritten (positional), spoke updated, harmonization.py created
- Pipeline: all 8 stages + runner rewritten, imports verified
- Server: updated for 12 faces, removed centrality, v2 prompts/resources
- Tools: face terminology, backwards-compat aliases
- Orchestrator: face terminology, GRID_SIZE

### 2026-04-06 — Tests Complete
- 194 tests passed, 0 failures, 3.13s
- 5 obsolete test files deleted, 11 rewritten, 1 new (test_harmonization.py), 2 kept as-is

### 2026-04-06 — Integration Complete
- End-to-end pipeline: intent → 12 faces × coordinates → constructs → tensions (569.47) → 132 gems → 12 spokes → central gem (highly_coherent, 0.083) → 6 harmonization pairs → construction questions
- All counts match spec: 1873 nodes, 2279 edges, 12 faces, 132 gems, 6 pairs
- Observation: spoke strengths uniform at 0.0794 — gem computation needs calibration for face-specific differentiation

### 2026-04-06 — Audit + Fixes Complete
- 13 issues found (3 critical, 5 moderate, 5 minor), all fixed
- Critical fixes: compact output key corrected, construct resolver now uses face weights (variable activation radius + effective_potency), gem magnitude now incorporates positional correspondence
- Moderate fixes: NexusTier type consistency (string keys), degree vocabulary unified (grid.degree_label replaces _interpret_axis), harmonization made bidirectional, central gem uses CV for differentiation, meaning_mechanism added to output
- Minor fixes: deprecated branch aliases documented, FACE_PHASES constant added
- 195 tests passed after fixes
- Integration re-verified: Ethics (0.574) and Methodology (0.739) correctly dominate for "ethical decision-making" intent. Spokes differentiate (3x strength). Central gem coherence 0.55 (highly_coherent). Harmonization alignment varies by activation pattern.
