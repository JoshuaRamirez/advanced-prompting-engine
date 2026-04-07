"""Stage 4 — Construct Resolver: determine active constructs per face.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 4).

Primary construct always active. Nearby constructs within Manhattan distance
threshold also activate. 12 faces, 144 constructs per face.

Activation radius varies by face weight from the coordinate:
  weight >= 0.7 → radius 3 (strong commitment widens the activation field)
  weight >= 0.4 → radius 2 (moderate commitment, default neighborhood)
  weight <  0.4 → radius 1 (weak commitment, narrow activation)

Each construct's potency is scaled by the face weight to produce
``effective_potency``. Downstream stages (tension, gem) should prefer
``effective_potency`` when available, falling back to ``potency``.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import ALL_FACES, GRID_SIZE, PipelineState


def _activation_radius(weight: float) -> int:
    """Determine activation radius from face weight."""
    if weight >= 0.7:
        return 3
    if weight >= 0.4:
        return 2
    return 1


class ConstructResolver:
    """Stage 4: Resolve primary + nearby active constructs per face."""

    def __init__(self, query_layer):
        self._query = query_layer

    def execute(self, state: PipelineState):
        if state.manifold_position is None:
            raise RuntimeError("Stage 4 requires manifold_position from Stage 3")

        per_face = state.manifold_position["per_face"]
        active_constructs: dict[str, list[dict]] = {}

        for face in ALL_FACES:
            face_data = per_face.get(face, {})
            primary_id = face_data.get("primary")
            px = face_data.get("x", 0)
            py = face_data.get("y", 0)

            # Read face weight from the resolved coordinate
            weight = 1.0
            if state.coordinate and face in state.coordinate:
                weight = state.coordinate[face].get("weight", 1.0)

            radius = _activation_radius(weight)

            # Always include the primary construct
            primary = self._query.get_construct_by_id(primary_id)
            if primary is None:
                active_constructs[face] = []
                continue

            # Add effective_potency scaled by face weight
            primary["effective_potency"] = primary.get("potency", 0.6) * weight

            active = [primary]
            seen = {primary_id}

            # Activate nearby constructs within Manhattan distance threshold
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    if abs(dx) + abs(dy) > radius:
                        continue
                    nx_ = px + dx
                    ny_ = py + dy
                    if not (0 <= nx_ < GRID_SIZE and 0 <= ny_ < GRID_SIZE):
                        continue
                    neighbor_id = f"{face}.{nx_}_{ny_}"
                    if neighbor_id in seen:
                        continue
                    seen.add(neighbor_id)
                    neighbor = self._query.get_construct_by_id(neighbor_id)
                    if neighbor is not None:
                        neighbor["effective_potency"] = neighbor.get("potency", 0.6) * weight
                        active.append(neighbor)

            active_constructs[face] = active

        state.active_constructs = active_constructs
