"""MCP Server — registers tools, prompts, resources. Manages startup.

Authoritative source: CONSTRUCT-v2.md, DESIGN.md.
Startup: SQLite -> canonical data -> NetworkX graph -> caches -> pipeline -> MCP.
"""

from __future__ import annotations

import atexit
import json
import logging

import networkx as nx
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.canonical import CANONICAL_VERSION, build_canonical_graph
from advanced_prompting_engine.graph.mutation import GraphMutationLayer
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.graph.schema import ALL_FACES, CUBE_PAIRS, FACE_DEFINITIONS, FACE_PHASES, GRID_SIZE, SYMMETRIC_RELATIONS
from advanced_prompting_engine.graph.store import SqliteStore
from advanced_prompting_engine.pipeline.runner import PipelineRunner
from advanced_prompting_engine.pipeline.construction_bridge import CUBE_PAIR_CONCERNS
from advanced_prompting_engine.tools.create_prompt_basis import handle_create_prompt_basis
from advanced_prompting_engine.tools.explore_space import handle_explore_space
from advanced_prompting_engine.tools.extend_schema import handle_extend_schema
from advanced_prompting_engine.tools.interpret_basis import handle_interpret_basis


def create_server(db_path: str | None = None) -> FastMCP:
    """Create and configure the MCP server with all components."""

    # --- Database + Graph ---
    store = SqliteStore(db_path=db_path)
    store.create_tables()
    atexit.register(store.close)

    # Check for version mismatch — stale DB from older version
    if not store.needs_initialization() and store.check_migration_needed(CANONICAL_VERSION):
        logger.info("Version mismatch (DB: %s, code: %s) — re-initializing...",
                     store.get_current_version(), CANONICAL_VERSION)
        nodes, edges = build_canonical_graph()
        orphans = store.migrate(nodes, edges, CANONICAL_VERSION)
        if orphans:
            logger.warning("Migration found %d orphaned user edges", len(orphans))
        logger.info("Migration complete: %d nodes, %d edges", len(nodes), len(edges))

    if store.needs_initialization():
        logger.info("First run — initializing canonical data...")
        nodes, edges = build_canonical_graph()
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

    # --- Caches ---
    embedding_cache = EmbeddingCache()
    embedding_cache.initialize(G)

    tfidf_cache = TfidfCache()
    tfidf_cache.initialize(G)

    logger.info("Caches initialized")

    # --- Pipeline ---
    query_layer = GraphQueryLayer(G)
    mutation_layer = GraphMutationLayer(G, store, tfidf_cache)
    pipeline = PipelineRunner(G, query_layer, embedding_cache, tfidf_cache)

    max_coord = GRID_SIZE - 1

    # --- MCP Server ---
    mcp = FastMCP(
        "Advanced Prompting Engine",
        instructions=(
            "A universal prompt creation engine. Measures intent across 12 philosophical "
            "dimensions and returns a construction basis for prompt creation. "
            "Use create_prompt_basis as the primary tool."
        ),
    )

    # --- Tools ---

    @mcp.tool()
    def create_prompt_basis(
        intent: str | None = None,
        coordinate: dict | str | None = None,
        compact: bool = False,
        focused: bool = False,
    ) -> str:
        """Measure intent across 12 philosophical dimensions and return a construction basis.

        Use this before constructing any prompt where dimensional precision,
        philosophical coherence, or systematic completeness matters.

        Provide either 'intent' (natural language) or 'coordinate' (JSON object with
        12 faces, each having x, y, weight).

        Output modes (mutually exclusive, focused takes priority):
        - Default: full output (~50KB) with all pipeline data
        - compact=true: summary fields only (~2KB)
        - focused=true: guidance-centric output (~500 bytes) with dominant
          dimensions, gaps, resonance, and coherence — what a prompt engineer needs
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

        result = handle_create_prompt_basis(
            pipeline, intent=intent, coordinate=coord_dict,
            compact=compact, focused=focused,
        )
        return json.dumps(result, default=_json_default)

    @mcp.tool()
    def explore_space(
        operation: str,
        face: str | None = None,
        x: int | None = None,
        y: int | None = None,
        target_face: str | None = None,
        target_x: int | None = None,
        target_y: int | None = None,
        coordinate: dict | str | None = None,
        coordinate_a: dict | str | None = None,
        coordinate_b: dict | str | None = None,
        classification: str | None = None,
        provenance: str = "merged",
    ) -> str:
        """Explore the philosophical manifold. Operations: list_faces, list_constructs,
        get_construct, get_neighborhood, find_path, get_spoke, stress_test, triangulate."""
        kwargs = {
            "face": face, "x": x, "y": y,
            "target_face": target_face, "target_x": target_x, "target_y": target_y,
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
        face: str | None = None,
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
            "face": face, "x": x, "y": y,
            "question": question,
            "tags": (json.loads(tags) if isinstance(tags, str) else tags) if tags else None,
            "description": description,
            "source_id": source_id, "target_id": target_id,
            "relation_type": relation_type, "strength": strength,
            "override_reason": override_reason,
        }
        result = handle_extend_schema(mutation_layer, operation, **kwargs)
        return json.dumps(result, default=_json_default)

    @mcp.tool()
    def interpret_basis(basis: str) -> str:
        """Interpret a construction basis produced by create_prompt_basis.

        Takes the JSON output from create_prompt_basis and returns a
        plain-language interpretation of the philosophical measurement.
        Extracts the guidance section and formats it as readable text
        with dominant dimensions, gaps, and strongest resonance.
        """
        result = handle_interpret_basis(basis)
        return json.dumps(result, default=_json_default)

    # --- Resources ---

    # Per-face action guidance for interpreting activation strength
    ACTION_GUIDANCE = {
        "ontology": "If strongly activated: your prompt explicitly defines what entities and relationships exist. If weak: consider whether your prompt's assumptions about what exists are clear.",
        "epistemology": "If strongly activated: your prompt establishes how truth is verified. If weak: consider whether your prompt's claims are grounded in evidence or reasoning.",
        "axiology": "If strongly activated: your prompt specifies evaluation criteria and standards of worth. If weak: consider what criteria the prompt uses to judge quality.",
        "teleology": "If strongly activated: your prompt is directed toward a clear purpose. If weak: consider whether the prompt's ultimate goal is stated or assumed.",
        "phenomenology": "If strongly activated: your prompt addresses subjective experience and representation. If weak: consider whether user experience is accounted for.",
        "ethics": "If strongly activated: your prompt addresses moral obligations and permissibility. If weak: consider whether ethical constraints are relevant but unstated.",
        "aesthetics": "If strongly activated: your prompt attends to form, beauty, and sensory quality. If weak: consider whether aesthetic standards matter for your use case.",
        "praxeology": "If strongly activated: your prompt structures actions and behaviors. If weak: consider whether the prompt's action model is clear.",
        "methodology": "If strongly activated: your prompt specifies systematic processes. If weak: consider whether the prompt's method of inquiry is defined.",
        "semiotics": "If strongly activated: your prompt carefully encodes and communicates meaning. If weak: consider whether signal encoding is clear.",
        "hermeneutics": "If strongly activated: your prompt handles interpretation and ambiguity. If weak: consider whether interpretive frameworks are needed.",
        "heuristics": "If strongly activated: your prompt uses practical strategies for complexity. If weak: consider whether fallback strategies are needed.",
    }

    @mcp.resource("ape://axiom_manifest")
    def axiom_manifest() -> str:
        """The 12 philosophical faces with core questions, sub-dimensions, and action guidance."""
        faces = []
        for i, face in enumerate(ALL_FACES):
            defn = FACE_DEFINITIONS[face]
            faces.append({
                "id": face,
                "core_question": defn["core_question"],
                "construction_template": defn["construction_template"],
                "x_axis": defn["x_axis_name"],
                "y_axis": defn["y_axis_name"],
                "phase": FACE_PHASES.get(face, "unknown"),
                "causal_order": i,
                "action_guidance": ACTION_GUIDANCE[face],
            })
        return json.dumps({"faces": faces})

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
            "description": f"A coordinate positions the client in the 12-axis philosophical manifold.",
            "format": f"Each face has {{x: int (0-{max_coord}), y: int (0-{max_coord}), weight: float (0-1)}}",
            "faces": {
                face: {
                    "x_axis": FACE_DEFINITIONS[face]["x_axis_name"],
                    "y_axis": FACE_DEFINITIONS[face]["y_axis_name"],
                }
                for face in ALL_FACES
            },
        }
        return json.dumps(schema)

    @mcp.resource("ape://examples")
    def examples() -> str:
        """Example intents with interpretations to demonstrate engine usage."""
        return json.dumps({
            "examples": [
                {
                    "intent": "Design an ethical framework for autonomous vehicle decision-making",
                    "interpretation": (
                        "Strongly activates epistemology (truth verification), "
                        "ontology (what entities exist), and praxeology (action structure). "
                        "Ethics present but not dominant. Methodology is a gap "
                        "\u2014 the intent doesn't address what systematic process to follow."
                    ),
                    "dominant_faces": ["epistemology", "ontology", "praxeology"],
                    "gaps": ["methodology", "aesthetics"],
                },
                {
                    "intent": "Write a poem about the nature of consciousness",
                    "interpretation": (
                        "Strongly activates phenomenology (subjective experience), "
                        "ontology (what exists), and aesthetics (beauty/form). "
                        "Methodology and praxeology are gaps \u2014 the intent is about "
                        "understanding and expressing, not about systematic process or action."
                    ),
                    "dominant_faces": ["phenomenology", "ontology", "aesthetics"],
                    "gaps": ["methodology", "praxeology"],
                },
                {
                    "intent": "Build a systematic method for evaluating scientific claims",
                    "interpretation": (
                        "Strongly activates epistemology (truth verification), "
                        "methodology (systematic process), and axiology (evaluation criteria). "
                        "Ethics and aesthetics are gaps \u2014 the intent focuses on "
                        "knowledge and process, not moral obligation or form."
                    ),
                    "dominant_faces": ["epistemology", "methodology", "axiology"],
                    "gaps": ["ethics", "aesthetics"],
                },
                {
                    "intent": "Interpret the meaning of an ambiguous legal contract",
                    "interpretation": (
                        "Strongly activates hermeneutics (interpretation frameworks), "
                        "semiotics (how meaning is encoded), and epistemology (truth verification). "
                        "Aesthetics and teleology are gaps \u2014 the intent is about "
                        "decoding meaning, not about beauty or ultimate purpose."
                    ),
                    "dominant_faces": ["hermeneutics", "semiotics", "epistemology"],
                    "gaps": ["aesthetics", "teleology"],
                },
            ]
        })

    # --- Prompts ---

    @mcp.prompt()
    def orient() -> str:
        """Understand the philosophical manifold before using it."""
        face_lines = "\n".join(
            f"- **{face.title()}** ({FACE_DEFINITIONS[face]['core_question']}): "
            f"x-axis: {FACE_DEFINITIONS[face]['x_axis_name']}, "
            f"y-axis: {FACE_DEFINITIONS[face]['y_axis_name']}"
            for face in ALL_FACES
        )
        return (
            "The Advanced Prompting Engine measures intent across 12 philosophical dimensions:\n\n"
            + face_lines
            + "\n\nTo use:\n"
            "1. Call create_prompt_basis with an intent (natural language) or coordinate (JSON)\n"
            "2. Review the 'guidance' section for dominant dimensions, gaps, and resonance\n"
            "3. Use the construction questions to refine your prompt\n"
            "4. Set focused=true for a concise summary instead of full output"
        )

    @mcp.prompt()
    def build_construction_basis() -> str:
        """Build a complete construction basis from an intent."""
        return (
            "To build a construction basis:\n"
            "1. Call create_prompt_basis with your intent\n"
            "2. Start with the 'guidance' section:\n"
            "   - 'dominant_dimensions' shows where your intent is strongest\n"
            "   - 'neglected_dimensions' shows philosophical gaps to consider\n"
            "   - 'strongest_resonance' shows the best theoretical-practical pairing\n"
            "3. Review construction_questions for per-face prompt construction guidance\n"
            "   - Each face has a template question, position_summary, and meaning_mechanism\n"
            "4. Review spectrum_opposites to understand what your position is NOT\n"
            "5. Review central_gem.coherence for overall dimensional alignment\n"
            "6. For quick results, use focused=true to get only guidance + top faces"
        )

    @mcp.prompt()
    def compare_positions() -> str:
        """Compare two intents dimensionally."""
        return (
            "To compare two positions:\n"
            "1. Run create_prompt_basis for each intent separately (use focused=true for brevity)\n"
            "2. Call explore_space with operation=triangulate, providing coordinate_a and coordinate_b\n"
            "3. Review the triangulation output:\n"
            "   - Per-face construct intersection shows where intents overlap\n"
            "   - Spoke comparison shows behavioral signature differences\n"
            "   - Coordinate distance quantifies overall separation\n"
            "4. Compare the 'guidance' sections from each basis:\n"
            "   - Which dimensions are dominant in one but neglected in the other?\n"
            "   - Do they share the same strongest resonance pair?"
        )

    @mcp.prompt()
    def resolve_and_construct() -> str:
        """Build a basis and resolve all tensions."""
        return (
            "To resolve tensions before constructing:\n"
            "1. Call create_prompt_basis with your intent\n"
            "2. Check the 'guidance' section first for an overview\n"
            "3. Review the tensions section:\n"
            "   - Positional tensions indicate conflicting philosophical positions\n"
            "   - Spectrum tensions indicate active-opposite polarity\n"
            "4. For high positional tensions, use explore_space with operation=stress_test\n"
            "   to find coordinate adjustments that reduce tension\n"
            "5. Check harmonization_pairs: low resonance between cube pairs suggests\n"
            "   the theoretical and practical aspects of a concern are misaligned\n"
            "6. Use the interpret_basis tool to get a plain-language reading of the result"
        )

    logger.info("MCP server configured: 4 tools, 4 prompts, 4 resources")
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
