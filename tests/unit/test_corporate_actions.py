"""FININT OMEGA — Unit tests for corporate actions module."""

from __future__ import annotations

from datetime import date

import pytest

from core.analytics.corporate_actions.engine import CorporateActionsEngine
from core.analytics.corporate_actions.models import (
    ActionType,
    CorporateActionRecord,
)


class TestCorporateActionModels:
    """Tests for corporate action Pydantic models."""

    def test_action_type_enum(self) -> None:
        assert ActionType.split.value == "split"
        assert ActionType.dividend.value == "dividend"
        assert len(ActionType) == 10

    def test_record_creation(self) -> None:
        record = CorporateActionRecord(
            symbol="AAPL",
            action_type=ActionType.split,
            ex_date=date(2025, 6, 1),
            ratio=4.0,
            description="4-for-1 split",
        )
        assert record.symbol == "AAPL"
        assert record.action_id  # auto-generated


class TestCorporateActionsEngine:
    """Tests for CorporateActionsEngine."""

    def test_add_and_get_action(self) -> None:
        engine = CorporateActionsEngine()
        record = CorporateActionRecord(
            symbol="AAPL",
            action_type=ActionType.split,
            ex_date=date(2025, 6, 1),
            ratio=4.0,
        )
        engine.add_action(record)
        actions = engine.get_actions("AAPL")
        assert len(actions) == 1
        assert actions[0].ratio == 4.0

    def test_get_actions_since_date(self) -> None:
        engine = CorporateActionsEngine()
        engine.add_action(
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.dividend,
                ex_date=date(2025, 3, 1),
                dividend_per_share=0.25,
            )
        )
        engine.add_action(
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.dividend,
                ex_date=date(2025, 6, 1),
                dividend_per_share=0.30,
            )
        )
        actions = engine.get_actions("AAPL", since_date=date(2025, 5, 1))
        assert len(actions) == 1
        assert actions[0].dividend_per_share == 0.30

    def test_adjust_prices_split(self) -> None:
        engine = CorporateActionsEngine()
        engine.add_action(
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.split,
                ex_date=date(2025, 6, 1),
                ratio=4.0,
            )
        )
        prices = [
            {"date": date(2025, 5, 30), "close": 200.0, "symbol": "AAPL"},
            {"date": date(2025, 6, 2), "close": 50.0, "symbol": "AAPL"},
        ]
        adjusted = engine.adjust_prices(prices, engine.get_actions("AAPL"))
        assert len(adjusted) == 2
        assert adjusted[1].original_close == 50.0
        assert adjusted[1].adjusted_close == pytest.approx(200.0, rel=1e-3)

    def test_adjust_prices_dividend(self) -> None:
        engine = CorporateActionsEngine()
        engine.add_action(
            CorporateActionRecord(
                symbol="MSFT",
                action_type=ActionType.dividend,
                ex_date=date(2025, 3, 15),
                dividend_per_share=2.0,
            )
        )
        prices = [
            {"date": date(2025, 3, 14), "close": 100.0, "symbol": "MSFT"},
            {"date": date(2025, 3, 17), "close": 98.0, "symbol": "MSFT"},
        ]
        adjusted = engine.adjust_prices(prices, engine.get_actions("MSFT"))
        assert len(adjusted) == 2
        assert adjusted[1].original_close == 98.0
        assert adjusted[1].adjusted_close == pytest.approx(100.0, rel=1e-3)

    def test_adjust_prices_bonus(self) -> None:
        engine = CorporateActionsEngine()
        engine.add_action(
            CorporateActionRecord(
                symbol="TCS",
                action_type=ActionType.bonus,
                ex_date=date(2025, 9, 1),
                ratio=1.0,  # 1:1 bonus (100% bonus)
            )
        )
        prices = [
            {"date": date(2025, 8, 30), "close": 300.0, "symbol": "TCS"},
            {"date": date(2025, 9, 2), "close": 150.0, "symbol": "TCS"},
        ]
        adjusted = engine.adjust_prices(prices, engine.get_actions("TCS"))
        assert adjusted[1].original_close == 150.0
        assert adjusted[1].adjusted_close == pytest.approx(300.0, rel=1e-3)

    def test_is_split(self) -> None:
        engine = CorporateActionsEngine()
        actions = [
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.split,
                ex_date=date(2025, 6, 1),
                ratio=4.0,
            )
        ]
        assert engine.is_split(actions, date(2025, 6, 1)) is True
        assert engine.is_split(actions, date(2025, 6, 2)) is False

    def test_is_dividend(self) -> None:
        engine = CorporateActionsEngine()
        actions = [
            CorporateActionRecord(
                symbol="MSFT",
                action_type=ActionType.dividend,
                ex_date=date(2025, 3, 15),
                dividend_per_share=2.0,
            )
        ]
        assert engine.is_dividend(actions, date(2025, 3, 15)) is True
        assert engine.is_dividend(actions, date(2025, 3, 16)) is False

    def test_total_return_with_dividend(self) -> None:
        engine = CorporateActionsEngine()
        actions = [
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.dividend,
                ex_date=date(2025, 6, 1),
                dividend_per_share=1.0,
            )
        ]
        prices = [
            {"date": date(2025, 1, 1), "close": 100.0},
            {"date": date(2025, 12, 31), "close": 120.0},
        ]
        total_return = engine.compute_total_return(prices, actions)
        assert total_return == pytest.approx(0.21, rel=1e-3)

    def test_total_return_with_split(self) -> None:
        engine = CorporateActionsEngine()
        actions = [
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.split,
                ex_date=date(2025, 6, 1),
                ratio=4.0,
            )
        ]
        prices = [
            {"date": date(2025, 1, 1), "close": 100.0},
            {"date": date(2025, 12, 31), "close": 50.0},
        ]
        total_return = engine.compute_total_return(prices, actions)
        assert total_return == pytest.approx(1.0, rel=1e-3)

    def test_total_return_empty(self) -> None:
        engine = CorporateActionsEngine()
        assert engine.compute_total_return([], []) == 0.0

    def test_total_return_single_price(self) -> None:
        engine = CorporateActionsEngine()
        prices = [{"date": date(2025, 1, 1), "close": 100.0}]
        assert engine.compute_total_return(prices, []) == 0.0

    def test_compute_adjustment_factor(self) -> None:
        engine = CorporateActionsEngine()
        engine.add_action(
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.split,
                ex_date=date(2025, 6, 1),
                ratio=4.0,
            )
        )
        factors = engine.compute_adjustment_factor(
            "AAPL", (date(2025, 1, 1), date(2025, 12, 31))
        )
        assert len(factors) == 1
        assert factors[0].factor == pytest.approx(0.25, rel=1e-6)

    def test_multiple_actions_ordering(self) -> None:
        engine = CorporateActionsEngine()
        engine.add_action(
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.dividend,
                ex_date=date(2025, 6, 1),
                dividend_per_share=1.0,
            )
        )
        engine.add_action(
            CorporateActionRecord(
                symbol="AAPL",
                action_type=ActionType.split,
                ex_date=date(2025, 3, 1),
                ratio=2.0,
            )
        )
        actions = engine.get_actions("AAPL")
        assert actions[0].ex_date == date(2025, 3, 1)
        assert actions[1].ex_date == date(2025, 6, 1)

    def test_adjust_empty_prices(self) -> None:
        engine = CorporateActionsEngine()
        assert engine.adjust_prices([], []) == []
