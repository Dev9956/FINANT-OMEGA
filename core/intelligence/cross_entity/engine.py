"""FININT OMEGA — Large-Scale Cross-Entity Intelligence Engine."""

from __future__ import annotations

from core.intelligence.cross_entity.models import (
    CrossEntityRequest,
    CrossEntityResult,
    EntityMetrics,
    RankingCriterion,
    RankingResult,
)


class CrossEntityEngine:
    """Analyze and rank multiple entities across dimensions."""

    def __init__(self) -> None:
        self._entities: dict[str, EntityMetrics] = {}
        self._results: dict[str, CrossEntityResult] = {}

    def register_entity(self, entity: EntityMetrics) -> str:
        self._entities[entity.symbol] = entity
        return entity.entity_id

    def analyze(self, request: CrossEntityRequest) -> CrossEntityResult:
        result = CrossEntityResult(request=request)

        entities = [self._entities[s] for s in request.symbols if s in self._entities]

        for criterion in request.criteria:
            ranking = self._rank_entities(entities, criterion)
            result.rankings.append(ranking)

        result.entities_analyzed = len(entities)
        result.summary = self._generate_summary(result)

        self._results[result.result_id] = result
        return result

    def get_result(self, result_id: str) -> CrossEntityResult | None:
        return self._results.get(result_id)

    def find_weakening_thesis(self) -> list[EntityMetrics]:
        return [e for e in self._entities.values() if e.thesis_health == "weakening"]

    def find_strong_cashflow_low_valuation(self) -> list[EntityMetrics]:
        results = []
        for entity in self._entities.values():
            fcf = entity.metrics.get("fcf_yield", 0)
            pe = entity.metrics.get("pe_ratio", 0)
            if fcf > 5 and 0 < pe < 15:
                results.append(entity)
        return results

    def find_high_anomaly(self, threshold: float = 0.7) -> list[EntityMetrics]:
        return [e for e in self._entities.values() if e.anomaly_score > threshold]

    def _rank_entities(
        self,
        entities: list[EntityMetrics],
        criterion: RankingCriterion,
    ) -> RankingResult:
        scored = []
        for entity in entities:
            score = self._compute_score(entity, criterion)
            entity_copy = entity.model_copy(update={"rank_score": score})
            scored.append(entity_copy)

        scored.sort(key=lambda e: e.rank_score, reverse=True)

        return RankingResult(
            criterion=criterion,
            rankings=scored,
            total_entities=len(scored),
        )

    def _compute_score(self, entity: EntityMetrics, criterion: RankingCriterion) -> float:
        if criterion == RankingCriterion.EARNINGS_MOMENTUM:
            return entity.metrics.get("earnings_growth", 0)
        elif criterion == RankingCriterion.CASHFLOW_QUALITY:
            return entity.metrics.get("fcf_yield", 0)
        elif criterion == RankingCriterion.VALUATION:
            pe = entity.metrics.get("pe_ratio", 100)
            return 100 - pe if pe > 0 else 0
        elif criterion == RankingCriterion.GROWTH:
            return entity.metrics.get("revenue_growth", 0)
        elif criterion == RankingCriterion.RISK:
            return 100 - entity.anomaly_score * 100
        elif criterion == RankingCriterion.THESIS_HEALTH:
            health_map = {"strengthening": 100, "stable": 60, "weakening": 20, "invalidated": 0}
            return health_map.get(entity.thesis_health, 50)
        else:
            earnings = entity.metrics.get("earnings_growth", 0) * 0.3
            fcf = entity.metrics.get("fcf_yield", 0) * 0.3
            val = (100 - entity.metrics.get("pe_ratio", 50)) * 0.2
            risk = (100 - entity.anomaly_score * 100) * 0.2
            return earnings + fcf + val + risk

    def _generate_summary(self, result: CrossEntityResult) -> str:
        if not result.rankings:
            return "No rankings computed"
        top = result.rankings[0].rankings[0] if result.rankings[0].rankings else None
        if top:
            return f"Analyzed {result.entities_analyzed} entities. Top pick: {top.symbol} (score: {top.rank_score:.1f})"
        return f"Analyzed {result.entities_analyzed} entities"
