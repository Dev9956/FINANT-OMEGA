"""FININT OMEGA — Information Decay Engine."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from core.intelligence.decay.models import (
    DecayFactor,
    EvidenceItem,
    FreshnessScore,
)


class DecayEngine:
    """Manage dynamic evidence weighting based on information decay."""

    _HALF_LIVES: dict[DecayFactor, int] = {
        DecayFactor.EARNINGS_FILING: 90,
        DecayFactor.NEWS_ARTICLE: 14,
        DecayFactor.ANALYST_REPORT: 60,
        DecayFactor.MACRO_DATA: 30,
        DecayFactor.REGULATORY_FILING: 180,
        DecayFactor.MARKET_DATA: 1,
        DecayFactor.MANAGEMENT_STATEMENT: 30,
        DecayFactor.INDUSTRY_REPORT: 90,
    }

    def __init__(self) -> None:
        self._evidence_store: dict[str, EvidenceItem] = {}

    def add_evidence(self, evidence: EvidenceItem) -> str:
        self._evidence_store[evidence.evidence_id] = evidence
        return evidence.evidence_id

    def score_freshness(
        self,
        evidence_id: str,
        reference_time: datetime | None = None,
    ) -> FreshnessScore:
        evidence = self._evidence_store.get(evidence_id)
        if evidence is None:
            return FreshnessScore(base_freshness=0.0, decay_adjusted=0.0, final_score=0.0)

        ref_time = reference_time or datetime.now(timezone.utc)
        half_life = self._HALF_LIVES.get(evidence.decay_factor, 30)

        published = evidence.published_time
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=timezone.utc)

        days_since = max((ref_time - published).total_seconds() / 86400, 0)
        decay = math.exp(-0.693 * days_since / half_life)

        confirmation_boost = 0.0
        if evidence.confirmed:
            confirmation_boost = 0.2

        final = min(decay * evidence.source_quality + confirmation_boost, 1.0)

        return FreshnessScore(
            base_freshness=1.0,
            decay_adjusted=decay,
            confirmation_boost=confirmation_boost,
            final_score=final,
        )

    def score_all_evidence(
        self,
        reference_time: datetime | None = None,
    ) -> list[dict]:
        results = []
        for evidence_id in self._evidence_store:
            score = self.score_freshness(evidence_id, reference_time)
            evidence = self._evidence_store[evidence_id]
            results.append({
                "evidence_id": evidence_id,
                "content": evidence.content[:100],
                "decay_factor": evidence.decay_factor.value,
                "freshness": score,
            })
        return sorted(results, key=lambda x: x["freshness"].final_score, reverse=True)

    def get_weighted_evidence(
        self,
        evidence_ids: list[str] | None = None,
        reference_time: datetime | None = None,
    ) -> list[dict]:
        ids = evidence_ids or list(self._evidence_store.keys())
        weighted = []
        for eid in ids:
            evidence = self._evidence_store.get(eid)
            if evidence is None:
                continue
            score = self.score_freshness(eid, reference_time)
            weight = score.final_score * evidence.confidence
            weighted.append({
                "evidence_id": eid,
                "content": evidence.content,
                "weight": weight,
                "freshness_score": score.final_score,
                "confidence": evidence.confidence,
            })
        return sorted(weighted, key=lambda x: x["weight"], reverse=True)

    def get_evidence(self, evidence_id: str) -> EvidenceItem | None:
        return self._evidence_store.get(evidence_id)

    def confirm_evidence(self, evidence_id: str) -> bool:
        evidence = self._evidence_store.get(evidence_id)
        if evidence is None:
            return False
        evidence.confirmed = True
        evidence.confirmation_time = datetime.now(timezone.utc)
        return True
