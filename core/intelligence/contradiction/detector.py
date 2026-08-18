"""FININT OMEGA — Contradiction detector for management vs financials analysis."""

from __future__ import annotations

from core.intelligence.contradiction.models import (
    ContradictionCategory,
    ContradictionItem,
    ContradictionResult,
    ContradictionSeverity,
    EvidenceConflict,
)


class ContradictionDetector:
    """Detect contradictions between qualitative statements and quantitative data."""

    def __init__(self) -> None:
        self._divergence_thresholds = {
            "revenue_growth": 5.0,
            "margin_change": 3.0,
            "cashflow_change": 10.0,
            "order_change": 15.0,
            "inventory_change": 20.0,
            "receivables_change": 20.0,
        }

    def detect_management_vs_financials(
        self,
        management_statements: list[str],
        financial_data: dict[str, dict],
    ) -> list[ContradictionItem]:
        contradictions = []

        positive_keywords = {"strong", "growth", "accelerat", "robust", "improv", "increase", "rise", "gain", "optimis"}
        negative_indicators = {"decline", "decrease", "fall", "drop", "deteriorat", "weak", "compress", "shrink"}

        for statement in management_statements:
            statement_lower = statement.lower()
            is_positive = any(kw in statement_lower for kw in positive_keywords)

            if is_positive:
                for metric, values in financial_data.items():
                    current = values.get("current", 0)
                    previous = values.get("previous", 0)
                    if previous != 0:
                        change_pct = ((current - previous) / abs(previous)) * 100
                        threshold = self._divergence_thresholds.get(metric, 10.0)
                        if change_pct < -threshold:
                            contradictions.append(ContradictionItem(
                                category=ContradictionCategory.MANAGEMENT_VS_FINANCIALS,
                                severity=ContradictionSeverity.HIGH,
                                statement=statement,
                                conflicting_evidence=[f"{metric}: {change_pct:+.1f}%"],
                                confidence=0.7,
                                description=f"Management claims strength but {metric} declined {abs(change_pct):.1f}%",
                                requires_investigation=True,
                            ))

        return contradictions

    def detect_guidance_vs_actual(
        self,
        guidance: dict[str, float],
        actuals: dict[str, float],
    ) -> list[ContradictionItem]:
        contradictions = []

        for metric, guided_value in guidance.items():
            if metric in actuals:
                actual_value = actuals[metric]
                if guided_value != 0:
                    deviation_pct = ((actual_value - guided_value) / abs(guided_value)) * 100
                else:
                    deviation_pct = 0.0

                if abs(deviation_pct) > 10:
                    severity = ContradictionSeverity.CRITICAL if abs(deviation_pct) > 20 else ContradictionSeverity.HIGH
                    contradictions.append(ContradictionItem(
                        category=ContradictionCategory.GUIDANCE_VS_ACTUAL,
                        severity=severity,
                        statement=f"Guided {metric} at {guided_value}",
                        conflicting_evidence=[f"Actual {metric}: {actual_value}"],
                        confidence=0.9,
                        description=f"{metric} missed guidance by {abs(deviation_pct):.1f}%",
                        requires_investigation=True,
                    ))

        return contradictions

    def detect_narrative_vs_numbers(
        self,
        narrative: str,
        metrics: dict[str, dict],
    ) -> ContradictionResult:
        narrative_lower = narrative.lower()
        contradictions = []

        bullish_keywords = {"growth", "accelerat", "strong", "robust", "improv", "expansion"}
        bearish_keywords = {"decline", "deteriorat", "weak", "compress", "contraction", "slowdown"}

        is_bullish_narrative = any(kw in narrative_lower for kw in bullish_keywords)
        is_bearish_narrative = any(kw in narrative_lower for kw in bearish_keywords)

        positive_metrics = 0
        negative_metrics = 0

        for metric_name, values in metrics.items():
            current = values.get("current", 0)
            previous = values.get("previous", 0)
            if previous != 0:
                change_pct = ((current - previous) / abs(previous)) * 100
                if change_pct > 5:
                    positive_metrics += 1
                elif change_pct < -5:
                    negative_metrics += 1

        total_metrics = positive_metrics + negative_metrics
        if total_metrics > 0:
            alignment_score = positive_metrics / total_metrics if is_bullish_narrative else negative_metrics / total_metrics
        else:
            alignment_score = 0.5

        if is_bullish_narrative and negative_metrics > positive_metrics:
            contradictions.append(ContradictionItem(
                category=ContradictionCategory.NARRATIVE_VS_MARKET,
                severity=ContradictionSeverity.HIGH,
                statement=narrative,
                conflicting_evidence=[f"{negative_metrics} metrics declining vs bullish narrative"],
                confidence=0.7,
                description="Narrative is bullish but majority of metrics are declining",
            ))
        elif is_bearish_narrative and positive_metrics > negative_metrics:
            contradictions.append(ContradictionItem(
                category=ContradictionCategory.NARRATIVE_VS_MARKET,
                severity=ContradictionSeverity.MODERATE,
                statement=narrative,
                conflicting_evidence=[f"{positive_metrics} metrics improving vs bearish narrative"],
                confidence=0.6,
                description="Narrative is bearish but majority of metrics are improving",
            ))

        overall_severity = ContradictionSeverity.INFO
        if contradictions:
            severities = [c.severity for c in contradictions]
            if ContradictionSeverity.CRITICAL in severities:
                overall_severity = ContradictionSeverity.CRITICAL
            elif ContradictionSeverity.HIGH in severities:
                overall_severity = ContradictionSeverity.HIGH
            elif ContradictionSeverity.MODERATE in severities:
                overall_severity = ContradictionSeverity.MODERATE

        return ContradictionResult(
            entity="",
            contradictions_found=len(contradictions),
            contradictions=contradictions,
            overall_severity=overall_severity,
            summary=f"Alignment score: {alignment_score:.2f}. {len(contradictions)} contradictions detected.",
        )

    def detect_earnings_vs_cashflow(
        self,
        earnings_data: dict[str, float],
        cashflow_data: dict[str, float],
    ) -> list[ContradictionItem]:
        contradictions = []

        net_income = earnings_data.get("net_income", 0)
        operating_cf = cashflow_data.get("operating_cashflow", 0)

        if net_income > 0 and operating_cf < 0:
            contradictions.append(ContradictionItem(
                category=ContradictionCategory.EARNINGS_VS_CASHFLOW,
                severity=ContradictionSeverity.CRITICAL,
                statement=f"Net income: {net_income:,.0f}",
                conflicting_evidence=[f"Operating cashflow: {operating_cf:,.0f}"],
                confidence=0.9,
                description="Positive earnings but negative operating cashflow - potential quality issue",
                requires_investigation=True,
            ))

        earnings_growth = earnings_data.get("growth_rate", 0)
        cashflow_growth = cashflow_data.get("growth_rate", 0)

        if earnings_growth > 10 and cashflow_growth < -10:
            contradictions.append(ContradictionItem(
                category=ContradictionCategory.EARNINGS_VS_CASHFLOW,
                severity=ContradictionSeverity.HIGH,
                statement=f"Earnings growth: {earnings_growth:+.1f}%",
                conflicting_evidence=[f"Cashflow growth: {cashflow_growth:+.1f}%"],
                confidence=0.8,
                description="Earnings growing but cashflow declining",
                requires_investigation=True,
            ))

        return contradictions

    def score_contradictions(self, contradictions: list[ContradictionItem]) -> dict:
        if not contradictions:
            return {"score": 0, "severity": "info", "count": 0}

        severity_weights = {
            ContradictionSeverity.CRITICAL: 4,
            ContradictionSeverity.HIGH: 3,
            ContradictionSeverity.MODERATE: 2,
            ContradictionSeverity.LOW: 1,
            ContradictionSeverity.INFO: 0,
        }

        total_weight = sum(severity_weights.get(c.severity, 0) for c in contradictions)
        max_possible = len(contradictions) * 4
        score = (total_weight / max_possible * 100) if max_possible > 0 else 0

        if score > 75:
            overall = "critical"
        elif score > 50:
            overall = "high"
        elif score > 25:
            overall = "moderate"
        else:
            overall = "low"

        return {
            "score": round(score, 1),
            "severity": overall,
            "count": len(contradictions),
            "critical": sum(1 for c in contradictions if c.severity == ContradictionSeverity.CRITICAL),
            "high": sum(1 for c in contradictions if c.severity == ContradictionSeverity.HIGH),
            "moderate": sum(1 for c in contradictions if c.severity == ContradictionSeverity.MODERATE),
        }
