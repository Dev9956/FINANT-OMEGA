"""FININT OMEGA — Causal Analysis Engine."""

from __future__ import annotations

from core.intelligence.causal.models import (
    CausalConfidence,
    CausalEdge,
    CausalGraph,
    CausalHypothesis,
    CausalNode,
    CausalRelationship,
)


class CausalEngine:
    """Build and evaluate causal hypotheses from financial data."""

    def __init__(self) -> None:
        self._graphs: dict[str, CausalGraph] = {}
        self._hypotheses: dict[str, CausalHypothesis] = {}

    def create_graph(self, title: str = "") -> CausalGraph:
        graph = CausalGraph()
        self._graphs[graph.graph_id] = graph
        return graph

    def add_node(self, graph_id: str, node: CausalNode) -> str:
        graph = self._graphs.get(graph_id)
        if graph is None:
            raise ValueError(f"Graph {graph_id} not found")
        graph.nodes.append(node)
        return node.node_id

    def add_edge(self, graph_id: str, edge: CausalEdge) -> str:
        graph = self._graphs.get(graph_id)
        if graph is None:
            raise ValueError(f"Graph {graph_id} not found")
        graph.edges.append(edge)
        return edge.edge_id

    def build_causal_chain(
        self,
        graph_id: str,
        cause: str,
        effect: str,
        intermediates: list[str] | None = None,
    ) -> CausalHypothesis:
        graph = self._graphs.get(graph_id)
        if graph is None:
            raise ValueError(f"Graph {graph_id} not found")

        nodes = []
        edges = []
        chain = [cause] + (intermediates or []) + [effect]

        for label in chain:
            node = CausalNode(label=label, category="financial")
            nodes.append(node)

        for i in range(len(nodes) - 1):
            edge = CausalEdge(
                source_node_id=nodes[i].node_id,
                target_node_id=nodes[i + 1].node_id,
                relationship=CausalRelationship.CAUSES,
                confidence=CausalConfidence.MODERATE,
            )
            edges.append(edge)

        hypothesis = CausalHypothesis(
            title=f"Causal chain: {cause} → {effect}",
            description=f"Proposed causal pathway from {cause} to {effect}",
            nodes=nodes,
            edges=edges,
            alternative_explanations=[
                f"Alternative: {effect} may be caused by factors other than {cause}",
                f"Alternative: Correlation between {cause} and {effect} may be spurious",
            ],
            testable_predictions=[
                f"If {cause} increases, {effect} should increase with lag",
                f"If {cause} decreases, {effect} should decrease with lag",
            ],
        )

        graph.hypotheses.append(hypothesis)
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis
        return hypothesis

    def get_hypothesis(self, hypothesis_id: str) -> CausalHypothesis | None:
        return self._hypotheses.get(hypothesis_id)

    def get_graph(self, graph_id: str) -> CausalGraph | None:
        return self._graphs.get(graph_id)

    def evaluate_hypothesis(
        self,
        hypothesis_id: str,
        evidence_for: list[str] | None = None,
        evidence_against: list[str] | None = None,
    ) -> dict:
        hypothesis = self._hypotheses.get(hypothesis_id)
        if hypothesis is None:
            return {"error": "Hypothesis not found"}

        evidence_for = evidence_for or []
        evidence_against = evidence_against or []

        total_evidence = len(evidence_for) + len(evidence_against)
        if total_evidence > 0:
            support_ratio = len(evidence_for) / total_evidence
        else:
            support_ratio = 0.5

        if support_ratio >= 0.75:
            confidence = CausalConfidence.HIGH
        elif support_ratio >= 0.5:
            confidence = CausalConfidence.MODERATE
        elif support_ratio >= 0.25:
            confidence = CausalConfidence.LOW
        else:
            confidence = CausalConfidence.SPECULATIVE

        return {
            "hypothesis_id": hypothesis_id,
            "confidence": confidence.value,
            "support_ratio": support_ratio,
            "evidence_for": len(evidence_for),
            "evidence_against": len(evidence_against),
            "recommendation": "Consider hypothesis" if support_ratio >= 0.5 else "Hypothesis weakly supported",
        }

    def list_graphs(self) -> list[CausalGraph]:
        return list(self._graphs.values())

    def list_hypotheses(self) -> list[CausalHypothesis]:
        return list(self._hypotheses.values())
