"""FININT OMEGA — Causal analysis models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class CausalRelationship(str, Enum):
    CAUSES = "causes"
    INFLUENCES = "influences"
    CORRELATED = "correlated"
    TEMPORAL = "temporal"
    INVERSE = "inverse"


class CausalConfidence(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    SPECULATIVE = "speculative"


class CausalNode(BaseModel):
    """A node in the causal graph."""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    label: str
    description: str = ""
    current_value: float | None = None
    unit: str = ""
    category: str = ""  # economic, financial, market, macro
    metadata: dict = Field(default_factory=dict)


class CausalEdge(BaseModel):
    """A directed edge in the causal graph."""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str
    target_node_id: str
    relationship: CausalRelationship
    confidence: CausalConfidence = CausalConfidence.MODERATE
    lag_periods: int = 0  # periods delay
    magnitude: float = 1.0
    evidence: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class CausalHypothesis(BaseModel):
    """A causal hypothesis chain."""
    hypothesis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    nodes: list[CausalNode] = Field(default_factory=list)
    edges: list[CausalEdge] = Field(default_factory=list)
    overall_confidence: CausalConfidence = CausalConfidence.MODERATE
    alternative_explanations: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    testable_predictions: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CausalGraph(BaseModel):
    """A complete causal graph."""
    graph_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nodes: list[CausalNode] = Field(default_factory=list)
    edges: list[CausalEdge] = Field(default_factory=list)
    hypotheses: list[CausalHypothesis] = Field(default_factory=list)
