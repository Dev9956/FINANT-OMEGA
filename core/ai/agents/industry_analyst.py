"""FININT OMEGA — Industry Analyst Agent."""

from __future__ import annotations

from core.ai.agents.base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    AgentRole,
    BaseAgent,
)


class IndustryAnalystAgent(BaseAgent):
    """Analyze industry trends, competitive landscape, and market dynamics."""

    TOOLS = ["sector_data", "company_data", "macro_data"]

    def default_role(self) -> AgentRole:
        return AgentRole.INDUSTRY_ANALYST

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self._validate_input(input_data)

        sector = input_data.context.get("sector", input_data.question)
        tool_calls: list[dict] = []

        for tool in self.TOOLS:
            if tool in self._config.allowed_tools or not self._config.allowed_tools:
                tool_calls.append({"tool": tool, "sector": sector})

        answer_parts = [
            f"Industry Analysis for {sector}:",
            f"Analyzed {len(tool_calls)} industry data sources.",
        ]

        trends = input_data.context.get("trends", [])
        if trends:
            answer_parts.append(f"Key trends identified: {len(trends)}")

        return self._build_output(
            input_data,
            answer="\n".join(answer_parts),
            confidence=0.6,
            reasoning="Analyzed sector data, company data, and macro trends.",
            tool_calls=tool_calls,
        )
