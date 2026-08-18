"""FININT OMEGA — Financial ratio calculations."""

from __future__ import annotations

from core.data.schemas import FinancialRatios, FinancialStatement


class FinancialRatioCalculator:
    """Computes financial ratios from statements."""

    def compute_from_statement(self, stmt: FinancialStatement, market_price: float | None = None) -> FinancialRatios:
        """Compute ratios from a single financial statement."""
        ratios = FinancialRatios(
            symbol=stmt.symbol,
            date=stmt.period_end,
        )

        # Profitability
        if stmt.revenue and stmt.revenue > 0:
            if stmt.gross_profit is not None:
                ratios.gross_margin = stmt.gross_profit / stmt.revenue
            if stmt.operating_expenses is not None and stmt.revenue:
                ebit = (stmt.revenue - stmt.cost_of_goods_sold - stmt.operating_expenses) if stmt.cost_of_goods_sold else None
                if ebit is not None:
                    ratios.operating_margin = ebit / stmt.revenue
            if stmt.net_income is not None:
                ratios.net_margin = stmt.net_income / stmt.revenue

        # ROE, ROA, ROCE
        if stmt.net_income and stmt.total_equity and stmt.total_equity > 0:
            ratios.roe = stmt.net_income / stmt.total_equity
        if stmt.net_income and stmt.total_assets and stmt.total_assets > 0:
            ratios.roa = stmt.net_income / stmt.total_assets
        if stmt.ebit and stmt.total_assets and stmt.total_assets > 0:
            ratios.roce = stmt.ebit / stmt.total_assets

        # Leverage
        if stmt.total_debt and stmt.total_equity and stmt.total_equity > 0:
            ratios.debt_equity = stmt.total_debt / stmt.total_equity

        # Valuation (requires market price)
        if market_price and stmt.eps_diluted and stmt.eps_diluted > 0:
            ratios.pe_ratio = market_price / stmt.eps_diluted

        # FCF yield (requires market cap)
        if stmt.free_cash_flow and market_price and stmt.shares_outstanding and stmt.shares_outstanding > 0:
            market_cap = market_price * stmt.shares_outstanding
            if market_cap > 0:
                ratios.fcf_yield = stmt.free_cash_flow / market_cap

        return ratios

    def compute_growth(
        self, current: FinancialStatement, previous: FinancialStatement
    ) -> dict[str, float | None]:
        """Compute year-over-year growth metrics."""
        result: dict[str, float | None] = {}

        if previous.revenue and previous.revenue > 0 and current.revenue:
            result["revenue_growth"] = (current.revenue - previous.revenue) / previous.revenue
        else:
            result["revenue_growth"] = None

        if previous.net_income and previous.net_income > 0 and current.net_income:
            result["earnings_growth"] = (current.net_income - previous.net_income) / previous.net_income
        else:
            result["earnings_growth"] = None

        if previous.eps_diluted and previous.eps_diluted > 0 and current.eps_diluted:
            result["eps_growth"] = (current.eps_diluted - previous.eps_diluted) / previous.eps_diluted
        else:
            result["eps_growth"] = None

        return result
