"""FININT OMEGA — Grid planner for natural language to grid specification."""

from __future__ import annotations

import re

from core.research.grid.models import ColumnSpec, GridSpec, RowSpec
from core.research.grid.resolver import MetricResolver


class GridPlanner:
    """Plan a research grid from a natural language request."""

    SECTOR_ENTITIES: dict[str, list[str]] = {
        "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"],
        "finance": ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK"],
        "healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT"],
        "energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC"],
        "consumer": ["PG", "KO", "PEP", "WMT", "COST", "HD", "MCD"],
    }

    METRIC_KEYWORDS: dict[str, list[str]] = {
        "revenue_growth": ["revenue growth", "sales growth", "revenue increase"],
        "eps_growth": ["eps growth", "earnings per share growth", "eps increase"],
        "roe": ["return on equity", "roe", "roequity"],
        "roce": ["return on capital employed", "roce"],
        "debt_equity": ["debt to equity", "debt-to-equity", "debt-equity", "debt equity ratio", "leverage ratio", "debt/equity"],
        "pe_ratio": ["p/e", "pe ratio", "price to earnings", "price/earnings"],
        "ev_ebitda": ["ev/ebitda", "ev to ebitda", "enterprise value ebitda"],
        "fcf_yield": ["fcf yield", "free cash flow yield"],
        "gross_margin": ["gross margin", "gross profit margin"],
        "operating_margin": ["operating margin", "operating profit margin"],
        "net_margin": ["net margin", "net profit margin", "profit margin"],
        "earnings_surprise": ["earnings surprise", "eps surprise", "beating estimates"],
        "market_cap": ["market cap", "market capitalization"],
        "dividend_yield": ["dividend yield", "div yield"],
        "current_ratio": ["current ratio", "liquidity ratio"],
        "revenue": ["revenue", "total revenue", "sales"],
        "ebitda": ["ebitda"],
        "net_income": ["net income", "net profit", "profit"],
        "total_debt": ["total debt", "debt"],
        "free_cash_flow": ["free cash flow", "fcf"],
    }

    def __init__(self) -> None:
        self.resolver = MetricResolver()

    def plan_grid(self, natural_language_request: str) -> GridSpec:
        """Parse a natural language request into a GridSpec."""
        entities = self._resolve_entities(natural_language_request)
        metrics = self._resolve_metrics(natural_language_request)

        if not metrics:
            metrics = ["revenue_growth", "roe", "pe_ratio"]

        columns = [self.resolver.resolve_metric(m) for m in metrics]
        rows = [self.resolver.resolve_entity(e) for e in entities]

        title = self._generate_title(natural_language_request, entities, metrics)

        return GridSpec(
            title=title,
            rows=rows,
            columns=columns,
            metadata={"source_request": natural_language_request},
        )

    EXCLUDED_WORDS = frozenset({"PE", "ROE", "ROA", "EPS", "FCF", "EV", "P", "E", "GDP", "CEO", "CFO", "COO", "YTD", "QTD", "MTD", "TTM"})

    def _resolve_entities(self, request: str) -> list[str]:
        """Extract entity symbols or sector from the request."""
        request_lower = request.lower()

        for sector, symbols in self.SECTOR_ENTITIES.items():
            if sector in request_lower:
                return symbols

        symbol_pattern = r"\b([A-Z]{1,5})\b"
        found = re.findall(symbol_pattern, request)
        if found:
            filtered = [s for s in found if s not in self.EXCLUDED_WORDS]
            if filtered:
                return list(dict.fromkeys(filtered))
            return list(dict.fromkeys(found))

        if "tech" in request_lower or "technology" in request_lower:
            return self.SECTOR_ENTITIES["tech"]
        elif "bank" in request_lower or "financial" in request_lower:
            return self.SECTOR_ENTITIES["finance"]
        elif "health" in request_lower or "pharma" in request_lower:
            return self.SECTOR_ENTITIES["healthcare"]
        elif "energy" in request_lower or "oil" in request_lower:
            return self.SECTOR_ENTITIES["energy"]
        elif "consumer" in request_lower or "retail" in request_lower:
            return self.SECTOR_ENTITIES["consumer"]

        return ["AAPL", "MSFT", "GOOGL"]

    def _resolve_metrics(self, request: str) -> list[str]:
        """Extract metric names from the request."""
        request_lower = request.lower()
        found_metrics: list[str] = []

        sorted_metrics = sorted(
            self.METRIC_KEYWORDS.items(),
            key=lambda x: max(len(kw) for kw in x[1]),
            reverse=True,
        )

        for metric_key, keywords in sorted_metrics:
            for keyword in keywords:
                if keyword in request_lower:
                    if metric_key not in found_metrics:
                        found_metrics.append(metric_key)
                    break

        return found_metrics

    def _generate_title(self, request: str, entities: list[str], metrics: list[str]) -> str:
        """Generate a title for the grid."""
        if len(entities) <= 3:
            entity_str = ", ".join(entities)
        else:
            entity_str = f"{len(entities)} entities"
        metric_str = ", ".join(metrics[:3])
        if len(metrics) > 3:
            metric_str += f" +{len(metrics) - 3} more"
        return f"Research Grid: {metric_str} for {entity_str}"
