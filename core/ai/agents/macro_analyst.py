"""FININT OMEGA — Macro Analyst Agent."""

from __future__ import annotations

from core.ai.agents.base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    AgentRole,
    BaseAgent,
)


class MacroAnalystAgent(BaseAgent):
    """Analyze macroeconomic indicators, rates, and global markets."""

    TOOLS = ["macro_data", "rates", "currency", "commodities"]

    def default_role(self) -> AgentRole:
        return AgentRole.MACRO_ANALYST

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self._validate_input(input_data)

        region = input_data.context.get("region", "global")
        period = input_data.context.get("period", "current")
        tool_calls: list[dict] = []

        for tool in self.TOOLS:
            if tool in self._config.allowed_tools or not self._config.allowed_tools:
                tool_calls.append({"tool": tool, "region": region})

        answer_parts = [
            f"Macro Analysis for {region} ({period}):",
            f"Used {len(tool_calls)} macro data sources.",
        ]

        indicators = input_data.context.get("indicators", {})
        if indicators:
            answer_parts.append(f"Key indicators: {list(indicators.keys())}")

        return self._build_output(
            input_data,
            answer="\n".join(answer_parts),
            confidence=0.6,
            reasoning="Analyzed macroeconomic data, rates, and currencies.",
            tool_calls=tool_calls,
        )
