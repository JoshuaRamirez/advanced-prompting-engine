"""MCP Server — registers tools, prompts, resources. Manages startup.

Authoritative source: Spec 10, Spec 09.
Startup: SQLite → canonical data → NetworkX graph → caches → pipeline → MCP.
"""

from __future__ import annotations

import atexit
import json
import logging

import networkx as nx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

from advanced_prompting_engine.cache.centrality import CentralityCache
from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.canonical import CANONICAL_VERSION, generate_all_canonical
from advanced_prompting_engine.graph.mutation import GraphMutationLayer
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.graph.schema import ALL_BRANCHES, BRANCH_DEFINITIONS, SYMMETRIC_RELATIONS
from advanced_prompting_engine.graph.store import SqliteStore
from advanced_prompting_engine.pipeline.runner import PipelineRunner
from advanced_prompting_engine.tools.create_prompt_basis import handle_create_prompt_basis
from advanced_prompting_engine.tools.explore_space import handle_explore_space
from advanced_prompting_engine.tools.extend_schema import handle_extend_schema


def create_server(db_path: str | None = None) -> FastMCP:
    """Create and configure the MCP server with all components."""

    # --- Step 1-4: Database + Graph ---
    store = SqliteStore(db_path=db_path)
    store.create_tables()
    atexit.register(store.close)

    if store.needs_initialization():
        logger.info("First run — initializing canonical data...")
        nodes, edges = generate_all_canonical()
        store.initialize_canonical(nodes, edges, CANONICAL_VERSION)
        logger.info("Canonical data initialized: %d nodes, %d edges", len(nodes), len(edges))

    # Load all data into NetworkX
    G = nx.DiGraph()
    for n in store.load_canonical_nodes():
        G.add_node(n["id"], **n)
    for e in store.load_canonical_edges():
        G.add_edge(e["source_id"], e["target_id"], **e)
        if e.get("relation") in SYMMETRIC_RELATIONS:
            rev = {k: v for k, v in e.items() if k not in ("source_id", "target_id")}
            G.add_edge(e["target_id"], e["source_id"],
                       source_id=e["target_id"], target_id=e["source_id"], **rev)
    for n in store.load_user_nodes():
        G.add_node(n["id"], **n)
    for e in store.load_user_edges():
        G.add_edge(e["source_id"], e["target_id"], **e)
        if e.get("relation") in SYMMETRIC_RELATIONS:
            rev = {k: v for k, v in e.items() if k not in ("source_id", "target_id")}
            G.add_edge(e["target_id"], e["source_id"],
                       source_id=e["target_id"], target_id=e["source_id"], **rev)

    logger.info("Graph loaded: %d nodes, %d edges", len(G.nodes()), len(G.edges()))

    # --- Step 5-7: Caches ---
    embedding_cache = EmbeddingCache()
    embedding_cache.initialize(G)

    tfidf_cache = TfidfCache()
    tfidf_cache.initialize(G)

    centrality_cache = CentralityCache()
    centrality_cache.initialize(G)

    logger.info("Caches initialized")

    # --- Step 8: Pipeline ---
    query_layer = GraphQueryLayer(G)
    mutation_layer = GraphMutationLayer(G, store, embedding_cache, tfidf_cache, centrality_cache)
    pipeline = PipelineRunner(G, query_layer, embedding_cache, tfidf_cache, centrality_cache)

    # --- Step 9-12: MCP Server ---
    mcp = FastMCP(
        "Advanced Prompting Engine",
        instructions=(
            "A universal prompt creation engine. Measures intent across 10 philosophical "
            "dimensions and returns a construction basis for prompt creation. "
            "Use create_prompt_basis as the primary tool."
        ),
    )

    # --- Tools ---

    @mcp.tool()
    def create_prompt_basis(
        intent: str | None = None,
        coordinate: dict | str | None = None,
    ) -> str:
        """Measure intent across 10 philosophical dimensions and return a construction basis.

        Use this before constructing any prompt where dimensional precision,
        philosophical coherence, or systematic completeness matters.

        Provide either 'intent' (natural language) or 'coordinate' (JSON object with
        10 branches, each having x, y, weight).
        """
        coord_dict = None
        if coordinate:
            if isinstance(coordinate, dict):
                coord_dict = coordinate
            elif isinstance(coordinate, str):
                try:
                    coord_dict = json.loads(coordinate)
                except json.JSONDecodeError:
                    return json.dumps({"status": "error", "message": "Invalid coordinate JSON"})
            else:
                coord_dict = coordinate

        result = handle_create_prompt_basis(pipeline, intent=intent, coordinate=coord_dict)
        return json.dumps(result, default=_json_default)

    @mcp.tool()
    def explore_space(
        operation: str,
        branch: str | None = None,
        x: int | None = None,
        y: int | None = None,
        target_branch: str | None = None,
        target_x: int | None = None,
        target_y: int | None = None,
        coordinate: dict | str | None = None,
        coordinate_a: dict | str | None = None,
        coordinate_b: dict | str | None = None,
        classification: str | None = None,
        provenance: str = "merged",
    ) -> str:
        """Explore the philosophical manifold. Operations: list_branches, list_constructs,
        get_construct, get_neighborhood, find_path, get_spoke, stress_test, triangulate."""
        kwargs = {
            "branch": branch, "x": x, "y": y,
            "target_branch": target_branch, "target_x": target_x, "target_y": target_y,
            "classification": classification, "provenance": provenance,
        }
        if coordinate:
            kwargs["coordinate"] = json.loads(coordinate) if isinstance(coordinate, str) else coordinate
        if coordinate_a:
            kwargs["coordinate_a"] = json.loads(coordinate_a) if isinstance(coordinate_a, str) else coordinate_a
        if coordinate_b:
            kwargs["coordinate_b"] = json.loads(coordinate_b) if isinstance(coordinate_b, str) else coordinate_b

        result = handle_explore_space(query_layer, pipeline, operation, **kwargs)
        return json.dumps(result, default=_json_default)

    @mcp.tool()
    def extend_schema(
        operation: str,
        branch: str | None = None,
        x: int | None = None,
        y: int | None = None,
        question: str | None = None,
        tags: list | str | None = None,
        description: str | None = None,
        source_id: str | None = None,
        target_id: str | None = None,
        relation_type: str | None = None,
        strength: float = 0.5,
        override_reason: str | None = None,
    ) -> str:
        """Add constructs or relations to the graph. Contradiction detection is automatic.

        Operations: add_construct, add_relation."""
        kwargs = {
            "branch": branch, "x": x, "y": y,
            "question": question,
            "tags": (json.loads(tags) if isinstance(tags, str) else tags) if tags else None,
            "description": description,
            "source_id": source_id, "target_id": target_id,
            "relation_type": relation_type, "strength": strength,
            "override_reason": override_reason,
        }
        result = handle_extend_schema(mutation_layer, operation, **kwargs)
        return json.dumps(result, default=_json_default)

    # --- Resources ---

    @mcp.resource("ape://axiom_manifest")
    def axiom_manifest() -> str:
        """The 10 philosophical branches with core questions and sub-dimensions."""
        branches = []
        for i, branch in enumerate(ALL_BRANCHES):
            defn = BRANCH_DEFINITIONS[branch]
            branches.append({
                "id": branch,
                "core_question": defn["core_question"],
                "construction_template": defn["construction_template"],
                "x_axis": defn["x_axis_name"],
                "y_axis": defn["y_axis_name"],
                "causal_order": i,
            })
        return json.dumps({"branches": branches})

    @mcp.resource("ape://schema_manifest")
    def schema_manifest() -> str:
        """Current state of the graph — node/edge counts by type."""
        from collections import Counter
        node_types = Counter(G.nodes[n].get("type", "unknown") for n in G.nodes())
        edge_types = Counter(G.edges[u, v].get("relation", "unknown") for u, v in G.edges())
        return json.dumps({
            "total_nodes": len(G.nodes()),
            "total_edges": len(G.edges()),
            "node_types": dict(node_types),
            "edge_types": dict(edge_types),
        })

    @mcp.resource("ape://coordinate_schema")
    def coordinate_schema() -> str:
        """Schema for a valid coordinate object."""
        schema = {
            "description": "A coordinate positions the client in the 10-axis philosophical manifold.",
            "format": "Each branch has {x: int (0-9), y: int (0-9), weight: float (0-1)}",
            "branches": {
                branch: {
                    "x_axis": BRANCH_DEFINITIONS[branch]["x_axis_name"],
                    "y_axis": BRANCH_DEFINITIONS[branch]["y_axis_name"],
                }
                for branch in ALL_BRANCHES
            },
        }
        return json.dumps(schema)

    # --- Prompts ---

    @mcp.prompt()
    def orient() -> str:
        """Understand the philosophical manifold before using it."""
        return (
            "To orient yourself in the philosophical manifold:\n"
            "1. Read the axiom_manifest resource to understand the 10 branches\n"
            "2. Read the coordinate_schema resource to understand how positions are specified\n"
            "3. Read the schema_manifest resource to see current graph state\n"
            "4. Use create_prompt_basis with your intent to get a construction basis"
        )

    @mcp.prompt()
    def build_construction_basis() -> str:
        """Build a complete construction basis from an intent."""
        return (
            "To build a construction basis:\n"
            "1. Call create_prompt_basis with your intent\n"
            "2. Review active_constructs and their epistemic questions\n"
            "3. Review spectrum_opposites to understand what your position is NOT\n"
            "4. Review spoke profiles for per-branch behavioral signatures\n"
            "5. Review central_gem for overall coherence\n"
            "6. Use construction_questions to guide prompt construction"
        )

    @mcp.prompt()
    def compare_positions() -> str:
        """Compare two intents dimensionally."""
        return (
            "To compare two positions:\n"
            "1. Call explore_space with operation=triangulate, providing coordinate_a and coordinate_b\n"
            "2. Review per-branch construct intersection\n"
            "3. Review shared tensions and spoke comparison\n"
            "4. Check coordinate distance for overall separation"
        )

    @mcp.prompt()
    def resolve_and_construct() -> str:
        """Build a basis and resolve all tensions."""
        return (
            "To resolve tensions before constructing:\n"
            "1. Call create_prompt_basis with your intent\n"
            "2. Review the tensions list\n"
            "3. For each tension, check resolution_paths\n"
            "4. If no resolution exists, consider adjusting the coordinate\n"
            "5. Use explore_space with operation=stress_test to find improvements"
        )

    logger.info("MCP server configured: 3 tools, 4 prompts, 3 resources")
    return mcp


def _json_default(obj):
    """Handle numpy arrays and other non-serializable types."""
    import numpy as np
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, set):
        return list(obj)
    return str(obj)
