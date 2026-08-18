"""FININT OMEGA — Generative Research Grid models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEXT = "text"


class ColumnSpec(BaseModel):
    """Specification for a grid column."""

    column_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    metric_type: MetricType = MetricType.NUMERIC
    source: str = ""
    calculation: str = ""
    evidence_required: bool = True
    description: str = ""


class RowSpec(BaseModel):
    """Specification for a grid row."""

    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = "company"
    entity_id: str
    entity_name: str


class GridSpec(BaseModel):
    """Specification for a research grid."""

    grid_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    rows: list[RowSpec] = Field(default_factory=list)
    columns: list[ColumnSpec] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    sorting: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class GridCell(BaseModel):
    """A single cell in a generated grid."""

    row_id: str
    column_id: str
    value: str | float | int | None = None
    unit: str = ""
    evidence_id: str | None = None
    confidence: float | None = None
    calculation_id: str | None = None


class GeneratedGrid(BaseModel):
    """A fully generated research grid."""

    grid_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    spec: GridSpec
    cells: list[GridCell] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_versions: dict[str, str] = Field(default_factory=dict)
    evidence_summary: dict = Field(default_factory=dict)
