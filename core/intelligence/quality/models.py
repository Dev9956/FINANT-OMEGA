"""FININT OMEGA — Quality models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class QualityDimension(str, Enum):
    EVIDENCE_COVERAGE = "evidence_coverage"
    SOURCE_QUALITY = "source_quality"
    NUMERICAL_ACCURACY = "numerical_accuracy"
    FRESHNESS = "freshness"
    CONTRADICTION_HANDLING = "contradiction_handling"
    COMPLETENESS = "completeness"
    UNCERTAINTY = "uncertainty"
    REPRODUCIBILITY = "reproducibility"


class QualityResult(BaseModel):
    """Research quality scoring result."""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    overall_score: float = 0.0
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    grade: str = ""
    recommendations: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))