"""Stage 3 — Position Computer: coordinate IS the manifold position.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 3).

v2 greatly simplifies this stage. In the 12x12 grid model, positions ARE
the coordinates — no spectral embedding projection needed. The manifold
position is the dict of face -> (x, y) coordinates with their weights.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import ALL_FACES, PipelineState


class PositionComputer:
    """Stage 3: Package coordinate as manifold position (identity transform in v2)."""

    def execute(self, state: PipelineState):
        if state.coordinate is None:
            raise RuntimeError("Stage 3 requires coordinate from Stage 2")

        coord = state.coordinate
        per_face: dict[str, dict] = {}

        for face in ALL_FACES:
            entry = coord[face]
            construct_id = f"{face}.{entry['x']}_{entry['y']}"
            per_face[face] = {
                "primary": construct_id,
                "x": entry["x"],
                "y": entry["y"],
                "weight": entry["weight"],
            }

        state.manifold_position = {
            "per_face": per_face,
        }
