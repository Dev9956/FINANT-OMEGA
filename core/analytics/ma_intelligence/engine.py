"""FININT OMEGA — M&A / transaction intelligence engine."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from core.analytics.ma_intelligence.models import (
    DealImpact,
    DealStatus,
    Transaction,
    TransactionType,
)


class MAIntelligenceEngine:
    """Engine for tracking and analyzing M&A transactions."""

    def __init__(self) -> None:
        self._transactions: dict[str, list[Transaction]] = defaultdict(list)

    def add_transaction(self, transaction: Transaction) -> str:
        """Add a transaction. Returns the transaction_id."""
        self._transactions[transaction.target_symbol or "unknown"].append(transaction)
        if transaction.acquirer_symbol:
            self._transactions[transaction.acquirer_symbol].append(transaction)
        return transaction.transaction_id

    def get_transactions(self, symbol: str) -> list[Transaction]:
        """Get all transactions involving a symbol."""
        return list(self._transactions.get(symbol, []))

    def get_sector_transactions(
        self, sector: str, since_date: date | None = None
    ) -> list[Transaction]:
        """Get transactions for a sector since a given date."""
        results: list[Transaction] = []
        for tx_list in self._transactions.values():
            for tx in tx_list:
                tx_sector = tx.metadata.get("sector", "")
                if tx_sector == sector:
                    if since_date is None or tx.deal_date >= since_date:
                        results.append(tx)

        seen: set[str] = set()
        unique: list[Transaction] = []
        for tx in results:
            if tx.transaction_id not in seen:
                seen.add(tx.transaction_id)
                unique.append(tx)
        return unique

    def compute_deal_impact(self, transaction: Transaction) -> DealImpact:
        """Compute the impact of a transaction on the market."""
        impact_lines: list[str] = []
        competitors: list[str] = []

        if transaction.transaction_type == TransactionType.acquisition:
            impact_lines.append(
                f"{transaction.acquirer_symbol} acquiring {transaction.target_symbol}"
            )
            competitors.append(f"{transaction.target_symbol}")
        elif transaction.transaction_type == TransactionType.merger:
            impact_lines.append(
                f"Merger between {transaction.acquirer_symbol} and {transaction.target_symbol}"
            )
        elif transaction.transaction_type == TransactionType.buyback:
            impact_lines.append(f"{transaction.acquirer_symbol} share buyback announced")
        elif transaction.transaction_type == TransactionType.ipo:
            impact_lines.append(f"{transaction.target_symbol} IPO")
        elif transaction.transaction_type == TransactionType.divestiture:
            impact_lines.append(
                f"{transaction.acquirer_symbol} divesting {transaction.target_symbol}"
            )

        valuation_change: float | None = None
        if transaction.deal_value and transaction.target_symbol:
            valuation_change = transaction.deal_value

        risk_change = "neutral"
        if transaction.status == DealStatus.cancelled:
            risk_change = "negative"
        elif transaction.status == DealStatus.completed:
            risk_change = "positive"

        return DealImpact(
            transaction_id=transaction.transaction_id,
            impact_on_sector="; ".join(impact_lines),
            impact_on_competitors=competitors,
            valuation_change=valuation_change,
            risk_change=risk_change,
        )

    def get_active_deals(self) -> list[Transaction]:
        """Get all transactions with announced status."""
        seen: set[str] = set()
        active: list[Transaction] = []
        for tx_list in self._transactions.values():
            for tx in tx_list:
                if tx.transaction_id not in seen and tx.status == DealStatus.announced:
                    seen.add(tx.transaction_id)
                    active.append(tx)
        return active

    def detect_competitive_implications(
        self, transaction: Transaction
    ) -> list[dict]:
        """Detect competitive implications of a transaction."""
        implications: list[dict] = []

        if transaction.transaction_type == TransactionType.acquisition:
            implications.append(
                {
                    "type": "market_consolidation",
                    "description": (
                        f"Acquisition of {transaction.target_symbol} by "
                        f"{transaction.acquirer_symbol} may reduce competition"
                    ),
                    "affected_symbols": [
                        s
                        for s in [transaction.acquirer_symbol, transaction.target_symbol]
                        if s
                    ],
                }
            )
        elif transaction.transaction_type == TransactionType.merger:
            implications.append(
                {
                    "type": "merger_impact",
                    "description": (
                        f"Merger between {transaction.acquirer_symbol} and "
                        f"{transaction.target_symbol} may reshape market"
                    ),
                    "affected_symbols": [
                        s
                        for s in [transaction.acquirer_symbol, transaction.target_symbol]
                        if s
                    ],
                }
            )
        elif transaction.transaction_type == TransactionType.buyback:
            implications.append(
                {
                    "type": "capital_return",
                    "description": f"{transaction.acquirer_symbol} returning capital to shareholders",
                    "affected_symbols": [transaction.acquirer_symbol] if transaction.acquirer_symbol else [],
                }
            )
        elif transaction.transaction_type == TransactionType.divestiture:
            implications.append(
                {
                    "type": "divestiture_opportunity",
                    "description": (
                        f"Divestiture of {transaction.target_symbol} by "
                        f"{transaction.acquirer_symbol} may create acquisition target"
                    ),
                    "affected_symbols": [
                        s
                        for s in [transaction.acquirer_symbol, transaction.target_symbol]
                        if s
                    ],
                }
            )

        return implications
