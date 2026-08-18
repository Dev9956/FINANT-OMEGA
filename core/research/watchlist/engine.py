"""FININT OMEGA — Watchlist research engine for large-scale parallel analysis."""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from core.research.watchlist.models import (
    ConcurrencyConfig,
    WatchlistResearchRequest,
    WatchlistResearchResult,
)

logger = structlog.get_logger()


class WatchlistResearchEngine:
    """Execute research across large watchlists with concurrency control."""

    def __init__(self) -> None:
        self._requests: dict[str, WatchlistResearchRequest] = {}
        self._results: dict[str, WatchlistResearchResult] = {}
        self._progress: dict[str, dict[str, int]] = {}

    def submit_research(self, request: WatchlistResearchRequest) -> str:
        """Submit a watchlist research request. Returns request_id."""
        self._requests[request.request_id] = request
        self._progress[request.request_id] = {
            "total": len(request.symbols),
            "completed": 0,
            "failed": 0,
        }
        logger.info(
            "watchlist_research_submitted",
            request_id=request.request_id,
            symbol_count=len(request.symbols),
        )
        return request.request_id

    def execute_batch(
        self,
        request: WatchlistResearchRequest,
        symbol_processor: Any = None,
    ) -> WatchlistResearchResult:
        """Execute research for all symbols in the request."""
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}
        completed = 0
        failed = 0

        for symbol in request.symbols:
            try:
                if symbol_processor:
                    result = symbol_processor(symbol, request.question)
                else:
                    result = self.process_symbol(symbol, request.question)
                results[symbol] = result
                completed += 1
            except Exception as e:
                errors[symbol] = str(e)
                failed += 1
                logger.warning(
                    "symbol_failed",
                    symbol=symbol,
                    error=str(e),
                )
            self._progress[request.request_id] = {
                "total": len(request.symbols),
                "completed": completed,
                "failed": failed,
            }

        ranking = self.rank_results(results, request.question)
        summary = self.aggregate_summary(results)

        result = WatchlistResearchResult(
            request_id=request.request_id,
            results=results,
            ranking=ranking,
            summary=summary,
            completed_at=datetime.now(timezone.utc),
            errors=errors,
            total_symbols=len(request.symbols),
            completed_symbols=completed,
            failed_symbols=failed,
        )
        self._results[request.request_id] = result
        return result

    async def execute_batch_async(
        self,
        request: WatchlistResearchRequest,
        symbol_processor: Any = None,
    ) -> WatchlistResearchResult:
        """Execute research asynchronously with concurrency control."""
        semaphore = asyncio.Semaphore(request.config.max_workers)
        rate_limit = 1.0 / request.config.rate_limit_per_second
        results: dict[str, Any] = {}
        errors: dict[str, str] = {}
        completed = 0
        failed = 0

        async def process_with_semaphore(sym: str) -> tuple[str, Any, str | None]:
            async with semaphore:
                await asyncio.sleep(rate_limit)
                try:
                    if symbol_processor and asyncio.iscoroutinefunction(symbol_processor):
                        res = await symbol_processor(sym, request.question)
                    else:
                        res = self.process_symbol(sym, request.question)
                    return sym, res, None
                except Exception as e:
                    return sym, None, str(e)

        tasks = [process_with_semaphore(sym) for sym in request.symbols]
        for coro in asyncio.as_completed(tasks):
            sym, result, error = await coro
            if error:
                errors[sym] = error
                failed += 1
            else:
                results[sym] = result
                completed += 1
            self._progress[request.request_id] = {
                "total": len(request.symbols),
                "completed": completed,
                "failed": failed,
            }

        ranking = self.rank_results(results, request.question)
        summary = self.aggregate_summary(results)

        res = WatchlistResearchResult(
            request_id=request.request_id,
            results=results,
            ranking=ranking,
            summary=summary,
            completed_at=datetime.now(timezone.utc),
            errors=errors,
            total_symbols=len(request.symbols),
            completed_symbols=completed,
            failed_symbols=failed,
        )
        self._results[request.request_id] = res
        return res

    def process_symbol(self, symbol: str, question: str) -> dict:
        """Process research for a single symbol (stub)."""
        return {
            "symbol": symbol,
            "question": question,
            "status": "completed",
            "metrics": {
                "revenue_growth": None,
                "roe": None,
                "pe_ratio": None,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def rank_results(self, results: dict[str, Any], criteria: str) -> list[dict]:
        """Rank results based on criteria."""
        ranked = []
        for symbol, data in results.items():
            score = self._compute_rank_score(data, criteria)
            ranked.append({
                "symbol": symbol,
                "score": score,
                "data": data,
            })
        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked

    def aggregate_summary(self, results: dict[str, Any]) -> str:
        """Aggregate results into a summary."""
        if not results:
            return "No results to summarize."
        total = len(results)
        completed = sum(1 for r in results.values() if r.get("status") == "completed")
        return (
            f"Analyzed {total} symbols. "
            f"{completed} completed successfully. "
            f"{total - completed} failed or incomplete."
        )

    def get_progress(self, request_id: str) -> dict[str, int] | None:
        """Get progress for a research request."""
        return self._progress.get(request_id)

    def get_results(self, request_id: str) -> WatchlistResearchResult | None:
        """Get results for a completed request."""
        return self._results.get(request_id)

    def _compute_rank_score(self, data: dict, criteria: str) -> float:
        """Compute a ranking score for a symbol."""
        score = 0.0
        metrics = data.get("metrics", {})
        if metrics.get("revenue_growth") is not None:
            score += max(0, metrics["revenue_growth"])
        if metrics.get("roe") is not None:
            score += max(0, metrics["roe"]) * 0.5
        if metrics.get("pe_ratio") is not None and 0 < metrics["pe_ratio"] < 50:
            score += (50 - metrics["pe_ratio"]) * 0.1
        return round(score, 2)
