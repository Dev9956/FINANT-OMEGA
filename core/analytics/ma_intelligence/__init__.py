"""FININT OMEGA — M&A intelligence module."""

from core.analytics.ma_intelligence.models import (
    DealImpact,
    Transaction,
    TransactionType,
)
from core.analytics.ma_intelligence.engine import MAIntelligenceEngine

__all__ = [
    "TransactionType",
    "Transaction",
    "DealImpact",
    "MAIntelligenceEngine",
]
