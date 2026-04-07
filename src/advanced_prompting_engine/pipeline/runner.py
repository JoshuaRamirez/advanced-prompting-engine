"""Pipeline Runner — orchestrates all 8 stages in sequence.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass).
Ensures caches are valid before pipeline run.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import PipelineState
from advanced_prompting_engine.math.semantic import SemanticBridge
from advanced_prompting_engine.pipeline.construction_bridge import ConstructionBridge
from advanced_prompting_engine.pipeline.construct_resolver import ConstructResolver
from advanced_prompting_engine.pipeline.coordinate_resolver import CoordinateResolver
from advanced_prompting_engine.pipeline.intent_parser import IntentParser
from advanced_prompting_engine.pipeline.nexus_gem_analyzer import NexusGemAnalyzer
from advanced_prompting_engine.pipeline.position_computer import PositionComputer
from advanced_prompting_engine.pipeline.spoke_analyzer import SpokeAnalyzer
from advanced_prompting_engine.pipeline.tension_analyzer import TensionAnalyzer


class PipelineRunner:
    """Runs the 8-stage pipeline: intent -> construction basis."""

    def __init__(self, graph, query_layer, embedding_cache, tfidf_cache, centrality_cache=None):
        self._graph = graph
        self._embedding_cache = embedding_cache
        self._tfidf_cache = tfidf_cache
        self._centrality_cache = centrality_cache

        # Initialize semantic bridge (degrades gracefully if artifacts missing)
        semantic_bridge = SemanticBridge()
        semantic_bridge.load()

        self._stages = [
            IntentParser(tfidf_cache, query_layer, semantic_bridge),  # Stage 1
            CoordinateResolver(),                            # Stage 2
            PositionComputer(),                              # Stage 3
            ConstructResolver(query_layer),                  # Stage 4
            TensionAnalyzer(graph, query_layer),             # Stage 5
            NexusGemAnalyzer(graph, query_layer),            # Stage 6
            SpokeAnalyzer(),                                 # Stage 7
            ConstructionBridge(query_layer),                 # Stage 8
        ]

    def run(self, raw_input: str | dict) -> dict:
        """Execute the full pipeline and return the construction basis."""
        # Ensure caches are valid
        if self._embedding_cache is not None:
            self._embedding_cache.ensure_valid(self._graph)
        self._tfidf_cache.ensure_valid(self._graph)
        if self._centrality_cache:
            self._centrality_cache.ensure_valid(self._graph)

        state = PipelineState(raw_input=raw_input)
        for stage in self._stages:
            stage.execute(state)

        return state.construction_basis
