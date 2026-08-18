"""FININT OMEGA — Corporate actions engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from core.analytics.corporate_actions.models import (
    ActionAdjustedPrice,
    ActionType,
    AdjustmentFactor,
    CorporateActionRecord,
)


class CorporateActionsEngine:
    """Engine for managing corporate actions and price adjustments."""

    def __init__(self) -> None:
        self._actions: dict[str, list[CorporateActionRecord]] = defaultdict(list)

    def add_action(self, record: CorporateActionRecord) -> str:
        """Add a corporate action. Returns the action_id."""
        self._actions[record.symbol].append(record)
        self._actions[record.symbol].sort(key=lambda a: a.ex_date)
        return record.action_id

    def get_actions(
        self, symbol: str, since_date: date | None = None
    ) -> list[CorporateActionRecord]:
        """Get corporate actions for a symbol since a given date."""
        actions = self._actions.get(symbol, [])
        if since_date is not None:
            actions = [a for a in actions if a.ex_date >= since_date]
        return list(actions)

    def compute_adjustment_factor(
        self, symbol: str, date_range: tuple[date, date]
    ) -> list[AdjustmentFactor]:
        """Compute cumulative adjustment factors for a symbol over a date range."""
        start_date, end_date = date_range
        actions = self._actions.get(symbol, [])
        range_actions = [a for a in actions if start_date <= a.ex_date <= end_date]

        factors: list[AdjustmentFactor] = []
        cumulative = 1.0

        for action in range_actions:
            if action.action_type == ActionType.split and action.ratio:
                factor = 1.0 / action.ratio
                cumulative *= factor
                factors.append(
                    AdjustmentFactor(
                        symbol=symbol,
                        date=action.ex_date,
                        factor=cumulative,
                        reason=f"Split {action.ratio}:1",
                    )
                )
            elif action.action_type == ActionType.bonus and action.ratio:
                factor = 1.0 / (1.0 + action.ratio)
                cumulative *= factor
                factors.append(
                    AdjustmentFactor(
                        symbol=symbol,
                        date=action.ex_date,
                        factor=cumulative,
                        reason=f"Bonus issue {action.ratio}:1",
                    )
                )
            elif action.action_type == ActionType.dividend and action.dividend_per_share:
                factors.append(
                    AdjustmentFactor(
                        symbol=symbol,
                        date=action.ex_date,
                        factor=cumulative,
                        reason=f"Dividend {action.dividend_per_share}",
                    )
                )

        return factors

    def adjust_prices(
        self,
        prices: list[dict],
        actions: list[CorporateActionRecord],
    ) -> list[ActionAdjustedPrice]:
        """Adjust historical prices for corporate actions.

        prices: list of dicts with 'date' (date/str), 'close' (float), 'symbol' (str)
        actions: corporate actions to apply

        All prices on or after an ex_date are adjusted by that action's factor
        so that post-action prices are scaled up to pre-action equivalents.
        """
        if not prices:
            return []

        def _to_date(d: date | str) -> date:
            if isinstance(d, str):
                return date.fromisoformat(d)
            return d

        symbol = prices[0].get("symbol", "")
        sorted_prices = sorted(prices, key=lambda p: _to_date(p["date"]))
        sorted_actions = sorted(actions, key=lambda a: a.ex_date)

        cumulative_factor = 1.0
        action_idx = 0
        adjusted: list[ActionAdjustedPrice] = []
        prev_close: float | None = None

        for price_entry in sorted_prices:
            price_date = _to_date(price_entry["date"])
            original_close = price_entry["close"]

            while action_idx < len(sorted_actions) and sorted_actions[action_idx].ex_date <= price_date:
                action = sorted_actions[action_idx]
                if action.action_type == ActionType.split and action.ratio:
                    cumulative_factor *= action.ratio
                elif action.action_type == ActionType.bonus and action.ratio:
                    cumulative_factor *= 1.0 + action.ratio
                elif action.action_type == ActionType.dividend and action.dividend_per_share:
                    ref_close = prev_close if prev_close and prev_close > 0 else original_close
                    if ref_close > 0:
                        cumulative_factor *= ref_close / (ref_close - action.dividend_per_share)
                action_idx += 1

            prev_close = original_close
            adjusted_close = original_close * cumulative_factor
            adjusted.append(
                ActionAdjustedPrice(
                    symbol=symbol,
                    date=price_date,
                    adjusted_close=round(adjusted_close, 4),
                    original_close=original_close,
                    adjustment_factor=cumulative_factor,
                )
            )

        return adjusted

    def is_split(self, actions: list[CorporateActionRecord], target_date: date) -> bool:
        """Check if any action on a given date is a stock split."""
        return any(
            a.action_type == ActionType.split and a.ex_date == target_date
            for a in actions
        )

    def is_dividend(
        self, actions: list[CorporateActionRecord], target_date: date
    ) -> bool:
        """Check if any action on a given date is a dividend."""
        return any(
            a.action_type == ActionType.dividend and a.ex_date == target_date
            for a in actions
        )

    def compute_total_return(
        self,
        prices: list[dict],
        actions: list[CorporateActionRecord],
    ) -> float:
        """Compute total return including dividends and splits.

        prices: list of dicts with 'date' (date), 'close' (float)
        """
        if len(prices) < 2:
            return 0.0

        sorted_prices = sorted(prices, key=lambda p: p["date"])
        first_close = sorted_prices[0]["close"]
        last_close = sorted_prices[-1]["close"]

        if first_close == 0:
            return 0.0

        cumulative_factor = 1.0
        dividend_total = 0.0

        for action in actions:
            if action.action_type == ActionType.split and action.ratio:
                cumulative_factor *= action.ratio
            elif action.action_type == ActionType.bonus and action.ratio:
                cumulative_factor *= 1.0 + action.ratio
            elif action.action_type == ActionType.dividend and action.dividend_per_share:
                dividend_total += action.dividend_per_share

        adjusted_final = last_close * cumulative_factor
        price_return = (adjusted_final - first_close) / first_close
        dividend_return = dividend_total / first_close if first_close > 0 else 0.0

        return round(price_return + dividend_return, 6)
