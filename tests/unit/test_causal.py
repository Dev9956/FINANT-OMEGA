"""Tests for Causal Analysis Engine."""

import pytest
from core.intelligence.causal.models import (
    CausalConfidence,
    CausalNode,
    CausalRelationship,
)
from core.intelligence.causal.engine import CausalEngine


class TestCausalEngine:
    def setup_method(self):
        self.engine = CausalEngine()

    def test_create_graph(self):
        graph = self.engine.create_graph(title="Test Graph")
        assert graph.graph_id
        assert len(self.engine.list_graphs()) == 1

    def test_add_node(self):
        graph = self.engine.create_graph()
        node = CausalNode(label="Oil Price")
        node_id = self.engine.add_node(graph.graph_id, node)
        assert node_id == node.node_id

    def test_add_node_invalid_graph(self):
        node = CausalNode(label="Test")
        with pytest.raises(ValueError):
            self.engine.add_node("nonexistent", node)

    def test_build_causal_chain(self):
        graph = self.engine.create_graph()
        hypothesis = self.engine.build_causal_chain(
            graph.graph_id,
            cause="Oil Price Increase",
            effect="Inflation",
            intermediates=["Transportation Costs"],
        )
        assert len(hypothesis.nodes) == 3
        assert len(hypothesis.edges) == 2
        assert len(hypothesis.alternative_explanations) > 0
        assert len(hypothesis.testable_predictions) > 0

    def test_get_hypothesis(self):
        graph = self.engine.create_graph()
        h = self.engine.build_causal_chain(graph.graph_id, "A", "B")
        retrieved = self.engine.get_hypothesis(h.hypothesis_id)
        assert retrieved is not None

    def test_get_hypothesis_not_found(self):
        assert self.engine.get_hypothesis("nonexistent") is None

    def test_evaluate_hypothesis_strong_support(self):
        graph = self.engine.create_graph()
        h = self.engine.build_causal_chain(graph.graph_id, "A", "B")
        result = self.engine.evaluate_hypothesis(
            h.hypothesis_id,
            evidence_for=["E1", "E2", "E3", "E4"],
            evidence_against=["E1"],
        )
        assert result["confidence"] == "high"
        assert result["support_ratio"] >= 0.75

    def test_evaluate_hypothesis_weak_support(self):
        graph = self.engine.create_graph()
        h = self.engine.build_causal_chain(graph.graph_id, "A", "B")
        result = self.engine.evaluate_hypothesis(
            h.hypothesis_id,
            evidence_for=["E1"],
            evidence_against=["E1", "E2", "E3", "E4"],
        )
        assert result["confidence"] == "speculative"

    def test_list_graphs(self):
        self.engine.create_graph("G1")
        self.engine.create_graph("G2")
        assert len(self.engine.list_graphs()) == 2

    def test_list_hypotheses(self):
        graph = self.engine.create_graph()
        self.engine.build_causal_chain(graph.graph_id, "A", "B")
        self.engine.build_causal_chain(graph.graph_id, "C", "D")
        assert len(self.engine.list_hypotheses()) == 2
