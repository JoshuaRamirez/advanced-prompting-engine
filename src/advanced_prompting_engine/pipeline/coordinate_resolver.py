"""Stage 2 — Coordinate Resolver: fill null faces via grid clamping.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 2).

v2 replaces v1's CSP solver with simple grid-center default assignment.
Null faces receive the grid center position (midpoint of the 12x12 grid)
with a low default weight, ensuring every face has a coordinate.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    GRID_SIZE,
    PipelineState,
)

# Default position for unresolved faces: grid center
_DEFAULT_X = (GRID_SIZE - 1) // 2  # 5 on 12x12
_DEFAULT_Y = (GRID_SIZE - 1) // 2
_DEFAULT_WEIGHT = 0.1


class CoordinateResolver:
    """Stage 2: Fill null faces in partial coordinate with grid-center defaults."""

    def execute(self, state: PipelineState):
        if state.partial_coordinate is None:
            raise RuntimeError("Stage 2 requires partial_coordinate from Stage 1")

        partial = state.partial_coordinate
        resolved: dict[str, dict] = {}
        max_coord = GRID_SIZE - 1

        for face in ALL_FACES:
            entry = partial.get(face)

            if entry is not None:
                # Clamp coordinates to valid grid range
                x = max(0, min(int(entry["x"]), max_coord))
                y = max(0, min(int(entry["y"]), max_coord))
                resolved[face] = {
                    "x": x,
                    "y": y,
                    "weight": entry.get("weight", _DEFAULT_WEIGHT),
                    "confidence": entry.get("confidence", 0.0),
                    "source": "intent",
                }
            else:
                # Assign grid center with low weight
                resolved[face] = {
                    "x": _DEFAULT_X,
                    "y": _DEFAULT_Y,
                    "weight": _DEFAULT_WEIGHT,
                    "confidence": 0.0,
                    "source": "default",
                }

        state.coordinate = resolved
