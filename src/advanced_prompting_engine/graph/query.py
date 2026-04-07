"""Graph Query Layer — structured read access to the NetworkX graph.

Authoritative source: CONSTRUCT-v2.md, DESIGN.md.
All methods support provenance filter (canonical/user/merged).
No direct NetworkX access elsewhere in the codebase.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.graph.schema import (
    GRID_SIZE,
    NEXUS_SOURCE,
    SPECTRUM_OPPOSITION,
)


class GraphQueryLayer:
    """Read methods over the NetworkX graph. All provenance-aware."""

    def __init__(self, G: nx.DiGraph):
        self._g = G

    @property
    def graph(self) -> nx.DiGraph:
        return self._g

    # ------------------------------------------------------------------
    # Face queries
    # ------------------------------------------------------------------

    def list_faces(self) -> list[dict]:
        return [
            {"id": n, **self._g.nodes[n]}
            for n in self._g.nodes()
            if self._g.nodes[n].get("type") == "face"
        ]

    # ------------------------------------------------------------------
    # Construct queries
    # ------------------------------------------------------------------

    def list_constructs(
        self,
        face: str,
        provenance: str = "merged",
        classification: str | None = None,
    ) -> list[dict]:
        results = []
        for n, data in self._g.nodes(data=True):
            if data.get("type") != "construct":
                continue
            if data.get("face") != face:
                continue
            if provenance != "merged" and data.get("provenance") != provenance:
                continue
            if classification and data.get("classification") != classification:
                continue
            results.append({"id": n, **data})
        return results

    def get_construct(self, face: str, x: int, y: int) -> dict | None:
        node_id = f"{face}.{x}_{y}"
        if node_id in self._g.nodes:
            return {"id": node_id, **self._g.nodes[node_id]}
        return None

    def get_construct_by_id(self, node_id: str) -> dict | None:
        if node_id in self._g.nodes:
            return {"id": node_id, **self._g.nodes[node_id]}
        return None

    # ------------------------------------------------------------------
    # Relation queries
    # ------------------------------------------------------------------

    def list_relation_types(self) -> list[str]:
        return list({d.get("relation", "") for _, _, d in self._g.edges(data=True)})

    def get_edges(self, node: str, relation_type: str | None = None) -> list[dict]:
        edges = []
        for _, v, data in self._g.edges(node, data=True):
            if relation_type and data.get("relation") != relation_type:
                continue
            edges.append({"source": node, "target": v, **data})
        return edges

    # ------------------------------------------------------------------
    # Spectrum queries
    # ------------------------------------------------------------------

    def get_spectrum_opposite(self, face: str, x: int, y: int) -> dict | None:
        """Find the spectrum opposite of an edge construct."""
        node_id = f"{face}.{x}_{y}"
        for _, v, data in self._g.edges(node_id, data=True):
            if data.get("relation") == SPECTRUM_OPPOSITION:
                return {"id": v, **self._g.nodes.get(v, {})}
        # Check reverse direction
        for u, _, data in self._g.in_edges(node_id, data=True):
            if data.get("relation") == SPECTRUM_OPPOSITION:
                return {"id": u, **self._g.nodes.get(u, {})}
        return None

    def get_edge_constructs(self, face: str) -> list[dict]:
        """All 44 edge-classified constructs for a face (12x12 grid)."""
        return [
            c for c in self.list_constructs(face)
            if c.get("classification") in ("corner", "midpoint", "edge")
        ]

    # ------------------------------------------------------------------
    # Nexus queries
    # ------------------------------------------------------------------

    def get_nexus(self, source_face: str, target_face: str) -> dict | None:
        node_id = f"nexus.{source_face}.{target_face}"
        if node_id in self._g.nodes:
            return {"id": node_id, **self._g.nodes[node_id]}
        return None

    def get_spoke(self, face: str) -> list[dict]:
        """All nexus nodes originating from a face (the spoke's 11 gems)."""
        results = []
        for n, data in self._g.nodes(data=True):
            if data.get("type") == "nexus" and data.get("source_face") == face:
                results.append({"id": n, **data})
        return results

    # ------------------------------------------------------------------
    # Cube pairing queries
    # ------------------------------------------------------------------

    def get_paired_face(self, face: str) -> str | None:
        """Return the complementary counterpart for a face, or None."""
        from advanced_prompting_engine.graph.schema import CUBE_PAIRS
        for a, b in CUBE_PAIRS:
            if face == a:
                return b
            if face == b:
                return a
        return None

    def get_nexus_by_tier(self, tier: str) -> list[dict]:
        """All nexi of a given cube tier ('paired', 'adjacent', 'opposite')."""
        return [
            {"id": n, **data}
            for n, data in self._g.nodes(data=True)
            if data.get("type") == "nexus" and data.get("cube_tier") == tier
        ]

    # ------------------------------------------------------------------
    # Path queries
    # ------------------------------------------------------------------

    def find_path(self, source: str, target: str, weight_fn=None) -> list[str]:
        try:
            return nx.shortest_path(self._g, source, target, weight=weight_fn)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def find_all_paths(self, source: str, target: str, max_depth: int = 5) -> list[list[str]]:
        try:
            return list(nx.all_simple_paths(self._g, source, target, cutoff=max_depth))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    # ------------------------------------------------------------------
    # Subgraph
    # ------------------------------------------------------------------

    def get_subgraph(self, nodes: list[str]) -> nx.DiGraph:
        return self._g.subgraph(nodes).copy()
