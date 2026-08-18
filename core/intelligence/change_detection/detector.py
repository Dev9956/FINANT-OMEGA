"""FININT OMEGA — Change detector: detect various types of changes between data."""

from __future__ import annotations

import structlog

from core.intelligence.change_detection.models import (
    ChangeSeverity,
    ChangeType,
    DetectedChange,
)

logger = structlog.get_logger()


class ChangeDetector:
    """Detect numerical, textual, structural, sentiment, guidance, and risk changes."""

    def detect_numerical_changes(
        self,
        data_a: dict[str, float],
        data_b: dict[str, float],
        thresholds: dict[str, float] | None = None,
    ) -> list[DetectedChange]:
        """Detect numerical changes between two data dicts."""
        try:
            thresholds = thresholds or {}
            changes: list[DetectedChange] = []
            all_keys = set(data_a.keys()) | set(data_b.keys())

            for key in all_keys:
                val_a = data_a.get(key)
                val_b = data_b.get(key)

                if val_a is None and val_b is None:
                    continue

                if val_a is None or val_b is None:
                    changes.append(
                        DetectedChange(
                            change_type=ChangeType.NUMERICAL,
                            field=key,
                            old_value=val_a if val_a is not None else "",
                            new_value=val_b if val_b is not None else "",
                            change_pct=100.0 if val_a is None else -100.0,
                            evidence=f"Field {'added' if val_a is None else 'removed'}",
                            confidence=1.0,
                        )
                    )
                    continue

                if not isinstance(val_a, (int, float)) or not isinstance(val_b, (int, float)):
                    if val_a != val_b:
                        changes.append(
                            DetectedChange(
                                change_type=ChangeType.NUMERICAL,
                                field=key,
                                old_value=val_a,
                                new_value=val_b,
                                change_pct=0.0,
                                evidence="Non-numeric value changed",
                                confidence=1.0,
                            )
                        )
                    continue

                if val_a == 0:
                    change_pct = 100.0 if val_b != 0 else 0.0
                else:
                    change_pct = ((val_b - val_a) / abs(val_a)) * 100.0

                threshold = thresholds.get(key, 5.0)
                severity = self._classify_severity(abs(change_pct))
                if abs(change_pct) >= threshold:
                    changes.append(
                        DetectedChange(
                            change_type=ChangeType.NUMERICAL,
                            severity=severity,
                            field=key,
                            old_value=val_a,
                            new_value=val_b,
                            change_pct=change_pct,
                            evidence=f"Changed {change_pct:+.1f}% (threshold: {threshold}%)",
                            confidence=min(abs(change_pct) / 50.0, 1.0),
                        )
                    )
            return changes
        except Exception as e:
            logger.error("detect_numerical_changes_failed", error=str(e))
            return []

    def detect_textual_changes(
        self, text_a: str, text_b: str
    ) -> list[DetectedChange]:
        """Detect changes between two text blocks."""
        try:
            changes: list[DetectedChange] = []
            if text_a == text_b:
                return changes

            words_a = set(text_a.lower().split())
            words_b = set(text_b.lower().split())
            added_words = words_b - words_a
            removed_words = words_a - words_b
            total_words = max(len(words_a | words_b), 1)
            similarity = len(words_a & words_b) / total_words

            if similarity < 0.5:
                severity = ChangeSeverity.MAJOR
            elif similarity < 0.8:
                severity = ChangeSeverity.MODERATE
            elif similarity < 0.95:
                severity = ChangeSeverity.MINOR
            else:
                severity = ChangeSeverity.TRIVIAL

            change_pct = (1.0 - similarity) * 100.0
            evidence_parts: list[str] = []
            if added_words:
                evidence_parts.append(f"Added: {', '.join(list(added_words)[:5])}")
            if removed_words:
                evidence_parts.append(f"Removed: {', '.join(list(removed_words)[:5])}")

            changes.append(
                DetectedChange(
                    change_type=ChangeType.TEXTUAL,
                    severity=severity,
                    field="text",
                    old_value=text_a[:200],
                    new_value=text_b[:200],
                    change_pct=change_pct,
                    evidence="; ".join(evidence_parts),
                    confidence=1.0 - similarity,
                )
            )
            return changes
        except Exception as e:
            logger.error("detect_textual_changes_failed", error=str(e))
            return []

    def detect_structural_changes(
        self, schema_a: dict, schema_b: dict
    ) -> list[DetectedChange]:
        """Detect structural (schema/key) changes between two dicts."""
        try:
            changes: list[DetectedChange] = []
            keys_a = set(schema_a.keys())
            keys_b = set(schema_b.keys())
            added = keys_b - keys_a
            removed = keys_a - keys_b

            for key in added:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.STRUCTURAL,
                        severity=ChangeSeverity.MODERATE,
                        field=key,
                        old_value=None,
                        new_value=schema_b[key],
                        change_pct=100.0,
                        evidence=f"New field added: {key}",
                        confidence=1.0,
                    )
                )
            for key in removed:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.STRUCTURAL,
                        severity=ChangeSeverity.MAJOR,
                        field=key,
                        old_value=schema_a[key],
                        new_value=None,
                        change_pct=-100.0,
                        evidence=f"Field removed: {key}",
                        confidence=1.0,
                    )
                )
            return changes
        except Exception as e:
            logger.error("detect_structural_changes_failed", error=str(e))
            return []

    def detect_sentiment_changes(
        self, sentiment_a: dict[str, float], sentiment_b: dict[str, float]
    ) -> list[DetectedChange]:
        """Detect sentiment shifts between two sentiment snapshots."""
        try:
            changes: list[DetectedChange] = []
            all_keys = set(sentiment_a.keys()) | set(sentiment_b.keys())

            for key in all_keys:
                val_a = sentiment_a.get(key, 0.0)
                val_b = sentiment_b.get(key, 0.0)
                diff = val_b - val_a
                if abs(diff) < 0.05:
                    continue

                severity = ChangeSeverity.TRIVIAL
                if abs(diff) >= 0.5:
                    severity = ChangeSeverity.CRITICAL
                elif abs(diff) >= 0.3:
                    severity = ChangeSeverity.MAJOR
                elif abs(diff) >= 0.2:
                    severity = ChangeSeverity.MODERATE
                elif abs(diff) >= 0.1:
                    severity = ChangeSeverity.MINOR

                changes.append(
                    DetectedChange(
                        change_type=ChangeType.SENTIMENT,
                        severity=severity,
                        field=key,
                        old_value=val_a,
                        new_value=val_b,
                        change_pct=diff * 100.0,
                        evidence=f"Sentiment shifted from {val_a:.2f} to {val_b:.2f}",
                        confidence=min(abs(diff) * 2, 1.0),
                    )
                )
            return changes
        except Exception as e:
            logger.error("detect_sentiment_changes_failed", error=str(e))
            return []

    def detect_guidance_changes(
        self, guidance_a: dict, guidance_b: dict
    ) -> list[DetectedChange]:
        """Detect changes in forward guidance."""
        try:
            changes: list[DetectedChange] = []
            all_keys = set(guidance_a.keys()) | set(guidance_b.keys())

            for key in all_keys:
                val_a = guidance_a.get(key)
                val_b = guidance_b.get(key)
                if val_a == val_b:
                    continue

                if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                    if val_a != 0:
                        change_pct = ((val_b - val_a) / abs(val_a)) * 100.0
                    else:
                        change_pct = 100.0 if val_b != 0 else 0.0
                else:
                    change_pct = 0.0

                severity = ChangeSeverity.MODERATE
                if abs(change_pct) > 20:
                    severity = ChangeSeverity.MAJOR
                elif abs(change_pct) > 10:
                    severity = ChangeSeverity.MODERATE

                changes.append(
                    DetectedChange(
                        change_type=ChangeType.GUIDANCE,
                        severity=severity,
                        field=key,
                        old_value=val_a,
                        new_value=val_b,
                        change_pct=change_pct,
                        evidence=f"Guidance changed for {key}",
                        confidence=0.8,
                    )
                )
            return changes
        except Exception as e:
            logger.error("detect_guidance_changes_failed", error=str(e))
            return []

    def detect_risk_changes(
        self, risks_a: list[str], risks_b: list[str]
    ) -> list[DetectedChange]:
        """Detect changes in risk factors."""
        try:
            changes: list[DetectedChange] = []
            set_a = set(risks_a)
            set_b = set(risks_b)
            added = set_b - set_a
            removed = set_a - set_b

            for risk in added:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.RISK,
                        severity=ChangeSeverity.MODERATE,
                        field="risk_factors",
                        old_value=None,
                        new_value=risk,
                        change_pct=100.0,
                        evidence=f"New risk added: {risk}",
                        confidence=1.0,
                    )
                )
            for risk in removed:
                changes.append(
                    DetectedChange(
                        change_type=ChangeType.RISK,
                        severity=ChangeSeverity.MINOR,
                        field="risk_factors",
                        old_value=risk,
                        new_value=None,
                        change_pct=-100.0,
                        evidence=f"Risk removed: {risk}",
                        confidence=1.0,
                    )
                )
            return changes
        except Exception as e:
            logger.error("detect_risk_changes_failed", error=str(e))
            return []

    @staticmethod
    def _classify_severity(abs_change_pct: float) -> ChangeSeverity:
        """Classify severity based on absolute percentage change."""
        if abs_change_pct >= 20.0:
            return ChangeSeverity.CRITICAL
        if abs_change_pct >= 10.0:
            return ChangeSeverity.MAJOR
        if abs_change_pct >= 5.0:
            return ChangeSeverity.MODERATE
        if abs_change_pct >= 2.0:
            return ChangeSeverity.MINOR
        return ChangeSeverity.TRIVIAL
