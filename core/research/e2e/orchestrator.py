"""FININT OMEGA — End-to-end research orchestrator.

Wires real data connectors, real LLM, RAG retrieval, and the evidence
pipeline into a single runnable system with graceful fallback.
"""

from __future__ import annotations

import os
from typing import Any

import structlog

from core.research.evidence_pipeline.pipeline import EvidencePipeline, PipelineResult
from core.data.connectors.base import (
    ConnectorConfig,
    DataQuality,
    DataRecord,
    get_connector,
)

logger = structlog.get_logger()

# Provider preference order — real first, mock fallback
PROVIDER_PREFERENCE = {
    "market_data": ["yfinance_market", "mock_market"],
    "earnings_data": ["yfinance_earnings", "mock_fundamentals"],
    "fundamentals": ["yfinance_fundamentals", "mock_fundamentals"],
    "macro_data": ["fred", "mock_macro"],
}


class E2EResearchOrchestrator:
    """Runs real end-to-end research with graceful degradation."""

    def __init__(self) -> None:
        self._pipeline = EvidencePipeline()
        self._use_real = os.environ.get("FININT_REAL_DATA", "").lower() in {"1", "true", "yes"}
        self._register_tools()

    def _register_tools(self) -> None:
        """Register data tools that prefer real providers with mock fallback."""
        self._pipeline.register_tool("market_data", self._make_data_tool("market_data"))
        self._pipeline.register_tool("earnings_data", self._make_data_tool("earnings_data"))
        self._pipeline.register_tool("fundamentals", self._make_data_tool("fundamentals"))
        self._pipeline.register_tool("macro_data", self._make_data_tool("macro_data"))

    def _make_data_tool(self, kind: str):
        def tool(**kwargs: Any):
            symbol = kwargs.get("symbol", "")
            question = kwargs.get("question", "")
            return self._fetch_with_fallback(kind, symbol, question)
        return tool

    def _fetch_with_fallback(
        self,
        kind: str,
        symbol: str,
        question: str,
    ) -> list[dict]:
        """Fetch from preferred providers, falling back if real fails."""
        preferences = PROVIDER_PREFERENCE.get(kind, [])
        results: list[dict] = []
        errors: list[str] = []

        for source_id in preferences:
            try:
                config = ConnectorConfig()
                if not self._use_real:
                    # In mock mode, still use real connectors only if explicitly enabled
                    if "yfinance" in source_id or source_id == "fred":
                        config.enabled = False
                connector = get_connector(source_id, config=config)
                if not connector.health_check():
                    continue

                if kind == "market_data":
                    records = connector.fetch(symbol=symbol, period="1y", interval="1d")
                elif kind in ("earnings_data", "fundamentals"):
                    records = connector.fetch(symbol=symbol)
                elif kind == "macro_data":
                    records = connector.fetch(indicator_name=question)
                else:
                    records = connector.fetch(symbol=symbol)

                for record in records:
                    if isinstance(record, DataRecord):
                        item = record.data
                        item["_provenance"] = record.provenance.to_dict()
                        item["_quality"] = record.provenance.quality.value
                        results.append(item)
                    else:
                        results.append(record)
                if results:
                    logger.info("e2e_fetch_success", kind=kind, source=source_id, records=len(results))
                    return results
            except Exception as e:
                errors.append(f"{source_id}: {e}")
                logger.warning("e2e_fetch_failed", kind=kind, source=source_id, error=str(e))

        logger.warning("e2e_fetch_all_failed", kind=kind, errors=errors)
        return [{"error": "; ".join(errors), "_quality": "error"}]

    def run(self, question: str, symbol: str | None = None) -> PipelineResult:
        """Execute end-to-end research."""
        logger.info(
            "e2e_research_start",
            question=question,
            symbol=symbol,
            mode="real" if self._use_real else "dev",
        )
        return self._pipeline.execute(question, symbol=symbol)


def build_e2e_orchestrator() -> E2EResearchOrchestrator:
    """Build the standard E2E orchestrator."""
    return E2EResearchOrchestrator()