"""FININT OMEGA — Corporate actions Pydantic models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of corporate actions."""

    split = "split"
    bonus = "bonus"
    dividend = "dividend"
    rights = "rights"
    buyback = "buyback"
    merger = "merger"
    acquisition = "acquisition"
    spinoff = "spinoff"
    demerger = "demerger"
    delisting = "delisting"


class CorporateActionRecord(BaseModel):
    """A corporate action event."""

    action_id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    action_type: ActionType
    ex_date: date
    effective_date: date | None = None
    ratio: float | None = None
    dividend_per_share: float | None = None
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AdjustmentFactor(BaseModel):
    """Cumulative adjustment factor for a symbol on a date."""

    symbol: str
    date: date
    factor: float
    reason: str


class ActionAdjustedPrice(BaseModel):
    """Price after corporate action adjustment."""

    symbol: str
    date: date
    adjusted_close: float
    original_close: float
    adjustment_factor: float
