"""FININT OMEGA — Confidence scorer for evidence and claims."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ConfidenceBreakdown(BaseModel):
    """Breakdown of confidence scoring components."""

    source_quality: float = 0.0
    recency: float = 0.0
    corroboration: float = 0.0
    consistency: float = 0.0
    overall: float = 0.0


class ConfidenceScorer:
    """Score confidence of claims based on multiple signals."""

    def __init__(self, source_weight: float = 0.3, recency_weight: float = 0.2, corroboration_weight: float = 0.3, consistency_weight: float = 0.2) -> None:
        self._source_weight = source_weight
        self._recency_weight = recency_weight
        self._corroboration_weight = corroboration_weight
        self._consistency_weight = consistency_weight

    def score_source_quality(self, source_reliability: float, citation_count: int) -> float:
        base = min(source_reliability, 1.0)
        citation_bonus = min(citation_count / 10.0, 0.3)
        return min(base + citation_bonus, 1.0)

    def score_recency(self, days_since_source: int, half_life_days: int = 365) -> float:
        import math
        if days_since_source <= 0:
            return 1.0
        return math.exp(-0.693 * days_since_source / half_life_days)

    def score_corroboration(self, supporting_count: int, contradicting_count: int) -> float:
        total = supporting_count + contradicting_count
        if total == 0:
            return 0.5
        return supporting_count / total

    def score_consistency(self, claim_texts: list[str], reference: str) -> float:
        if not claim_texts:
            return 0.5
        ref_words = set(reference.lower().split())
        consistent = 0
        for text in claim_texts:
            text_words = set(text.lower().split())
            overlap = len(ref_words & text_words) / max(len(ref_words | text_words), 1)
            if overlap > 0.3:
                consistent += 1
        return consistent / len(claim_texts)

    def compute(self, source_reliability: float = 0.8, citation_count: int = 0, days_since_source: int = 0, supporting_count: int = 0, contradicting_count: int = 0, claim_texts: list[str] | None = None, reference: str = "") -> ConfidenceBreakdown:
        sq = self.score_source_quality(source_reliability, citation_count)
        rec = self.score_recency(days_since_source)
        cor = self.score_corroboration(supporting_count, contradicting_count)
        con = self.score_consistency(claim_texts or [], reference)
        overall = (
            self._source_weight * sq
            + self._recency_weight * rec
            + self._corroboration_weight * cor
            + self._consistency_weight * con
        )
        return ConfidenceBreakdown(
            source_quality=sq,
            recency=rec,
            corroboration=cor,
            consistency=con,
            overall=overall,
        )
