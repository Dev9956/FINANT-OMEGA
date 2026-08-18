"""FININT OMEGA — Large watchlist research models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ConcurrencyConfig(BaseModel):
    """Configuration for concurrent watchlist research."""

    max_workers: int = 5
    rate_limit_per_second: float = 10.0
    retry_count: int = 3


class WatchlistResearchRequest(BaseModel):
    """A request for research on a watchlist of symbols."""

    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbols: list[str] = Field(default_factory=list)
    question: str = ""
    config: ConcurrencyConfig = Field(default_factory=ConcurrencyConfig)
    priority: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WatchlistResearchResult(BaseModel):
    """Results of a watchlist research batch."""

    request_id: str
    results: dict[str, Any] = Field(default_factory=dict)
    ranking: list[dict] = Field(default_factory=list)
    summary: str = ""
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    errors: dict[str, str] = Field(default_factory=dict)
    total_symbols: int = 0
    completed_symbols: int = 0
    failed_symbols: int = 0
