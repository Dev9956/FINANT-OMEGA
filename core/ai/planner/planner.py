"""FININT OMEGA — Research planner: intent detection, entity resolution, tool routing."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Intent(str, Enum):
    QUOTE = "quote"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    NEWS = "news"
    EARNINGS = "earnings"
    RISK = "risk"
    SCREEN = "screen"
    UNKNOWN = "unknown"


class PlanStep(BaseModel):
    """A single step in a research plan."""

    step_id: str
    tool_name: str
    description: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    order: int = 0


class ResearchPlan(BaseModel):
    """A complete research plan."""

    query: str
    intent: Intent
    entities: dict[str, Any] = Field(default_factory=dict)
    steps: list[PlanStep] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class ResearchPlanner:
    """Detect user intent, resolve entities, and route to appropriate tools."""

    SYMBOL_PATTERN = re.compile(r"\b([A-Z]{1,5})\b")
    QUOTE_KEYWORDS = {"price", "quote", "current", "trading at", "share price"}
    ANALYSIS_KEYWORDS = {"analyze", "analysis", "fundamentals", "valuation", "ratio"}
    COMPARISON_KEYWORDS = {"compare", "vs", "versus", "better", "difference"}
    NEWS_KEYWORDS = {"news", "headline", "announcement", "update"}
    EARNINGS_KEYWORDS = {"earnings", "eps", "revenue", "quarterly", "results"}
    RISK_KEYWORDS = {"risk", "volatility", "var", "drawdown", "beta"}
    SCREEN_KEYWORDS = {"screen", "filter", "find stocks", "search for"}

    def detect_intent(self, query: str) -> Intent:
        q = query.lower()
        if any(k in q for k in self.QUOTE_KEYWORDS):
            return Intent.QUOTE
        if any(k in q for k in self.ANALYSIS_KEYWORDS):
            return Intent.ANALYSIS
        if any(k in q for k in self.COMPARISON_KEYWORDS):
            return Intent.COMPARISON
        if any(k in q for k in self.NEWS_KEYWORDS):
            return Intent.NEWS
        if any(k in q for k in self.EARNINGS_KEYWORDS):
            return Intent.EARNINGS
        if any(k in q for k in self.RISK_KEYWORDS):
            return Intent.RISK
        if any(k in q for k in self.SCREEN_KEYWORDS):
            return Intent.SCREEN
        return Intent.UNKNOWN

    def resolve_entities(self, query: str) -> dict[str, Any]:
        symbols = list(set(self.SYMBOL_PATTERN.findall(query)))
        return {"symbols": symbols}

    def _route_tool(self, intent: Intent) -> str:
        routing = {
            Intent.QUOTE: "market_data",
            Intent.ANALYSIS: "fundamentals",
            Intent.COMPARISON: "comparator",
            Intent.NEWS: "news_search",
            Intent.EARNINGS: "earnings_data",
            Intent.RISK: "risk_analyzer",
            Intent.SCREEN: "stock_screener",
            Intent.UNKNOWN: "general_search",
        }
        return routing[intent]

    def plan(self, query: str) -> ResearchPlan:
        intent = self.detect_intent(query)
        entities = self.resolve_entities(query)
        tool = self._route_tool(intent)
        steps = [
            PlanStep(
                step_id="step_1",
                tool_name=tool,
                description=f"Execute {intent.value} query",
                parameters={"query": query, **entities},
                order=0,
            )
        ]
        if intent == Intent.ANALYSIS and entities.get("symbols"):
            steps.append(PlanStep(
                step_id="step_2",
                tool_name="risk_analyzer",
                description="Run risk analysis on target",
                parameters={"symbols": entities["symbols"]},
                depends_on=["step_1"],
                order=1,
            ))
        return ResearchPlan(
            query=query,
            intent=intent,
            entities=entities,
            steps=steps,
        )
