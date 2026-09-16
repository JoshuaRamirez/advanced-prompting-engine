#!/usr/bin/env python3
"""Interactive test script for validating live cloud embeddings.

Usage:
    python3 scripts/test_live_cloud_embedding.py
    python3 scripts/test_live_cloud_embedding.py "Design a decentralized governance framework"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project source is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from advanced_prompting_engine.providers.factory import get_embedding_provider
from advanced_prompting_engine.pipeline.runner import PipelineRunner
from advanced_prompting_engine.graph.canonical import build_canonical_graph
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.cache.embedding import EmbeddingCache
import networkx as nx


def main():
    test_intent = sys.argv[1] if len(sys.argv) > 1 else "Design an ethical framework for autonomous vehicle decision-making"

    print("=" * 70)
    print("Advanced Prompting Engine — Live Cloud Embedding Test")
    print("=" * 70)

    provider = get_embedding_provider()
    print(f"Active Provider : {provider.provider_name}")
    print(f"Active Model    : {provider.model_name}")
    print(f"Dimensions      : {provider.dimensions}d")
    print(f"Is Available    : {provider.is_available()}")
    print("-" * 70)

    if provider.provider_name == "local":
        print("Note: Provider is currently 'local'. To use cloud embeddings, set:")
        print("      export APE_EMBEDDING_PROVIDER=openai")
        print("=" * 70)

    print(f"Testing Intent  : {test_intent!r}")
    print("Running pipeline...")

    # Load in-memory graph
    nodes, edges = build_canonical_graph()
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source_id"], e["target_id"], **e)

    query_layer = GraphQueryLayer(G)
    tfidf_cache = TfidfCache()
    tfidf_cache.initialize(G)
    emb_cache = EmbeddingCache()

    runner = PipelineRunner(G, query_layer, emb_cache, tfidf_cache)
    basis = runner.run(test_intent)

    print("\n--- Pipeline Results ---")
    coords = basis.get("coordinate", {})
    print(f"{'Face':<16} {'X':<4} {'Y':<4} {'Weight':<8} {'Confidence':<10}")
    print("-" * 46)
    for face, entry in sorted(coords.items(), key=lambda item: item[1].get("weight", 0), reverse=True):
        x = entry.get("x")
        y = entry.get("y")
        w = entry.get("weight", 0)
        c = entry.get("confidence", 0)
        print(f"{face:<16} {x:<4} {y:<4} {w:<8.3f} {c:<10.3f}")

    print("\nCentral Gem Coherence:", basis.get("central_gem", {}).get("coherence"))
    print("Dominant Control Type:", basis.get("control_type_composition", {}).get("dominant_control_type"))
    print("=" * 70)
    print("Test completed successfully!")


if __name__ == "__main__":
    main()
