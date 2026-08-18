"""FININT OMEGA — M&A / transaction intelligence Pydantic models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Types of M&A / corporate transactions."""

    acquisition = "acquisition"
    merger = "merger"
    funding_round = "funding_round"
    ipo = "ipo"
    buyback = "buyback"
    strategic_investment = "strategic_investment"
    divestiture = "divestiture"


class DealStatus(str, Enum):
    """Status of a deal."""

    announced = "announced"
    completed = "completed"
    cancelled = "cancelled"


class Transaction(BaseModel):
    """A corporate transaction record."""

    transaction_id: str = Field(default_factory=lambda: str(uuid4()))
    transaction_type: TransactionType
    acquirer_symbol: str | None = None
    target_symbol: str | None = None
    deal_value: float | None = None
    deal_date: date
    status: DealStatus = DealStatus.announced
    currency: str = "USD"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DealImpact(BaseModel):
    """Assessed impact of a transaction."""

    transaction_id: str
    impact_on_sector: str = ""
    impact_on_competitors: list[str] = Field(default_factory=list)
    valuation_change: float | None = None
    risk_change: str = "neutral"
