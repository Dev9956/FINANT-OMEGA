"""Tests for Evidence Graph."""

import pytest
from core.evidence.graph.models import (
    EvidenceEdge,
    EvidenceNode,
    EvidenceNodeType,
    GraphRelationship,
)
from core.evidence.graph.graph import EvidenceGraph


class TestEvidenceGraph:
    def setup_method(self):
        self.graph = EvidenceGraph()

    def test_add_node(self):
        node = EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="Test claim")
        node_id = self.graph.add_node(node)
        assert node_id == node.node_id
        assert self.graph.node_count() == 1

    def test_add_edge(self):
        n1 = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="Evidence A")
        n2 = EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="Claim B")
        self.graph.add_node(n1)
        self.graph.add_node(n2)

        edge = EvidenceEdge(
            source_node_id=n1.node_id,
            target_node_id=n2.node_id,
            relationship=GraphRelationship.SUPPORTS,
        )
        edge_id = self.graph.add_edge(edge)
        assert edge_id == edge.edge_id
        assert self.graph.edge_count() == 1

    def test_add_edge_missing_node(self):
        n1 = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="Evidence A")
        self.graph.add_node(n1)

        edge = EvidenceEdge(
            source_node_id=n1.node_id,
            target_node_id="nonexistent",
            relationship=GraphRelationship.SUPPORTS,
        )
        with pytest.raises(ValueError):
            self.graph.add_edge(edge)

    def test_get_supporting_evidence(self):
        evidence = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="E1", confidence=0.9)
        claim = EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="C1")
        self.graph.add_node(evidence)
        self.graph.add_node(claim)

        self.graph.add_edge(EvidenceEdge(
            source_node_id=evidence.node_id,
            target_node_id=claim.node_id,
            relationship=GraphRelationship.SUPPORTS,
        ))

        supporting = self.graph.get_supporting_evidence(claim.node_id)
        assert len(supporting) == 1
        assert supporting[0].node_id == evidence.node_id

    def test_get_contradicting_evidence(self):
        evidence = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="E1")
        claim = EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="C1")
        self.graph.add_node(evidence)
        self.graph.add_node(claim)

        self.graph.add_edge(EvidenceEdge(
            source_node_id=evidence.node_id,
            target_node_id=claim.node_id,
            relationship=GraphRelationship.CONTRADICTS,
        ))

        contradicting = self.graph.get_contradicting_evidence(claim.node_id)
        assert len(contradicting) == 1

    def test_get_conclusion_evidence_chain(self):
        source = EvidenceNode(node_type=EvidenceNodeType.SOURCE, label="SEC Filing")
        evidence = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="Revenue data")
        conclusion = EvidenceNode(node_type=EvidenceNodeType.CONCLUSION, label="Revenue growing")

        self.graph.add_node(source)
        self.graph.add_node(evidence)
        self.graph.add_node(conclusion)

        self.graph.add_edge(EvidenceEdge(
            source_node_id=source.node_id,
            target_node_id=evidence.node_id,
            relationship=GraphRelationship.SOURCED_FROM,
        ))
        self.graph.add_edge(EvidenceEdge(
            source_node_id=evidence.node_id,
            target_node_id=conclusion.node_id,
            relationship=GraphRelationship.SUPPORTS,
        ))

        chain = self.graph.get_conclusion_evidence_chain(conclusion.node_id)
        assert chain["supporting_count"] == 1
        assert chain["contradicting_count"] == 0
        assert len(chain["evidence_chain"]) == 1

    def test_compute_node_confidence(self):
        e1 = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="E1", confidence=0.9)
        e2 = EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="E2", confidence=0.7)
        claim = EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="C1", confidence=0.5)
        self.graph.add_node(e1)
        self.graph.add_node(e2)
        self.graph.add_node(claim)

        self.graph.add_edge(EvidenceEdge(
            source_node_id=e1.node_id, target_node_id=claim.node_id,
            relationship=GraphRelationship.SUPPORTS,
        ))
        self.graph.add_edge(EvidenceEdge(
            source_node_id=e2.node_id, target_node_id=claim.node_id,
            relationship=GraphRelationship.SUPPORTS,
        ))

        conf = self.graph.compute_node_confidence(claim.node_id)
        assert 0.0 <= conf <= 1.0

    def test_search(self):
        node = EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="Apple revenue growing")
        self.graph.add_node(node)
        results = self.graph.search("apple")
        assert len(results) == 1

    def test_nodes_by_type(self):
        self.graph.add_node(EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="C1"))
        self.graph.add_node(EvidenceNode(node_type=EvidenceNodeType.EVIDENCE, label="E1"))
        self.graph.add_node(EvidenceNode(node_type=EvidenceNodeType.CLAIM, label="C2"))

        claims = self.graph.nodes_by_type(EvidenceNodeType.CLAIM)
        assert len(claims) == 2
