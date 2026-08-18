"""FININT OMEGA — Thesis engine with versioning, evaluation, and evolution tracking."""

from __future__ import annotations

from datetime import datetime, timezone

from core.intelligence.thesis.models import (
    InvalidationCondition,
    ThesisConfidence,
    ThesisEvaluation,
    ThesisEvolution,
    ThesisStatus,
    ThesisUpdate,
    ThesisVersion,
)


class ThesisEngine:
    """Manage investment thesis lifecycle: versioning, evaluation, evolution."""

    def __init__(self) -> None:
        self._theses: dict[str, dict] = {}  # thesis_id -> thesis data
        self._versions: dict[str, list[ThesisVersion]] = {}  # thesis_id -> versions
        self._updates: dict[str, list[ThesisUpdate]] = {}  # thesis_id -> updates
        self._invalidation_conditions: dict[str, list[InvalidationCondition]] = {}
        self._version_counter: dict[str, int] = {}

    def create_thesis(
        self,
        symbol: str,
        title: str,
        bull_case: str = "",
        base_case: str = "",
        bear_case: str = "",
        key_drivers: list[str] | None = None,
        key_risks: list[str] | None = None,
        assumptions: list[str] | None = None,
        confidence: float = 0.7,
        time_horizon: str = "",
    ) -> ThesisVersion:
        thesis_id = str(__import__("uuid").uuid4())
        version_number = 1

        version = ThesisVersion(
            version_number=version_number,
            thesis_id=thesis_id,
            title=title,
            bull_case=bull_case,
            base_case=base_case,
            bear_case=bear_case,
            key_drivers=key_drivers or [],
            key_risks=key_risks or [],
            assumptions=assumptions or [],
            confidence=confidence,
            confidence_level=self._confidence_to_level(confidence),
            status=ThesisStatus.ACTIVE,
            time_horizon=time_horizon,
            change_summary="Initial thesis creation",
        )

        self._theses[thesis_id] = {
            "symbol": symbol,
            "current_version": version_number,
            "status": ThesisStatus.ACTIVE,
            "confidence": confidence,
        }
        self._versions[thesis_id] = [version]
        self._updates[thesis_id] = []
        self._invalidation_conditions[thesis_id] = []
        self._version_counter[thesis_id] = version_number

        return version

    def get_thesis(self, thesis_id: str) -> ThesisVersion | None:
        versions = self._versions.get(thesis_id, [])
        return versions[-1] if versions else None

    def get_thesis_history(self, thesis_id: str) -> ThesisEvolution:
        versions = self._versions.get(thesis_id, [])
        updates = self._updates.get(thesis_id, [])

        return ThesisEvolution(
            thesis_id=thesis_id,
            versions=versions,
            updates=updates,
            total_versions=len(versions),
            confidence_trend=[v.confidence for v in versions],
            status_history=[v.status.value for v in versions],
        )

    def update_thesis(
        self,
        thesis_id: str,
        change_summary: str = "",
        reason: str = "",
        **kwargs,
    ) -> ThesisVersion | None:
        current = self.get_thesis(thesis_id)
        if current is None:
            return None

        new_version_number = self._version_counter[thesis_id] + 1

        update_fields = {}
        for key, value in kwargs.items():
            if hasattr(current, key):
                update_fields[key] = value

        new_version = current.model_copy(update={
            **update_fields,
            "version_number": new_version_number,
            "created_at": datetime.now(timezone.utc),
            "change_summary": change_summary,
            "change_reason": reason,
        })

        changes = []
        confidence_change = 0.0
        for key, value in update_fields.items():
            old_val = getattr(current, key)
            if old_val != value:
                changes.append(f"{key}: {old_val} -> {value}")
                if key == "confidence":
                    confidence_change = value - current.confidence

        update_record = ThesisUpdate(
            thesis_id=thesis_id,
            from_version=current.version_number,
            to_version=new_version_number,
            changes=changes,
            confidence_change=confidence_change,
            reason=reason,
        )

        self._versions[thesis_id].append(new_version)
        self._updates[thesis_id].append(update_record)
        self._version_counter[thesis_id] = new_version_number

        self._theses[thesis_id]["current_version"] = new_version_number
        self._theses[thesis_id]["confidence"] = new_version.confidence
        self._theses[thesis_id]["status"] = new_version.status

        return new_version

    def add_invalidation_condition(self, thesis_id: str, condition: InvalidationCondition) -> None:
        if thesis_id not in self._invalidation_conditions:
            self._invalidation_conditions[thesis_id] = []
        self._invalidation_conditions[thesis_id].append(condition)

    def evaluate_thesis(
        self,
        thesis_id: str,
        supporting_evidence: list[str] | None = None,
        contradicting_evidence: list[str] | None = None,
        metric_values: dict[str, float] | None = None,
    ) -> ThesisEvaluation:
        current = self.get_thesis(thesis_id)
        if current is None:
            return ThesisEvaluation(
                thesis_id=thesis_id,
                health="unknown",
                confidence=0.0,
                confidence_change=0.0,
                status=ThesisStatus.ACTIVE,
            )

        supporting = supporting_evidence or []
        contradicting = contradicting_evidence or []
        metrics = metric_values or {}

        supporting_count = len(supporting)
        contradicting_count = len(contradicting)

        if supporting_count + contradicting_count > 0:
            evidence_ratio = supporting_count / (supporting_count + contradicting_count)
        else:
            evidence_ratio = 0.5

        triggers_fired = []
        invalidation_met = []
        conditions = self._invalidation_conditions.get(thesis_id, [])

        for condition in conditions:
            if condition.metric in metrics:
                value = metrics[condition.metric]
                met = self._check_condition(value, condition)
                if met:
                    condition.periods_met += 1
                    condition.currently_met = True
                    if condition.periods_met >= condition.consecutive_periods:
                        invalidation_met.append(condition.description)
                else:
                    condition.currently_met = False
                    condition.periods_met = 0

        health = "stable"
        confidence_change = 0.0
        new_status = current.status

        if invalidation_met:
            health = "invalidated"
            new_status = ThesisStatus.INVALIDATED
            confidence_change = -0.5
        elif evidence_ratio > 0.7:
            health = "strengthening"
            new_status = ThesisStatus.STRENGTHENED
            confidence_change = 0.1
        elif evidence_ratio < 0.3:
            health = "weakening"
            new_status = ThesisStatus.WEAKENED
            confidence_change = -0.1

        new_confidence = max(0.0, min(1.0, current.confidence + confidence_change))

        recommendations = []
        if contradicting_count > supporting_count:
            recommendations.append("Investigate contradicting evidence")
        if new_confidence < 0.3:
            recommendations.append("Consider thesis invalidation")
        if len(invalidation_met) > 0:
            recommendations.append("Thesis invalidation conditions met - review immediately")

        return ThesisEvaluation(
            thesis_id=thesis_id,
            health=health,
            confidence=new_confidence,
            confidence_change=confidence_change,
            status=new_status,
            supporting_count=supporting_count,
            contradicting_count=contradicting_count,
            triggers_fired=triggers_fired,
            invalidation_met=invalidation_met,
            recommendations=recommendations,
        )

    def list_theses(self, symbol: str | None = None) -> list[ThesisVersion]:
        results = []
        for thesis_id, data in self._theses.items():
            if symbol and data.get("symbol") != symbol:
                continue
            versions = self._versions.get(thesis_id, [])
            if versions:
                results.append(versions[-1])
        return results

    def _check_condition(self, value: float, condition: InvalidationCondition) -> bool:
        if condition.comparator == "lt":
            return value < condition.threshold
        elif condition.comparator == "gt":
            return value > condition.threshold
        elif condition.comparator == "lte":
            return value <= condition.threshold
        elif condition.comparator == "gte":
            return value >= condition.threshold
        elif condition.comparator == "eq":
            return abs(value - condition.threshold) < 1e-9
        return False

    def _confidence_to_level(self, confidence: float) -> ThesisConfidence:
        if confidence >= 0.8:
            return ThesisConfidence.HIGH
        elif confidence >= 0.6:
            return ThesisConfidence.MODERATE
        elif confidence >= 0.4:
            return ThesisConfidence.LOW
        return ThesisConfidence.VERY_LOW
