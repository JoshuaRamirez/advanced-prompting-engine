"""Tests for Graph Query Layer (v2: faces, 12x12 grid)."""

import networkx as nx
import pytest

from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.graph.schema import CUBE_PAIRS, NexusTier


@pytest.fixture
def sample_graph():
    """Small graph with 2 faces, a few constructs, 1 nexus."""
    G = nx.DiGraph()
    # Faces
    G.add_node("ontology", type="face", tier=1, provenance="canonical")
    G.add_node("epistemology", type="face", tier=1, provenance="canonical")
    # Constructs
    G.add_node("ontology.0_0", type="construct", face="ontology", x=0, y=0,
               classification="corner", potency=1.0, provenance="canonical",
               question="Q1", tags=["test"])
    G.add_node("ontology.5_5", type="construct", face="ontology", x=5, y=5,
               classification="center", potency=0.6, provenance="canonical",
               question="Q2", tags=["test"])
    G.add_node("ontology.11_11", type="construct", face="ontology", x=11, y=11,
               classification="corner", potency=1.0, provenance="canonical",
               question="Q3", tags=["test"])
    G.add_node("epistemology.0_0", type="construct", face="epistemology", x=0, y=0,
               classification="corner", potency=1.0, provenance="canonical",
               question="Q4", tags=["test"])
    # Spectrum opposition
    G.add_edge("ontology.0_0", "ontology.11_11", relation="SPECTRUM_OPPOSITION",
               strength=0.6)
    # Nexus
    G.add_node("nexus.ontology.epistemology", type="nexus",
               source_face="ontology", target_face="epistemology",
               cube_tier="adjacent", provenance="canonical")
    # HAS_CONSTRUCT
    G.add_edge("ontology", "ontology.0_0", relation="HAS_CONSTRUCT")
    return G


@pytest.fixture
def query_layer(sample_graph):
    return GraphQueryLayer(sample_graph)


class TestFaces:
    def test_list_faces(self, query_layer):
        faces = query_layer.list_faces()
        assert len(faces) == 2
        names = {f["id"] for f in faces}
        assert "ontology" in names
        assert "epistemology" in names


class TestConstructs:
    def test_list_by_face(self, query_layer):
        constructs = query_layer.list_constructs("ontology")
        assert len(constructs) == 3

    def test_list_by_classification(self, query_layer):
        corners = query_layer.list_constructs("ontology", classification="corner")
        assert len(corners) == 2

    def test_get_construct(self, query_layer):
        c = query_layer.get_construct("ontology", 0, 0)
        assert c is not None
        assert c["classification"] == "corner"

    def test_get_construct_missing(self, query_layer):
        assert query_layer.get_construct("ontology", 3, 3) is None

    def test_get_construct_by_id(self, query_layer):
        c = query_layer.get_construct_by_id("ontology.0_0")
        assert c is not None
        assert c["potency"] == 1.0


class TestSpectrums:
    def test_get_spectrum_opposite(self, query_layer):
        opp = query_layer.get_spectrum_opposite("ontology", 0, 0)
        assert opp is not None
        assert opp["id"] == "ontology.11_11"

    def test_get_spectrum_opposite_center(self, query_layer):
        """Center constructs have no spectrum opposite."""
        opp = query_layer.get_spectrum_opposite("ontology", 5, 5)
        assert opp is None

    def test_get_edge_constructs(self, query_layer):
        edges = query_layer.get_edge_constructs("ontology")
        assert len(edges) == 2  # two corners, no midpoints/edge in this graph


class TestNexus:
    def test_get_nexus(self, query_layer):
        n = query_layer.get_nexus("ontology", "epistemology")
        assert n is not None
        assert n["source_face"] == "ontology"

    def test_get_nexus_missing(self, query_layer):
        assert query_layer.get_nexus("heuristics", "semiotics") is None

    def test_get_spoke(self, query_layer):
        spoke = query_layer.get_spoke("ontology")
        assert len(spoke) == 1  # only 1 nexus from ontology in this graph

    def test_cube_tier_on_nexus(self, query_layer):
        n = query_layer.get_nexus("ontology", "epistemology")
        assert n["cube_tier"] == "adjacent"


class TestCubePairing:
    def test_get_paired_face(self, query_layer):
        assert query_layer.get_paired_face("ontology") == "praxeology"
        assert query_layer.get_paired_face("praxeology") == "ontology"

    def test_get_paired_face_nonexistent(self, query_layer):
        assert query_layer.get_paired_face("nonexistent") is None

    def test_get_nexus_by_tier(self, query_layer):
        adjacent = query_layer.get_nexus_by_tier("adjacent")
        assert len(adjacent) == 1  # only 1 nexus in the sample graph


class TestPaths:
    def test_find_path(self, query_layer):
        path = query_layer.find_path("ontology", "ontology.0_0")
        assert len(path) > 0

    def test_find_path_no_path(self, query_layer):
        path = query_layer.find_path("ontology.0_0", "epistemology.0_0")
        assert isinstance(path, list)
