"""FININT OMEGA — Causal Analysis API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.intelligence.causal.engine import CausalEngine
from core.intelligence.causal.models import CausalNode

router = APIRouter(prefix="/api/v1/intelligence/causal", tags=["causal"])

_engine: CausalEngine | None = None


def _get_engine() -> CausalEngine:
    global _engine
    if _engine is None:
        _engine = CausalEngine()
    return _engine


class CreateGraphRequest(BaseModel):
    title: str = ""


class AddNodeRequest(BaseModel):
    label: str
    description: str = ""
    current_value: float | None = None
    unit: str = ""
    category: str = ""


class BuildChainRequest(BaseModel):
    cause: str
    effect: str
    intermediates: list[str] = Field(default_factory=list)


class EvaluateHypothesisRequest(BaseModel):
    evidence_for: list[str] = Field(default_factory=list)
    evidence_against: list[str] = Field(default_factory=list)


@router.post("/graphs")
def create_graph(req: CreateGraphRequest):
    engine = _get_engine()
    graph = engine.create_graph(title=req.title)
    return {"graph_id": graph.graph_id}


@router.post("/graphs/{graph_id}/nodes")
def add_node(graph_id: str, req: AddNodeRequest):
    engine = _get_engine()
    node = CausalNode(
        label=req.label,
        description=req.description,
        current_value=req.current_value,
        unit=req.unit,
        category=req.category,
    )
    try:
        node_id = engine.add_node(graph_id, node)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"node_id": node_id}


@router.post("/graphs/{graph_id}/chain")
def build_chain(graph_id: str, req: BuildChainRequest):
    engine = _get_engine()
    try:
        hypothesis = engine.build_causal_chain(
            graph_id, req.cause, req.effect, req.intermediates,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return hypothesis


@router.get("/hypotheses/{hypothesis_id}")
def get_hypothesis(hypothesis_id: str):
    engine = _get_engine()
    h = engine.get_hypothesis(hypothesis_id)
    if h is None:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return h


@router.post("/hypotheses/{hypothesis_id}/evaluate")
def evaluate_hypothesis(hypothesis_id: str, req: EvaluateHypothesisRequest):
    engine = _get_engine()
    result = engine.evaluate_hypothesis(
        hypothesis_id,
        evidence_for=req.evidence_for,
        evidence_against=req.evidence_against,
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/graphs")
def list_graphs():
    engine = _get_engine()
    return {"graphs": engine.list_graphs()}


@router.get("/hypotheses")
def list_hypotheses():
    engine = _get_engine()
    return {"hypotheses": engine.list_hypotheses()}
