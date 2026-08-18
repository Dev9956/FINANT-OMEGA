"""FININT OMEGA — Screening engine for natural-language stock screening."""

from __future__ import annotations

from core.data.schemas import FinancialRatios, MarketOHLCV


class ScreeningFilter:
    """A single screening filter condition."""

    def __init__(self, field: str, operator: str, value: float):
        self.field = field
        self.operator = operator
        self.value = value

    def evaluate(self, data: dict) -> bool:
        """Evaluate the filter against a data record."""
        actual = data.get(self.field)
        if actual is None:
            return False
        try:
            actual = float(actual)
        except (ValueError, TypeError):
            return False
        if self.operator == ">":
            return actual > self.value
        elif self.operator == ">=":
            return actual >= self.value
        elif self.operator == "<":
            return actual < self.value
        elif self.operator == "<=":
            return actual <= self.value
        elif self.operator == "==":
            return actual == self.value
        elif self.operator == "!=":
            return actual != self.value
        return False


class StockScreener:
    """Natural-language-like stock screener."""

    def __init__(self) -> None:
        self._filters: list[ScreeningFilter] = []

    def add_filter(self, field: str, operator: str, value: float) -> None:
        """Add a filter condition."""
        self._filters.append(ScreeningFilter(field=field, operator=operator, value=value))

    def clear_filters(self) -> None:
        """Remove all filters."""
        self._filters.clear()

    def screen(self, candidates: list[dict]) -> list[dict]:
        """Screen candidates against all filters."""
        results = []
        for candidate in candidates:
            if all(f.evaluate(candidate) for f in self._filters):
                results.append(candidate)
        return results

    def screen_financials(
        self,
        stocks: list[dict],
        filters: list[dict],
    ) -> list[dict]:
        """Screen stocks with filter specifications."""
        self.clear_filters()
        for f in filters:
            self.add_filter(f["field"], f["operator"], f["value"])
        return self.screen(stocks)
