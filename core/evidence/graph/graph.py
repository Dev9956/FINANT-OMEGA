"""FININT OMEGA — Evidence graph for tracking evidence relationships."""

from __future__ import annotations

from collections import defaultdict, deque

from core.evidence.graph.models import (
    EvidenceEdge,
    EvidenceNode,
    EvidenceNodeType,
    GraphRelationship,
)


class EvidenceGraph:
    """Graph-based evidence tracking supporting supporting/contradicting/derived relationships."""

    def __init__(self) -> None:
        self._nodes: dict[str, EvidenceNode] = {}
        self._edges: dict[str, EvidenceEdge] = {}
        self._adjacency: dict[str, list[str]] = defaultdict(list)
        self._reverse_adjacency: dict[str, list[str]] = defaultdict(list)

    def add_node(self, node: EvidenceNode) -> str:
        self._nodes[node.node_id] = node
        return node.node_id

    def add_edge(self, edge: EvidenceEdge) -> str:
        if edge.source_node_id not in self._nodes:
            raise ValueError(f"Source node {edge.source_node_id} not found")
        if edge.target_node_id not in self._nodes:
            raise ValueError(f"Target node {edge.target_node_id} not found")
        self._edges[edge.edge_id] = edge
        self._adjacency[edge.source_node_id].append(edge.edge_id)
        self._reverse_adjacency[edge.target_node_id].append(edge.edge_id)
        return edge.edge_id

    def get_node(self, node_id: str) -> EvidenceNode | None:
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> EvidenceEdge | None:
        return self._edges.get(edge_id)

    def get_supporting_evidence(self, node_id: str) -> list[EvidenceNode]:
        supporting = []
        for edge_id in self._reverse_adjacency.get(node_id, []):
            edge = self._edges.get(edge_id)
            if edge and edge.relationship in (GraphRelationship.SUPPORTS, GraphRelationship.STRENGTHENS):
                node = self._nodes.get(edge.source_node_id)
                if node:
                    supporting.append(node)
        return supporting

    def get_contradicting_evidence(self, node_id: str) -> list[EvidenceNode]:
        contradicting = []
        for edge_id in self._reverse_adjacency.get(node_id, []):
            edge = self._edges.get(edge_id)
            if edge and edge.relationship in (GraphRelationship.CONTRADICTS, GraphRelationship.WEAKENS):
                node = self._nodes.get(edge.source_node_id)
                if node:
                    contradicting.append(node)
        return contradicting

    def get_derived_from(self, node_id: str) -> list[EvidenceNode]:
        derived = []
        for edge_id in self._adjacency.get(node_id, []):
            edge = self._edges.get(edge_id)
            if edge and edge.relationship == GraphRelationship.DERIVED_FROM:
                node = self._nodes.get(edge.target_node_id)
                if node:
                    derived.append(node)
        return derived

    def get_source_nodes(self, node_id: str) -> list[EvidenceNode]:
        sources = []
        for edge_id in self._adjacency.get(node_id, []):
            edge = self._edges.get(edge_id)
            if edge and edge.relationship == GraphRelationship.SOURCED_FROM:
                node = self._nodes.get(edge.target_node_id)
                if node:
                    sources.append(node)
        return sources

    def get_conclusion_evidence_chain(self, conclusion_id: str) -> dict:
        conclusion = self._nodes.get(conclusion_id)
        if not conclusion or conclusion.node_type != EvidenceNodeType.CONCLUSION:
            return {"error": "Not a conclusion node"}

        supporting = self.get_supporting_evidence(conclusion_id)
        contradicting = self.get_contradicting_evidence(conclusion_id)

        all_evidence = []
        for node in supporting + contradicting:
            sources = self.get_source_nodes(node.node_id)
            all_evidence.append({
                "evidence": node,
                "sources": sources,
                "relationship": "supports" if node in supporting else "contradicts",
            })

        return {
            "conclusion": conclusion,
            "supporting_count": len(supporting),
            "contradicting_count": len(contradicting),
            "evidence_chain": all_evidence,
            "total_evidence": len(supporting) + len(contradicting),
        }

    def compute_node_confidence(self, node_id: str) -> float:
        node = self._nodes.get(node_id)
        if not node:
            return 0.0

        supporting = self.get_supporting_evidence(node_id)
        contradicting = self.get_contradicting_evidence(node_id)

        if not supporting and not contradicting:
            return node.confidence

        support_score = sum(e.confidence for e in supporting) / max(len(supporting), 1)
        contra_score = sum(e.confidence for e in contradicting) / max(len(contradicting), 1)

        total = support_score + contra_score
        if total == 0:
            return 0.5

        return support_score / total

    def search(self, query: str) -> list[EvidenceNode]:
        query_lower = query.lower()
        return [
            node for node in self._nodes.values()
            if query_lower in node.label.lower() or query_lower in node.content.lower()
        ]

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def nodes_by_type(self, node_type: EvidenceNodeType) -> list[EvidenceNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def edges_by_relationship(self, relationship: GraphRelationship) -> list[EvidenceEdge]:
        return [e for e in self._edges.values() if e.relationship == relationship]
