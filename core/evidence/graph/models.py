"""FININT OMEGA — Evidence graph models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class EvidenceNodeType(str, Enum):
    CLAIM = "claim"
    EVIDENCE = "evidence"
    SOURCE = "source"
    CALCULATION = "calculation"
    DOCUMENT = "document"
    CONCLUSION = "conclusion"
    DATA_POINT = "data_point"


class GraphRelationship(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    SOURCED_FROM = "sourced_from"
    CALCULATED_BY = "calculated_by"
    REFERENCES = "references"
    STRENGTHENS = "strengthens"
    WEAKENS = "weakens"


class EvidenceNode(BaseModel):
    """A node in the evidence graph."""
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    node_type: EvidenceNodeType
    label: str
    content: str = ""
    confidence: float = 0.0
    source_id: str = ""
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceEdge(BaseModel):
    """An edge in the evidence graph."""
    edge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str
    target_node_id: str
    relationship: GraphRelationship
    weight: float = 1.0
    confidence: float = 0.0
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
