"""Tests for the geometry-integral intent parser.

Validates that the parser correctly inverts the Construct's 3-layer
inference machinery to produce coordinates from natural language intent.
"""

import pytest

from advanced_prompting_engine.graph.schema import ALL_FACES, GRID_SIZE, PipelineState
from advanced_prompting_engine.math.semantic import GeometricBridge
from advanced_prompting_engine.pipeline.intent_parser import IntentParser


@pytest.fixture(scope="module")
def parser():
    bridge = GeometricBridge()
    bridge.load()
    return IntentParser(geometric_bridge=bridge)


@pytest.fixture
def make_state():
    def _make(raw_input):
        return PipelineState(raw_input=raw_input)
    return _make


class TestPreformedCoordinate:
    def test_passthrough(self, parser, make_state):
        coord = {f: {"x": 5, "y": 5, "weight": 0.5} for f in ALL_FACES}
        state = make_state(coord)
        parser.execute(state)
        assert state.partial_coordinate == coord

    def test_validates_missing_face(self, parser, make_state):
        coord = {"ontology": {"x": 0, "y": 0, "weight": 1.0}}
        state = make_state(coord)
        with pytest.raises(ValueError, match="Missing face"):
            parser.execute(state)

    def test_validates_out_of_range(self, parser, make_state):
        coord = {f: {"x": 0, "y": 0, "weight": 0.5} for f in ALL_FACES}
        coord["ontology"]["x"] = 99
        state = make_state(coord)
        with pytest.raises(ValueError, match="out of range"):
            parser.execute(state)


class TestEmptyInput:
    def test_empty_string_all_none(self, parser, make_state):
        state = make_state("")
        parser.execute(state)
        assert all(v is None for v in state.partial_coordinate.values())

    def test_whitespace_all_none(self, parser, make_state):
        state = make_state("   ")
        parser.execute(state)
        assert all(v is None for v in state.partial_coordinate.values())


class TestNaturalLanguage:
    def test_produces_12_face_entries(self, parser, make_state):
        state = make_state("What is the nature of truth and knowledge?")
        parser.execute(state)
        assert len(state.partial_coordinate) == 12

    def test_activated_faces_have_required_keys(self, parser, make_state):
        state = make_state("How should we structure our moral reasoning?")
        parser.execute(state)
        for face, entry in state.partial_coordinate.items():
            if entry is not None:
                assert "x" in entry
                assert "y" in entry
                assert "weight" in entry
                assert "confidence" in entry

    def test_coordinates_in_valid_range(self, parser, make_state):
        state = make_state("Build a system for autonomous decision-making")
        parser.execute(state)
        max_coord = GRID_SIZE - 1
        for face, entry in state.partial_coordinate.items():
            if entry is not None:
                assert 0 <= entry["x"] <= max_coord
                assert 0 <= entry["y"] <= max_coord
                assert 0.1 <= entry["weight"] <= 1.0
                assert 0.0 <= entry["confidence"] <= 1.0

    def test_weights_vary_across_faces(self, parser, make_state):
        state = make_state("What moral obligations do we have to future generations?")
        parser.execute(state)
        activated = {f: e for f, e in state.partial_coordinate.items() if e is not None}
        if len(activated) > 1:
            weights = [e["weight"] for e in activated.values()]
            assert max(weights) > min(weights), "Weights should vary across faces"

    def test_positions_vary_across_faces(self, parser, make_state):
        """Different faces should generally land on different grid positions."""
        state = make_state("To be or not to be that is the question whether tis nobler in the mind to suffer")
        parser.execute(state)
        activated = {f: e for f, e in state.partial_coordinate.items() if e is not None}
        if len(activated) > 3:
            positions = [(e["x"], e["y"]) for e in activated.values()]
            unique_positions = set(positions)
            # At least some positions should differ
            assert len(unique_positions) > 1, "All faces landed on the same position"


class TestScalarToGrid:
    """Test the polarity convention mapping: 0.0 → 0, 1.0 → 11."""

    def test_low_maps_to_zero(self, parser):
        assert parser._scalar_to_grid(0.0) == 0

    def test_high_maps_to_max(self, parser):
        assert parser._scalar_to_grid(1.0) == GRID_SIZE - 1

    def test_center_maps_to_middle(self, parser):
        mid = parser._scalar_to_grid(0.5)
        assert mid in (5, 6)  # dual midpoints

    def test_clamps_below_zero(self, parser):
        assert parser._scalar_to_grid(-0.1) == 0

    def test_clamps_above_one(self, parser):
        assert parser._scalar_to_grid(1.1) == GRID_SIZE - 1


class TestTokenization:
    def test_lowercases(self, parser):
        tokens = parser._tokenize("TRUTH Knowledge VERIFY")
        assert all(t == t.lower() for t in tokens)

    def test_removes_punctuation(self, parser):
        tokens = parser._tokenize("What? How! Why; truth, knowledge.")
        assert all(c.isalpha() for t in tokens for c in t)

    def test_removes_stop_words(self, parser):
        tokens = parser._tokenize("What is the nature of truth?")
        assert "what" not in tokens
        assert "is" not in tokens
        assert "the" not in tokens
        assert "of" not in tokens

    def test_preserves_content_words(self, parser):
        tokens = parser._tokenize("moral obligation duty ethics")
        assert "moral" in tokens
        assert "obligation" in tokens
        assert "duty" in tokens
        assert "ethics" in tokens

    def test_unstemmed(self, parser):
        """GloVe needs word forms, not stems."""
        tokens = parser._tokenize("obligations duties morality")
        assert "obligations" in tokens  # not "oblig"
        assert "duties" in tokens       # not "duti"
        assert "morality" in tokens     # not "mor"


class TestGracefulDegradation:
    def test_no_bridge_all_none(self, make_state):
        parser = IntentParser(geometric_bridge=None)
        state = make_state("What is truth?")
        parser.execute(state)
        assert all(v is None for v in state.partial_coordinate.values())

    def test_unloaded_bridge_all_none(self, make_state):
        bridge = GeometricBridge()  # don't load
        parser = IntentParser(geometric_bridge=bridge)
        state = make_state("What is truth?")
        parser.execute(state)
        assert all(v is None for v in state.partial_coordinate.values())
