"""FININT OMEGA — Company monitor: snapshot, diff, materiality scoring."""

from __future__ import annotations

import structlog

from core.intelligence.company_monitoring.models import (
    CompanyState,
    MaterialityLevel,
    MonitoringAlert,
    StateDiff,
)

logger = structlog.get_logger()

MATERIALITY_THRESHOLDS: dict[MaterialityLevel, float] = {
    MaterialityLevel.NORMAL: 0.0,
    MaterialityLevel.NOTABLE: 5.0,
    MaterialityLevel.SIGNIFICANT: 10.0,
    MaterialityLevel.CRITICAL: 20.0,
}


class CompanyMonitor:
    """Monitor a single company's metrics, detect diffs, and score materiality."""

    def snapshot(self, symbol: str, data: dict) -> CompanyState:
        """Create a new state snapshot from incoming data."""
        try:
            return CompanyState(symbol=symbol, metrics=data)
        except Exception as e:
            logger.error("snapshot_failed", symbol=symbol, error=str(e))
            raise

    def diff(self, previous_state: CompanyState, current_state: CompanyState) -> list[StateDiff]:
        """Compare two states and return per-metric diffs."""
        try:
            diffs: list[StateDiff] = []
            all_keys = set(previous_state.metrics.keys()) | set(current_state.metrics.keys())
            for key in all_keys:
                old_val = previous_state.metrics.get(key)
                new_val = current_state.metrics.get(key)
                if old_val is None and new_val is None:
                    continue
                if old_val is None or new_val is None:
                    diffs.append(
                        StateDiff(
                            symbol=current_state.symbol,
                            metric=key,
                            old_value=old_val if old_val is not None else "",
                            new_value=new_val if new_val is not None else "",
                            change_pct=100.0 if old_val is None else -100.0,
                        )
                    )
                    continue
                if not isinstance(old_val, (int, float)) or not isinstance(new_val, (int, float)):
                    if old_val != new_val:
                        diffs.append(
                            StateDiff(
                                symbol=current_state.symbol,
                                metric=key,
                                old_value=old_val,
                                new_value=new_val,
                                change_pct=0.0,
                            )
                        )
                    continue
                if old_val == 0:
                    change_pct = 100.0 if new_val != 0 else 0.0
                else:
                    change_pct = ((new_val - old_val) / abs(old_val)) * 100.0
                if change_pct == 0.0:
                    continue
                diffs.append(
                    StateDiff(
                        symbol=current_state.symbol,
                        metric=key,
                        old_value=old_val,
                        new_value=new_val,
                        change_pct=change_pct,
                    )
                )
            for d in diffs:
                d.materiality_score = self.score_materiality(d)
                d.is_material = d.materiality_score > 0
            return diffs
        except Exception as e:
            logger.error("diff_failed", symbol=current_state.symbol, error=str(e))
            return []

    def score_materiality(self, diff: StateDiff) -> float:
        """Score the materiality of a diff (0.0 = trivial, 1.0 = critical)."""
        try:
            abs_change = abs(diff.change_pct)
            if abs_change >= MATERIALITY_THRESHOLDS[MaterialityLevel.CRITICAL]:
                return 1.0
            if abs_change >= MATERIALITY_THRESHOLDS[MaterialityLevel.SIGNIFICANT]:
                return 0.75
            if abs_change >= MATERIALITY_THRESHOLDS[MaterialityLevel.NOTABLE]:
                return 0.5
            return 0.0
        except Exception as e:
            logger.error("score_materiality_failed", error=str(e))
            return 0.0

    def score_materiality_level(self, diff: StateDiff) -> MaterialityLevel:
        """Classify the materiality level of a diff."""
        abs_change = abs(diff.change_pct)
        if abs_change >= MATERIALITY_THRESHOLDS[MaterialityLevel.CRITICAL]:
            return MaterialityLevel.CRITICAL
        if abs_change >= MATERIALITY_THRESHOLDS[MaterialityLevel.SIGNIFICANT]:
            return MaterialityLevel.SIGNIFICANT
        if abs_change >= MATERIALITY_THRESHOLDS[MaterialityLevel.NOTABLE]:
            return MaterialityLevel.NOTABLE
        return MaterialityLevel.NORMAL

    def evaluate_thesis_impact(self, diffs: list[StateDiff], thesis: str) -> str:
        """Evaluate whether diffs support, weaken, or are neutral to a thesis."""
        try:
            if not diffs:
                return "neutral"
            material_diffs = [d for d in diffs if d.is_material]
            if not material_diffs:
                return "neutral"
            positive_count = sum(1 for d in material_diffs if d.change_pct > 0)
            negative_count = sum(1 for d in material_diffs if d.change_pct < 0)
            if positive_count > negative_count:
                return "supports"
            if negative_count > positive_count:
                return "weakens"
            return "neutral"
        except Exception as e:
            logger.error("evaluate_thesis_impact_failed", error=str(e))
            return "neutral"

    def should_alert(self, diff: StateDiff, materiality: MaterialityLevel) -> bool:
        """Determine if an alert should be generated for a diff."""
        return materiality in (
            MaterialityLevel.NOTABLE,
            MaterialityLevel.SIGNIFICANT,
            MaterialityLevel.CRITICAL,
        )
