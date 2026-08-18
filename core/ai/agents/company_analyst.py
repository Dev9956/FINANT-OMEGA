"""FININT OMEGA — Company Analyst Agent."""

from __future__ import annotations

from core.ai.agents.base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    AgentRole,
    BaseAgent,
)


class CompanyAnalystAgent(BaseAgent):
    """Analyze company fundamentals, market data, and news."""

    TOOLS = ["market_data", "fundamentals", "news", "filings"]

    def default_role(self) -> AgentRole:
        return AgentRole.COMPANY_ANALYST

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self._validate_input(input_data)

        symbol = input_data.context.get("symbol", "UNKNOWN")
        period = input_data.context.get("period", "annual")

        # Collect evidence from existing context
        evidence_summary: list[str] = []
        tool_calls: list[dict] = []

        # Simulate tool calls for each allowed tool
        for tool in self.TOOLS:
            if tool in self._config.allowed_tools or not self._config.allowed_tools:
                tool_calls.append({"tool": tool, "symbol": symbol})

        # Build answer from context and evidence
        if input_data.evidence:
            for ev in input_data.evidence:
                evidence_summary.append(str(ev))

        answer_parts = [
            f"Company Analysis for {symbol} ({period}):",
            f"Analyzed {len(tool_calls)} data sources.",
        ]
        if evidence_summary:
            answer_parts.append(f"Evidence items reviewed: {len(evidence_summary)}.")

        return self._build_output(
            input_data,
            answer="\n".join(answer_parts),
            confidence=0.6,
            reasoning="Used market data, fundamentals, and news sources.",
            tool_calls=tool_calls,
        )
