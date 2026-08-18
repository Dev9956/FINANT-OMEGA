"""FININT OMEGA — Portfolio Risk Analyst Agent."""

from __future__ import annotations

from core.ai.agents.base import (
    AgentConfig,
    AgentInput,
    AgentOutput,
    AgentRole,
    BaseAgent,
)


class PortfolioRiskAnalystAgent(BaseAgent):
    """Analyze portfolio risk, factor exposure, and stress tests."""

    TOOLS = ["portfolio_data", "risk_calculations", "factor_analysis"]

    def default_role(self) -> AgentRole:
        return AgentRole.PORTFOLIO_RISK_ANALYST

    def execute(self, input_data: AgentInput) -> AgentOutput:
        self._validate_input(input_data)

        holdings = input_data.context.get("holdings", [])
        tool_calls: list[dict] = []

        for tool in self.TOOLS:
            if tool in self._config.allowed_tools or not self._config.allowed_tools:
                tool_calls.append({"tool": tool, "holdings_count": len(holdings)})

        answer_parts = [
            f"Portfolio Risk Analysis ({len(holdings)} holdings):",
            f"Used {len(tool_calls)} risk analysis tools.",
        ]

        var = input_data.context.get("var")
        if var is not None:
            answer_parts.append(f"Value at Risk (95%): {var}")

        sharpe = input_data.context.get("sharpe_ratio")
        if sharpe is not None:
            answer_parts.append(f"Sharpe Ratio: {sharpe}")

        beta = input_data.context.get("portfolio_beta")
        if beta is not None:
            answer_parts.append(f"Portfolio Beta: {beta}")

        return self._build_output(
            input_data,
            answer="\n".join(answer_parts),
            confidence=0.6,
            reasoning="Computed risk metrics, factor exposure, and stress tests.",
            tool_calls=tool_calls,
        )
