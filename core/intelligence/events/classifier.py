"""FININT OMEGA — Event classifier for financial events."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field


class EventCategory(str, Enum):
    EARNINGS = "earnings"
    MERGER = "merger"
    DIVIDEND = "dividend"
    GUIDANCE = "guidance"
    INSIDER = "insider"
    MACRO = "macro"
    REGULATORY = "regulatory"
    OTHER = "other"


class ClassifiedEvent(BaseModel):
    """A classified financial event."""

    event_id: str = ""
    title: str
    description: str = ""
    category: EventCategory = EventCategory.OTHER
    symbols: list[str] = Field(default_factory=list)
    sentiment: float = 0.0
    confidence: float = 0.0
    metadata: dict = Field(default_factory=dict)


class EventClassifier:
    """Classify financial events by category, sentiment, and relevance."""

    EARNINGS_PATTERNS = [r"earnings", r"eps", r"revenue beat", r"quarterly results", r"profit"]
    MERGER_PATTERNS = [r"merger", r"acquisition", r"acquire", r"takeover", r"buyout"]
    DIVIDEND_PATTERNS = [r"dividend", r"payout", r"ex-date", r"record date"]
    GUIDANCE_PATTERNS = [r"guidance", r"outlook", r"forecast", r"raised outlook", r"lowered guidance"]
    INSIDER_PATTERNS = [r"insider", r"ceo buy", r"director sell", r"form 4"]
    MACRO_PATTERNS = [r"gdp", r"inflation", r"fed rate", r"unemployment", r"cpi"]
    REGULATORY_PATTERNS = [r"sec filing", r"regulation", r"antitrust", r"lawsuit"]

    def _match_patterns(self, text: str, patterns: list[str]) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def classify(self, title: str, description: str = "", symbols: list[str] | None = None) -> ClassifiedEvent:
        combined = f"{title} {description}"
        if self._match_patterns(combined, self.EARNINGS_PATTERNS):
            category = EventCategory.EARNINGS
        elif self._match_patterns(combined, self.MERGER_PATTERNS):
            category = EventCategory.MERGER
        elif self._match_patterns(combined, self.DIVIDEND_PATTERNS):
            category = EventCategory.DIVIDEND
        elif self._match_patterns(combined, self.GUIDANCE_PATTERNS):
            category = EventCategory.GUIDANCE
        elif self._match_patterns(combined, self.INSIDER_PATTERNS):
            category = EventCategory.INSIDER
        elif self._match_patterns(combined, self.MACRO_PATTERNS):
            category = EventCategory.MACRO
        elif self._match_patterns(combined, self.REGULATORY_PATTERNS):
            category = EventCategory.REGULATORY
        else:
            category = EventCategory.OTHER

        positive_words = {"beat", "upgrade", "buy", "surge", "rally", "profit", "growth", "outperform"}
        negative_words = {"miss", "downgrade", "sell", "drop", "decline", "loss", "cut", "underperform"}
        words = set(combined.lower().split())
        pos = len(words & positive_words)
        neg = len(words & negative_words)
        total = pos + neg
        sentiment = (pos - neg) / total if total > 0 else 0.0

        return ClassifiedEvent(
            title=title,
            description=description,
            category=category,
            symbols=symbols or [],
            sentiment=sentiment,
            confidence=0.8 if category != EventCategory.OTHER else 0.4,
        )
