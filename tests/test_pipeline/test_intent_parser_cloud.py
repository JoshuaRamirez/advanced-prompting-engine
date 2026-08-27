"""Tests for IntentParser with cloud vector embeddings and fallback."""

from unittest import mock
import numpy as np
import pytest

from advanced_prompting_engine.graph.schema import ALL_FACES, GRID_SIZE, PipelineState
from advanced_prompting_engine.math.cloud_bridge import CloudSemanticBridge
from advanced_prompting_engine.math.semantic import GeometricBridge
from advanced_prompting_engine.pipeline.intent_parser import IntentParser
from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider


class TestIntentParserCloud:
    @pytest.fixture
    def cloud_setup(self):
        geom_bridge = GeometricBridge()
        geom_bridge.load()

        cloud_bridge = CloudSemanticBridge()
        cloud_bridge.load("openai", 3072)

        provider = OpenAIEmbeddingProvider(api_key="sk-test-key", dimensions=3072)
        parser = IntentParser(
            geometric_bridge=geom_bridge,
            embedding_provider=provider,
            cloud_bridge=cloud_bridge,
        )
        return parser, provider

    def test_cloud_embedding_execution(self, cloud_setup):
        parser, provider = cloud_setup

        rng = np.random.RandomState(42)
        mock_vec = rng.randn(3072).astype(np.float32)
        mock_vec = mock_vec / np.linalg.norm(mock_vec)

        with mock.patch.object(provider, "embed_text", return_value=mock_vec):
            state = PipelineState(raw_input="Structure an ethical framework for autonomous vehicles")
            parser.execute(state)

            assert state.partial_coordinate is not None
            assert len(state.partial_coordinate) == 12

            for face, entry in state.partial_coordinate.items():
                assert face in ALL_FACES
                if entry is not None:
                    assert 0 <= entry["x"] <= GRID_SIZE - 1
                    assert 0 <= entry["y"] <= GRID_SIZE - 1
                    assert 0.1 <= entry["weight"] <= 1.0
                    assert 0.0 <= entry["confidence"] <= 1.0

    def test_cloud_embedding_fallback_on_none(self, cloud_setup):
        parser, provider = cloud_setup

        # Simulate provider returning None (e.g. network timeout or failure)
        with mock.patch.object(provider, "embed_text", return_value=None):
            state = PipelineState(raw_input="Analyze epistemological warrant and empirical verification")
            parser.execute(state)

            # Should fall back cleanly to local GeometricBridge and produce valid coordinates
            assert state.partial_coordinate is not None
            assert len(state.partial_coordinate) == 12
            assert state.partial_coordinate["epistemology"] is not None

    def test_cloud_embedding_fallback_on_exception(self, cloud_setup):
        parser, provider = cloud_setup

        # Simulate provider raising an unexpected exception
        with mock.patch.object(provider, "embed_text", side_effect=RuntimeError("Socket error")):
            state = PipelineState(raw_input="Examine moral duties and deontological principles")
            parser.execute(state)

            # Should fall back gracefully without raising exceptions
            assert state.partial_coordinate is not None
            assert len(state.partial_coordinate) == 12
            assert state.partial_coordinate["ethics"] is not None
