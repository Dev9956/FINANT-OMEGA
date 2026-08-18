"""Tests for the Large Watchlist Research module."""

from __future__ import annotations

import pytest

from core.research.watchlist.engine import WatchlistResearchEngine
from core.research.watchlist.models import (
    ConcurrencyConfig,
    WatchlistResearchRequest,
    WatchlistResearchResult,
)


class TestWatchlistResearchEngine:
    """Tests for WatchlistResearchEngine."""

    def setup_method(self) -> None:
        self.engine = WatchlistResearchEngine()

    def test_submit_research(self) -> None:
        request = WatchlistResearchRequest(
            symbols=["AAPL", "MSFT", "GOOGL"],
            question="Compare financial health",
        )
        request_id = self.engine.submit_research(request)
        assert request_id == request.request_id

    def test_process_symbol(self) -> None:
        result = self.engine.process_symbol("AAPL", "What is the PE ratio?")
        assert result["symbol"] == "AAPL"
        assert result["status"] == "completed"

    def test_execute_batch(self) -> None:
        request = WatchlistResearchRequest(
            symbols=["AAPL", "MSFT"],
            question="Analyze",
        )
        self.engine.submit_research(request)
        result = self.engine.execute_batch(request)
        assert isinstance(result, WatchlistResearchResult)
        assert result.total_symbols == 2
        assert result.completed_symbols == 2
        assert result.failed_symbols == 0

    def test_execute_batch_partial_failure(self) -> None:
        request = WatchlistResearchRequest(
            symbols=["AAPL", "FAIL_SYMBOL"],
            question="Analyze",
        )

        def processor(symbol: str, question: str) -> dict:
            if symbol == "FAIL_SYMBOL":
                raise ValueError("Symbol not found")
            return {"symbol": symbol, "status": "ok"}

        self.engine.submit_research(request)
        result = self.engine.execute_batch(request, symbol_processor=processor)
        assert result.completed_symbols == 1
        assert result.failed_symbols == 1
        assert "FAIL_SYMBOL" in result.errors

    def test_rank_results(self) -> None:
        results = {
            "AAPL": {"metrics": {"roe": 15.0, "pe_ratio": 28.0}},
            "MSFT": {"metrics": {"roe": 20.0, "pe_ratio": 35.0}},
        }
        ranking = self.engine.rank_results(results, "best ROE")
        assert len(ranking) == 2
        assert ranking[0]["symbol"] == "MSFT"

    def test_aggregate_summary(self) -> None:
        results = {
            "AAPL": {"status": "completed"},
            "MSFT": {"status": "completed"},
        }
        summary = self.engine.aggregate_summary(results)
        assert "2" in summary
        assert "completed" in summary

    def test_aggregate_summary_empty(self) -> None:
        summary = self.engine.aggregate_summary({})
        assert "No results" in summary

    def test_get_progress(self) -> None:
        request = WatchlistResearchRequest(symbols=["A", "B", "C"])
        self.engine.submit_research(request)
        progress = self.engine.get_progress(request.request_id)
        assert progress is not None
        assert progress["total"] == 3

    def test_get_results(self) -> None:
        request = WatchlistResearchRequest(symbols=["AAPL"])
        self.engine.submit_research(request)
        self.engine.execute_batch(request)
        result = self.engine.get_results(request.request_id)
        assert result is not None
        assert result.completed_symbols == 1

    def test_execute_batch_with_custom_processor(self) -> None:
        request = WatchlistResearchRequest(
            symbols=["AAPL", "MSFT"],
            question="Analyze",
        )

        def custom_processor(symbol: str, question: str) -> dict:
            return {"symbol": symbol, "custom": True, "score": 42}

        self.engine.submit_research(request)
        result = self.engine.execute_batch(request, symbol_processor=custom_processor)
        assert result.results["AAPL"]["custom"] is True
        assert result.results["MSFT"]["score"] == 42

    def test_ranking_order(self) -> None:
        results = {
            "A": {"metrics": {"roe": 5.0}},
            "B": {"metrics": {"roe": 25.0}},
            "C": {"metrics": {"roe": 15.0}},
        }
        ranking = self.engine.rank_results(results, "roe")
        assert ranking[0]["symbol"] == "B"
        assert ranking[-1]["symbol"] == "A"

    def test_watchlist_result_model(self) -> None:
        result = WatchlistResearchResult(
            request_id="test-123",
            results={"AAPL": {"status": "ok"}},
            ranking=[{"symbol": "AAPL", "score": 10}],
            summary="Test summary",
            total_symbols=1,
            completed_symbols=1,
        )
        assert result.request_id == "test-123"
        assert result.errors == {}
