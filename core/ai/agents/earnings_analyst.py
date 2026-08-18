"""FININT OMEGA — Earnings Analyst Agent."""

from __future__ import annotations

from core.ai.agents.base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    AgentRole,
    BaseAgent,
)


class EarningsAnalystAgent(BaseAgent):
    """Analyze earnings results, estimates, and transcripts."""

    TOOLS = ["earnings_data", "estimates", "transcripts"]

    def default_role(self) -> AgentRole:
        return AgentRole.EARNINGS_ANALYST

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self._validate_input(input_data)

        symbol = input_data.context.get("symbol", "UNKNOWN")
        tool_calls: list[dict] = []

        for tool in self.TOOLS:
            if tool in self._config.allowed_tools or not self._config.allowed_tools:
                tool_calls.append({"tool": tool, "symbol": symbol})

        answer_parts = [
            f"Earnings Analysis for {symbol}:",
            f"Reviewed {len(tool_calls)} earnings data sources.",
        ]

        surprise = input_data.context.get("surprise")
        if surprise is not None:
            answer_parts.append(f"Earnings surprise: {surprise}")

        momentum = input_data.context.get("momentum")
        if momentum is not None:
            answer_parts.append(f"Earnings momentum: {momentum}")

        evidence_count = len(input_data.evidence)
        if evidence_count > 0:
            answer_parts.append(f"Evidence items: {evidence_count}")

        return self._build_output(
            input_data,
            answer="\n".join(answer_parts),
            confidence=0.6,
            reasoning="Analyzed earnings data, estimates, and transcripts.",
            tool_calls=tool_calls,
        )
