"""FININT OMEGA — Prediction Tracking and Calibration Engine."""

from __future__ import annotations

from datetime import datetime, timezone

from core.intelligence.predictions.models import (
    CalibrationResult,
    PredictionOutcome,
    PredictionRecord,
    PredictionStatus,
)


class PredictionEngine:
    """Track predictions and measure calibration over time."""

    def __init__(self) -> None:
        self._predictions: dict[str, PredictionRecord] = {}
        self._outcomes: dict[str, PredictionOutcome] = {}

    def register_prediction(
        self,
        entity: str,
        prediction_text: str,
        metric: str = "",
        predicted_value: float | None = None,
        direction: str = "",
        confidence: float = 0.5,
        horizon_days: int = 30,
        assumptions: list[str] | None = None,
        evidence: list[str] | None = None,
    ) -> PredictionRecord:
        pred = PredictionRecord(
            entity=entity,
            prediction_text=prediction_text,
            metric=metric,
            predicted_value=predicted_value,
            direction=direction,
            confidence=confidence,
            horizon_days=horizon_days,
            assumptions=assumptions or [],
            evidence=evidence or [],
        )
        self._predictions[pred.prediction_id] = pred
        return pred

    def get_prediction(self, prediction_id: str) -> PredictionRecord | None:
        return self._predictions.get(prediction_id)

    def resolve_prediction(
        self,
        prediction_id: str,
        actual_value: float,
    ) -> PredictionOutcome | None:
        pred = self._predictions.get(prediction_id)
        if pred is None:
            return None

        error = None
        direction_correct = None

        if pred.predicted_value is not None:
            error = actual_value - pred.predicted_value

        if pred.direction:
            if actual_value > (pred.predicted_value or 0) and pred.direction == "up":
                direction_correct = True
            elif actual_value < (pred.predicted_value or 0) and pred.direction == "down":
                direction_correct = True
            elif pred.direction == "stable" and abs(actual_value - (pred.predicted_value or 0)) / max(abs(pred.predicted_value or 1), 1) < 0.05:
                direction_correct = True
            else:
                direction_correct = False

        outcome = PredictionOutcome(
            prediction_id=prediction_id,
            actual_value=actual_value,
            error=error,
            direction_correct=direction_correct,
        )

        self._outcomes[prediction_id] = outcome
        pred.status = PredictionStatus.RESOLVED
        return outcome

    def get_outcome(self, prediction_id: str) -> PredictionOutcome | None:
        return self._outcomes.get(prediction_id)

    def list_predictions(self, entity: str | None = None, status: PredictionStatus | None = None) -> list[PredictionRecord]:
        preds = list(self._predictions.values())
        if entity:
            preds = [p for p in preds if p.entity == entity]
        if status:
            preds = [p for p in preds if p.status == status]
        return preds

    def compute_calibration(self) -> list[CalibrationResult]:
        resolved = [p for p in self._predictions.values() if p.status == PredictionStatus.RESOLVED]
        if not resolved:
            return []

        buckets = {
            "0-20%": (0, 0.2),
            "20-40%": (0.2, 0.4),
            "40-60%": (0.4, 0.6),
            "60-80%": (0.6, 0.8),
            "80-100%": (0.8, 1.01),
        }

        results = []
        for bucket_name, (low, high) in buckets.items():
            bucket_preds = [p for p in resolved if low <= p.confidence < high]
            if not bucket_preds:
                continue

            correct = sum(
                1 for p in bucket_preds
                if p.prediction_id in self._outcomes
                and self._outcomes[p.prediction_id].direction_correct is True
            )

            total = len(bucket_preds)
            accuracy = correct / total if total > 0 else 0
            avg_conf = sum(p.confidence for p in bucket_preds) / total
            mid_bucket = (low + high) / 2
            cal_error = abs(accuracy - mid_bucket)

            results.append(CalibrationResult(
                confidence_bucket=bucket_name,
                total_predictions=total,
                correct_predictions=correct,
                accuracy=accuracy,
                avg_confidence=avg_conf,
                calibration_error=cal_error,
            ))

        return results

    def compute_brier_score(self) -> float:
        resolved = [p for p in self._predictions.values() if p.status == PredictionStatus.RESOLVED]
        if not resolved:
            return 0.0

        total_score = 0.0
        count = 0
        for pred in resolved:
            outcome = self._outcomes.get(pred.prediction_id)
            if outcome and outcome.direction_correct is not None:
                actual = 1.0 if outcome.direction_correct else 0.0
                total_score += (pred.confidence - actual) ** 2
                count += 1

        return total_score / count if count > 0 else 0.0
