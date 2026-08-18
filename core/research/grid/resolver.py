"""FININT OMEGA — Metric resolver for the research grid."""

from __future__ import annotations

import uuid
from typing import Any

from core.data.schemas import FinancialRatios, FinancialStatement, MarketOHLCV
from core.research.grid.models import ColumnSpec, MetricType, RowSpec


class MetricResolver:
    """Resolve metric names to column specs and compute values."""

    STANDARD_METRICS: dict[str, dict[str, Any]] = {
        "revenue_growth": {
            "name": "Revenue Growth (YoY)",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "revenue_growth_yoy",
            "description": "Year-over-year revenue growth rate",
            "unit": "%",
        },
        "eps_growth": {
            "name": "EPS Growth (YoY)",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "eps_growth_yoy",
            "description": "Year-over-year EPS growth rate",
            "unit": "%",
        },
        "roe": {
            "name": "Return on Equity",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "roe",
            "description": "Net income divided by shareholders' equity",
            "unit": "%",
        },
        "roce": {
            "name": "Return on Capital Employed",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "roce",
            "description": "EBIT divided by capital employed",
            "unit": "%",
        },
        "debt_equity": {
            "name": "Debt-to-Equity Ratio",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "debt_equity",
            "description": "Total debt divided by total equity",
            "unit": "x",
        },
        "pe_ratio": {
            "name": "P/E Ratio",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "pe_ratio",
            "description": "Price-to-earnings ratio",
            "unit": "x",
        },
        "ev_ebitda": {
            "name": "EV/EBITDA",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "ev_ebitda",
            "description": "Enterprise value to EBITDA",
            "unit": "x",
        },
        "fcf_yield": {
            "name": "FCF Yield",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "fcf_yield",
            "description": "Free cash flow yield",
            "unit": "%",
        },
        "gross_margin": {
            "name": "Gross Margin",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "gross_margin",
            "description": "Gross profit margin",
            "unit": "%",
        },
        "operating_margin": {
            "name": "Operating Margin",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "operating_margin",
            "description": "Operating profit margin",
            "unit": "%",
        },
        "net_margin": {
            "name": "Net Profit Margin",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "net_margin",
            "description": "Net income margin",
            "unit": "%",
        },
        "earnings_surprise": {
            "name": "Earnings Surprise",
            "metric_type": MetricType.NUMERIC,
            "source": "earnings",
            "calculation": "earnings_surprise",
            "description": "Actual EPS minus consensus estimate",
            "unit": "$",
        },
        "market_cap": {
            "name": "Market Capitalization",
            "metric_type": MetricType.NUMERIC,
            "source": "market",
            "calculation": "market_cap",
            "description": "Current market capitalization",
            "unit": "USD",
        },
        "dividend_yield": {
            "name": "Dividend Yield",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "dividend_yield",
            "description": "Annual dividend yield",
            "unit": "%",
        },
        "current_ratio": {
            "name": "Current Ratio",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_ratios",
            "calculation": "current_ratio",
            "description": "Current assets divided by current liabilities",
            "unit": "x",
        },
        "revenue": {
            "name": "Revenue",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "revenue",
            "description": "Total revenue",
            "unit": "USD",
        },
        "ebitda": {
            "name": "EBITDA",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "ebitda",
            "description": "Earnings before interest, taxes, depreciation and amortization",
            "unit": "USD",
        },
        "net_income": {
            "name": "Net Income",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "net_income",
            "description": "Net income",
            "unit": "USD",
        },
        "total_debt": {
            "name": "Total Debt",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "total_debt",
            "description": "Total debt on balance sheet",
            "unit": "USD",
        },
        "free_cash_flow": {
            "name": "Free Cash Flow",
            "metric_type": MetricType.NUMERIC,
            "source": "financial_statements",
            "calculation": "free_cash_flow",
            "description": "Operating cash flow minus capital expenditures",
            "unit": "USD",
        },
    }

    def resolve_metric(self, metric_name: str) -> ColumnSpec:
        """Resolve a metric name to a ColumnSpec."""
        key = metric_name.lower().strip().replace(" ", "_").replace("-", "_")
        if key in self.STANDARD_METRICS:
            m = self.STANDARD_METRICS[key]
            return ColumnSpec(
                column_id=key,
                name=m["name"],
                metric_type=m["metric_type"],
                source=m["source"],
                calculation=m["calculation"],
                evidence_required=True,
                description=m["description"],
            )
        return ColumnSpec(
            column_id=key,
            name=metric_name,
            metric_type=MetricType.NUMERIC,
            source="unknown",
            calculation=key,
            evidence_required=False,
            description=f"Custom metric: {metric_name}",
        )

    def resolve_entity(self, entity_name: str) -> RowSpec:
        """Resolve an entity name to a RowSpec."""
        symbol = entity_name.upper().strip()
        return RowSpec(
            entity_type="company",
            entity_id=symbol,
            entity_name=entity_name,
        )

    def resolve_calculation(self, formula: str, columns: list[str]) -> callable:
        """Resolve a formula string to a callable calculation function."""
        formula_lower = formula.lower().strip()

        if formula_lower == "revenue_growth_yoy":
            return self._calc_revenue_growth
        elif formula_lower == "eps_growth_yoy":
            return self._calc_eps_growth
        elif formula_lower == "debt_equity_ratio":
            return self._calc_debt_equity
        elif formula_lower == "fcf_yield":
            return self._calc_fcf_yield
        elif formula_lower == "ev_ebitda":
            return self._calc_ev_ebitda
        else:
            return lambda data, row_id: data.get(formula_lower)

    def extract_value(self, data: dict, calculation: str, row_id: str) -> Any:
        """Extract a value from data for a given calculation and row."""
        if calculation in self.STANDARD_METRICS:
            source = self.STANDARD_METRICS[calculation]["source"]
            if source == "financial_ratios":
                return data.get(calculation)
            elif source == "financial_statements":
                return data.get(calculation)
            elif source == "market":
                return data.get(calculation)
        return data.get(calculation)

    def _calc_revenue_growth(self, data: dict, row_id: str) -> Any:
        current = data.get("revenue_current")
        prior = data.get("revenue_prior")
        if current is not None and prior and prior != 0:
            return round((current - prior) / abs(prior) * 100, 2)
        return None

    def _calc_eps_growth(self, data: dict, row_id: str) -> Any:
        current = data.get("eps_current")
        prior = data.get("eps_prior")
        if current is not None and prior and prior != 0:
            return round((current - prior) / abs(prior) * 100, 2)
        return None

    def _calc_debt_equity(self, data: dict, row_id: str) -> Any:
        debt = data.get("total_debt")
        equity = data.get("total_equity")
        if debt is not None and equity and equity != 0:
            return round(debt / equity, 2)
        return None

    def _calc_fcf_yield(self, data: dict, row_id: str) -> Any:
        fcf = data.get("free_cash_flow")
        mcap = data.get("market_cap")
        if fcf is not None and mcap and mcap != 0:
            return round(fcf / mcap * 100, 2)
        return None

    def _calc_ev_ebitda(self, data: dict, row_id: str) -> Any:
        ev = data.get("enterprise_value")
        ebitda = data.get("ebitda")
        if ev is not None and ebitda and ebitda != 0:
            return round(ev / ebitda, 2)
        return None
