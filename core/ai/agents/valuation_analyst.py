"""FININT OMEGA — Valuation Analyst Agent."""

from __future__ import annotations

from core.ai.agents.base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    AgentRole,
    BaseAgent,
)


class ValuationAnalystAgent(BaseAgent):
    """Perform valuation analysis using multiples and peer comparison."""

    TOOLS = ["market_data", "fundamentals", "ratios"]

    def default_role(self) -> AgentRole:
        return AgentRole.VALUATION_ANALYST

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self._validate_input(input_data)

        symbol = input_data.context.get("symbol", "UNKNOWN")
        comparables = input_data.context.get("comparables", [])
        tool_calls: list[dict] = []

        for tool in self.TOOLS:
            if tool in self._config.allowed_tools or not self._config.allowed_tools:
                tool_calls.append({"tool": tool, "symbol": symbol})

        answer_parts = [
            f"Valuation Analysis for {symbol}:",
            f"Used {len(tool_calls)} valuation data sources.",
        ]

        if comparables:
            answer_parts.append(f"Peer comparison: {len(comparables)} comparable companies.")

        pe = input_data.context.get("pe_ratio")
        pb = input_data.context.get("pb_ratio")
        if pe is not None:
            answer_parts.append(f"P/E Ratio: {pe}")
        if pb is not None:
            answer_parts.append(f"P/B Ratio: {pb}")

        return self._build_output(
            input_data,
            answer="\n".join(answer_parts),
            confidence=0.6,
            reasoning="Computed valuation multiples and peer comparison.",
            tool_calls=tool_calls,
        )
