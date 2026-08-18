"""FININT OMEGA — Evidence Graph API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.evidence.graph.graph import EvidenceGraph
from core.evidence.graph.models import EvidenceEdge, EvidenceNode, EvidenceNodeType, GraphRelationship

router = APIRouter(prefix="/api/v1/intelligence/evidence-graph", tags=["evidence-graph"])

_graph: EvidenceGraph | None = None


def _get_graph() -> EvidenceGraph:
    global _graph
    if _graph is None:
        _graph = EvidenceGraph()
    return _graph


class AddNodeRequest(BaseModel):
    node_type: str
    label: str
    content: str = ""
    confidence: float = 0.0
    source_id: str = ""


class AddEdgeRequest(BaseModel):
    source_node_id: str
    target_node_id: str
    relationship: str
    weight: float = 1.0
    confidence: float = 0.0
    description: str = ""


@router.post("/nodes")
def add_node(req: AddNodeRequest):
    graph = _get_graph()
    node = EvidenceNode(
        node_type=EvidenceNodeType(req.node_type),
        label=req.label,
        content=req.content,
        confidence=req.confidence,
        source_id=req.source_id,
    )
    node_id = graph.add_node(node)
    return {"node_id": node_id}


@router.post("/edges")
def add_edge(req: AddEdgeRequest):
    graph = _get_graph()
    edge = EvidenceEdge(
        source_node_id=req.source_node_id,
        target_node_id=req.target_node_id,
        relationship=GraphRelationship(req.relationship),
        weight=req.weight,
        confidence=req.confidence,
        description=req.description,
    )
    try:
        edge_id = graph.add_edge(edge)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"edge_id": edge_id}


@router.get("/nodes/{node_id}")
def get_node(node_id: str):
    graph = _get_graph()
    node = graph.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.get("/nodes/{node_id}/supporting")
def get_supporting(node_id: str):
    graph = _get_graph()
    return graph.get_supporting_evidence(node_id)


@router.get("/nodes/{node_id}/contradicting")
def get_contradicting(node_id: str):
    graph = _get_graph()
    return graph.get_contradicting_evidence(node_id)


@router.get("/nodes/{node_id}/chain")
def get_evidence_chain(node_id: str):
    graph = _get_graph()
    chain = graph.get_conclusion_evidence_chain(node_id)
    if "error" in chain:
        raise HTTPException(status_code=400, detail=chain["error"])
    return chain


@router.get("/nodes/{node_id}/confidence")
def compute_confidence(node_id: str):
    graph = _get_graph()
    confidence = graph.compute_node_confidence(node_id)
    return {"node_id": node_id, "confidence": confidence}


@router.get("/search")
def search_nodes(q: str):
    graph = _get_graph()
    return graph.search(q)


@router.get("/stats")
def graph_stats():
    graph = _get_graph()
    return {
        "node_count": graph.node_count(),
        "edge_count": graph.edge_count(),
    }
