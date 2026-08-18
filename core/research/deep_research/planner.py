"""FININT OMEGA — Deep Research Engine: question planner and task generator."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from core.research.deep_research.models import (
    ResearchConfig,
    ResearchDepth,
    ResearchTask,
    TaskStatus,
)

# Domain keywords for financial topic detection
_FINANCIAL_KEYWORDS = {
    "company": ["company", "firm", "corporation", "business", "enterprise"],
    "earnings": ["earnings", "eps", "revenue", "profit", "quarterly", "annual report"],
    "valuation": ["valuation", "pe ratio", "pb ratio", "ev/ebitda", "fair value", "dcf"],
    "sector": ["sector", "industry", "segment", "market"],
    "macro": ["macro", "economy", "gdp", "inflation", "interest rate", "fed", "central bank"],
    "risk": ["risk", "volatility", "drawdown", "var", "beta", "sharpe"],
    "technical": ["technical", "chart", "indicator", "rsi", "macd", "moving average"],
    "portfolio": ["portfolio", "allocation", "diversification", "rebalance"],
}

_DOMAIN_SUBTEMPLATES: dict[str, list[str]] = {
    "company": [
        "What is the financial health of {entity}?",
        "How has {entity} performed over the last 4 quarters?",
        "What are the key growth drivers for {entity}?",
        "What risks does {entity} face?",
        "How does {entity} compare to peers?",
    ],
    "earnings": [
        "What were the latest earnings results for {entity}?",
        "How did {entity} compare to analyst estimates?",
        "What is the earnings trend for {entity}?",
        "What guidance did {entity} provide?",
        "How has {entity}'s revenue grown over time?",
    ],
    "valuation": [
        "What is the current valuation of {entity}?",
        "How does {entity}'s valuation compare to peers?",
        "What is the fair value estimate for {entity}?",
        "Is {entity} overvalued or undervalued?",
    ],
    "sector": [
        "What are the key trends in the {entity} sector?",
        "Which companies lead the {entity} industry?",
        "What is the growth outlook for {entity}?",
        "How competitive is the {entity} market?",
    ],
    "macro": [
        "What is the current macroeconomic outlook?",
        "How do current interest rates affect markets?",
        "What are the key macro risks right now?",
        "How does the {entity} economy look?",
    ],
    "risk": [
        "What are the main risk factors for {entity}?",
        "How volatile has {entity} been historically?",
        "What is the correlation of {entity} with the market?",
    ],
    "technical": [
        "What do technical indicators say about {entity}?",
        "Is {entity} in an uptrend or downtrend?",
        "What are the key support/resistance levels for {entity}?",
    ],
    "portfolio": [
        "How should {entity} be allocated in a portfolio?",
        "What is the risk-return profile of {entity}?",
        "How diversified is a portfolio containing {entity}?",
    ],
}


def _detect_domains(question: str) -> list[str]:
    """Detect financial domains from the question text."""
    q_lower = question.lower()
    detected: list[str] = []
    for domain, keywords in _FINANCIAL_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            detected.append(domain)
    if not detected:
        detected.append("company")
    return detected


def _extract_entities(question: str) -> list[str]:
    """Extract likely entity names (uppercase tokens) from the question."""
    symbols = re.findall(r"\b([A-Z]{2,6})\b", question)
    return list(dict.fromkeys(symbols)) or ["the company"]


class ResearchPlanner:
    """Generate sub-questions and research tasks from a research question."""

    def analyze_question(self, question: str) -> list[str]:
        """Break a research question into sub-questions."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        domains = _detect_domains(question)
        entities = _extract_entities(question)
        entity = entities[0] if entities else "the entity"

        sub_questions: list[str] = []
        for domain in domains:
            templates = _DOMAIN_SUBTEMPLATES.get(domain, [])
            for template in templates:
                sq = template.format(entity=entity)
                if sq not in sub_questions:
                    sub_questions.append(sq)

        # Add the original question if not already included
        if question not in sub_questions:
            sub_questions.insert(0, question)

        return sub_questions

    def create_task_graph(
        self,
        sub_questions: list[str],
        config: ResearchConfig | None = None,
    ) -> list[ResearchTask]:
        """Create research tasks from sub-questions, respecting depth limits."""
        if config is None:
            config = ResearchConfig()

        # Limit tasks by config
        limited = sub_questions[: config.max_tasks]

        tasks: list[ResearchTask] = []
        for i, sq in enumerate(limited):
            # Tasks depend on the first task (root question) except root itself
            deps: list[str] = []
            if i > 0 and tasks:
                deps.append(tasks[0].task_id)

            task = ResearchTask(
                question=sq,
                status=TaskStatus.PENDING,
                dependencies=deps,
                metadata={"priority": i},
            )
            tasks.append(task)

        return tasks

    def plan(
        self,
        question: str,
        config: ResearchConfig | None = None,
    ) -> tuple[list[str], list[ResearchTask]]:
        """Full planning pipeline: analyze question and create task graph."""
        if config is None:
            config = ResearchConfig()

        sub_questions = self.analyze_question(question)
        tasks = self.create_task_graph(sub_questions, config)
        return sub_questions, tasks
