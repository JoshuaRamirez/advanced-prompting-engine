"""Tests for the CloudSemanticBridge mathematical projections."""

import numpy as np
import pytest

from advanced_prompting_engine.graph.schema import ALL_FACES
from advanced_prompting_engine.math.cloud_bridge import CloudSemanticBridge


class TestCloudSemanticBridge:
    def test_load_openai_anchors(self):
        bridge = CloudSemanticBridge()
        loaded = bridge.load("openai", 3072)
        assert loaded is True
        assert bridge.is_loaded is True
        assert bridge.dimensions == 3072
        assert bridge.provider == "openai"
        assert bridge.has_phase_data is True

    def test_load_gemini_anchors(self):
        bridge = CloudSemanticBridge()
        loaded = bridge.load("gemini", 2048)
        assert loaded is True
        assert bridge.is_loaded is True
        assert bridge.dimensions == 2048
        assert bridge.provider == "gemini"

    def test_load_missing_provider(self):
        bridge = CloudSemanticBridge()
        loaded = bridge.load("nonexistent_provider", 999)
        assert loaded is False
        assert bridge.is_loaded is False

    def test_face_relevance(self):
        bridge = CloudSemanticBridge()
        bridge.load("openai", 3072)

        rng = np.random.RandomState(123)
        vec = rng.randn(3072).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        scores = bridge.face_relevance(vec)
        assert len(scores) == 12
        for face in ALL_FACES:
            assert face in scores
            assert isinstance(scores[face], float)

        # Discriminative scores should be approximately zero-mean
        mean_score = sum(scores.values()) / 12.0
        assert abs(mean_score) < 1e-5

    def test_phase_weighting(self):
        bridge = CloudSemanticBridge()
        bridge.load("openai", 3072)

        rng = np.random.RandomState(456)
        vec = rng.randn(3072).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        phase_weights = bridge.phase_weighting(vec)
        assert len(phase_weights) == 12
        for face in ALL_FACES:
            assert face in phase_weights
            assert 0.0 <= phase_weights[face] <= 1.0

    def test_axis_projection(self):
        bridge = CloudSemanticBridge()
        bridge.load("openai", 3072)

        rng = np.random.RandomState(789)
        vec = rng.randn(3072).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        for face in ALL_FACES:
            x_scalar, x_conf = bridge.axis_projection(vec, face, "x")
            y_scalar, y_conf = bridge.axis_projection(vec, face, "y")

            assert 0.0 <= x_scalar <= 1.0
            assert 0.0 <= y_scalar <= 1.0
            assert 0.0 <= x_conf <= 1.0
            assert 0.0 <= y_conf <= 1.0
