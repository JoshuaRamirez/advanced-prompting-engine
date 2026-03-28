"""Shared hash utilities for cache invalidation.

Authoritative source: Spec 09.
Two hashes: graph_hash (topology) and tfidf_hash (content).
"""

from __future__ import annotations

import hashlib

import networkx as nx


def compute_graph_hash(G: nx.Graph) -> str:
    """Deterministic hash of graph topology (nodes + edges + relation types).

    Changes when: node added/removed, edge added/removed, edge relation changes.
    Does NOT change when: edge strengths change, node descriptions change.
    """
    node_part = str(sorted(G.nodes()))
    edge_part = str(sorted(
        (u, v, d.get("relation", ""))
        for u, v, d in G.edges(data=True)
    ))
    combined = f"{len(G.nodes())}:{len(G.edges())}:{node_part}:{edge_part}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def compute_tfidf_hash(G: nx.Graph) -> str:
    """Hash that includes node content (question text + tags).

    Changes when: question or tags change on any construct node.
    Used by TF-IDF cache only (embeddings depend on topology, not labels).
    """
    content = sorted(
        f"{n}:{G.nodes[n].get('question', '')}:{G.nodes[n].get('tags', '')}"
        for n in G.nodes()
        if G.nodes[n].get("type") == "construct"
    )
    return hashlib.sha256(str(content).encode()).hexdigest()[:16]
