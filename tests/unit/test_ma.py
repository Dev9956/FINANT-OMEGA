"""FININT OMEGA — Unit tests for M&A intelligence module."""

from __future__ import annotations

from datetime import date

import pytest

from core.analytics.ma_intelligence.engine import MAIntelligenceEngine
from core.analytics.ma_intelligence.models import (
    DealStatus,
    Transaction,
    TransactionType,
)


class TestMATransactionModels:
    """Tests for M&A transaction Pydantic models."""

    def test_transaction_type_enum(self) -> None:
        assert TransactionType.acquisition.value == "acquisition"
        assert TransactionType.merger.value == "merger"
        assert len(TransactionType) == 7

    def test_transaction_creation(self) -> None:
        tx = Transaction(
            transaction_type=TransactionType.acquisition,
            acquirer_symbol="MSFT",
            target_symbol="ATVI",
            deal_value=69000000000,
            deal_date=date(2023, 10, 13),
            status=DealStatus.completed,
        )
        assert tx.transaction_id  # auto-generated
        assert tx.currency == "USD"

    def test_deal_status_enum(self) -> None:
        assert DealStatus.announced.value == "announced"
        assert DealStatus.completed.value == "completed"
        assert DealStatus.cancelled.value == "cancelled"


class TestMAIntelligenceEngine:
    """Tests for MAIntelligenceEngine."""

    def test_add_and_get_transaction(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.acquisition,
            acquirer_symbol="MSFT",
            target_symbol="ATVI",
            deal_value=69000000000,
            deal_date=date(2023, 10, 13),
        )
        engine.add_transaction(tx)
        results = engine.get_transactions("ATVI")
        assert len(results) == 1
        assert results[0].acquirer_symbol == "MSFT"

    def test_get_transactions_both_symbols(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.merger,
            acquirer_symbol="A",
            target_symbol="B",
            deal_date=date(2025, 1, 1),
        )
        engine.add_transaction(tx)
        assert len(engine.get_transactions("A")) == 1
        assert len(engine.get_transactions("B")) == 1

    def test_sector_transactions(self) -> None:
        engine = MAIntelligenceEngine()
        engine.add_transaction(
            Transaction(
                transaction_type=TransactionType.acquisition,
                acquirer_symbol="MSFT",
                target_symbol="ATVI",
                deal_date=date(2023, 10, 13),
                metadata={"sector": "technology"},
            )
        )
        engine.add_transaction(
            Transaction(
                transaction_type=TransactionType.acquisition,
                acquirer_symbol="JPM",
                target_symbol="BANK",
                deal_date=date(2023, 11, 1),
                metadata={"sector": "financials"},
            )
        )
        tech_txns = engine.get_sector_transactions("technology")
        assert len(tech_txns) == 1
        assert tech_txns[0].acquirer_symbol == "MSFT"

    def test_sector_transactions_since_date(self) -> None:
        engine = MAIntelligenceEngine()
        engine.add_transaction(
            Transaction(
                transaction_type=TransactionType.acquisition,
                acquirer_symbol="A",
                target_symbol="B",
                deal_date=date(2025, 1, 1),
                metadata={"sector": "tech"},
            )
        )
        engine.add_transaction(
            Transaction(
                transaction_type=TransactionType.acquisition,
                acquirer_symbol="C",
                target_symbol="D",
                deal_date=date(2025, 6, 1),
                metadata={"sector": "tech"},
            )
        )
        txns = engine.get_sector_transactions("tech", since_date=date(2025, 3, 1))
        assert len(txns) == 1

    def test_compute_deal_impact_acquisition(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.acquisition,
            acquirer_symbol="MSFT",
            target_symbol="ATVI",
            deal_value=69000000000,
            deal_date=date(2023, 10, 13),
            status=DealStatus.completed,
        )
        impact = engine.compute_deal_impact(tx)
        assert impact.transaction_id == tx.transaction_id
        assert "MSFT" in impact.impact_on_sector
        assert "ATVI" in impact.impact_on_sector
        assert impact.valuation_change == 69000000000
        assert impact.risk_change == "positive"

    def test_compute_deal_impact_buyback(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.buyback,
            acquirer_symbol="AAPL",
            deal_date=date(2025, 1, 1),
        )
        impact = engine.compute_deal_impact(tx)
        assert "buyback" in impact.impact_on_sector.lower()

    def test_compute_deal_impact_cancelled(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.acquisition,
            acquirer_symbol="A",
            target_symbol="B",
            deal_date=date(2025, 1, 1),
            status=DealStatus.cancelled,
        )
        impact = engine.compute_deal_impact(tx)
        assert impact.risk_change == "negative"

    def test_get_active_deals(self) -> None:
        engine = MAIntelligenceEngine()
        engine.add_transaction(
            Transaction(
                transaction_type=TransactionType.acquisition,
                acquirer_symbol="A",
                target_symbol="B",
                deal_date=date(2025, 1, 1),
                status=DealStatus.announced,
            )
        )
        engine.add_transaction(
            Transaction(
                transaction_type=TransactionType.acquisition,
                acquirer_symbol="C",
                target_symbol="D",
                deal_date=date(2025, 1, 1),
                status=DealStatus.completed,
            )
        )
        active = engine.get_active_deals()
        assert len(active) == 1
        assert active[0].status == DealStatus.announced

    def test_detect_competitive_implications_acquisition(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.acquisition,
            acquirer_symbol="MSFT",
            target_symbol="ATVI",
            deal_date=date(2023, 10, 13),
        )
        implications = engine.detect_competitive_implications(tx)
        assert len(implications) == 1
        assert implications[0]["type"] == "market_consolidation"

    def test_detect_competitive_implications_buyback(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.buyback,
            acquirer_symbol="AAPL",
            deal_date=date(2025, 1, 1),
        )
        implications = engine.detect_competitive_implications(tx)
        assert len(implications) == 1
        assert implications[0]["type"] == "capital_return"

    def test_no_duplicate_transactions(self) -> None:
        engine = MAIntelligenceEngine()
        tx = Transaction(
            transaction_type=TransactionType.acquisition,
            acquirer_symbol="A",
            target_symbol="B",
            deal_date=date(2025, 1, 1),
        )
        engine.add_transaction(tx)
        sector_txns = engine.get_sector_transactions("unknown_sector")
        # No sector match, so empty
        assert len(sector_txns) == 0
