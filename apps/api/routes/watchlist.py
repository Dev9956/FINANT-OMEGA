"""FININT OMEGA — Watchlist research API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.research.watchlist.engine import WatchlistResearchEngine
from core.research.watchlist.models import ConcurrencyConfig, WatchlistResearchRequest

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])

_engine = WatchlistResearchEngine()


class WatchlistResearchSubmitRequest(BaseModel):
    """Request body for submitting watchlist research."""

    symbols: list[str] = Field(description="List of symbols to research")
    question: str = Field(default="", description="Research question")
    max_workers: int = Field(default=5, description="Max concurrent workers")
    rate_limit_per_second: float = Field(default=10.0, description="Rate limit")
    priority: int = Field(default=0, description="Request priority")


class WatchlistResearchSubmitResponse(BaseModel):
    """Response for watchlist research submission."""

    request_id: str
    symbol_count: int
    status: str


@router.post("/research", response_model=WatchlistResearchSubmitResponse)
async def submit_research(request: WatchlistResearchSubmitRequest) -> WatchlistResearchSubmitResponse:
    """Submit watchlist research for batch processing."""
    config = ConcurrencyConfig(
        max_workers=request.max_workers,
        rate_limit_per_second=request.rate_limit_per_second,
    )
    watchlist_request = WatchlistResearchRequest(
        symbols=request.symbols,
        question=request.question,
        config=config,
        priority=request.priority,
    )
    request_id = _engine.submit_research(watchlist_request)
    return WatchlistResearchSubmitResponse(
        request_id=request_id,
        symbol_count=len(request.symbols),
        status="submitted",
    )


@router.get("/research/{request_id}")
async def get_results(request_id: str) -> dict:
    """Get results of a watchlist research request."""
    result = _engine.get_results(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Results not found: {request_id}")
    return result.model_dump(mode="json")


@router.get("/research/{request_id}/status")
async def get_status(request_id: str) -> dict:
    """Get progress of a watchlist research request."""
    progress = _engine.get_progress(request_id)
    if progress is None:
        raise HTTPException(status_code=404, detail=f"Request not found: {request_id}")
    return progress
