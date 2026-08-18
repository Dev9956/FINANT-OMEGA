"""FININT OMEGA — Prediction models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class PredictionStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class PredictionRecord(BaseModel):
    """A tracked prediction."""
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity: str
    prediction_text: str
    metric: str = ""
    predicted_value: float | None = None
    direction: str = ""  # up, down, stable
    confidence: float = 0.5
    horizon_days: int = 30
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    status: PredictionStatus = PredictionStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None


class PredictionOutcome(BaseModel):
    """Outcome of a prediction."""
    prediction_id: str
    actual_value: float | None = None
    error: float | None = None
    direction_correct: bool | None = None
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CalibrationResult(BaseModel):
    """Calibration analysis result."""
    confidence_bucket: str
    total_predictions: int
    correct_predictions: int
    accuracy: float = 0.0
    avg_confidence: float = 0.0
    calibration_error: float = 0.0
