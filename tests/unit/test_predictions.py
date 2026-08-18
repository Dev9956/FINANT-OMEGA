"""Tests for Prediction Tracking and Calibration."""

import pytest
from core.intelligence.predictions.models import PredictionStatus
from core.intelligence.predictions.engine import PredictionEngine


class TestPredictionEngine:
    def setup_method(self):
        self.engine = PredictionEngine()

    def test_register_prediction(self):
        pred = self.engine.register_prediction(
            entity="AAPL",
            prediction_text="Revenue growth > 10%",
            confidence=0.7,
        )
        assert pred.prediction_id
        assert pred.entity == "AAPL"
        assert pred.status == PredictionStatus.PENDING

    def test_resolve_prediction(self):
        pred = self.engine.register_prediction(
            entity="AAPL",
            prediction_text="Revenue growth > 10%",
            predicted_value=12.0,
            direction="up",
            confidence=0.7,
        )
        outcome = self.engine.resolve_prediction(pred.prediction_id, actual_value=13.0)
        assert outcome is not None
        assert outcome.direction_correct is True
        assert outcome.error == 1.0

    def test_resolve_prediction_wrong_direction(self):
        pred = self.engine.register_prediction(
            entity="AAPL",
            prediction_text="Revenue growth",
            predicted_value=12.0,
            direction="up",
            confidence=0.7,
        )
        outcome = self.engine.resolve_prediction(pred.prediction_id, actual_value=8.0)
        assert outcome.direction_correct is False

    def test_get_prediction(self):
        pred = self.engine.register_prediction(entity="AAPL", prediction_text="Test")
        retrieved = self.engine.get_prediction(pred.prediction_id)
        assert retrieved is not None

    def test_list_predictions(self):
        self.engine.register_prediction(entity="AAPL", prediction_text="P1")
        self.engine.register_prediction(entity="MSFT", prediction_text="P2")
        assert len(self.engine.list_predictions()) == 2
        assert len(self.engine.list_predictions(entity="AAPL")) == 1

    def test_calibration(self):
        for i in range(10):
            pred = self.engine.register_prediction(
                entity="AAPL", prediction_text=f"P{i}", confidence=0.7,
            )
            self.engine.resolve_prediction(pred.prediction_id, actual_value=float(i))
        calibration = self.engine.compute_calibration()
        assert len(calibration) > 0

    def test_brier_score(self):
        pred = self.engine.register_prediction(
            entity="AAPL", prediction_text="Test", confidence=0.8, direction="up",
            predicted_value=10,
        )
        self.engine.resolve_prediction(pred.prediction_id, actual_value=12.0)
        score = self.engine.compute_brier_score()
        assert 0 <= score <= 1

    def test_resolve_nonexistent(self):
        assert self.engine.resolve_prediction("nonexistent", 10.0) is None
