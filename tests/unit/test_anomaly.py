"""Tests for Financial Anomaly Detection."""

import pytest
from core.intelligence.anomaly.models import AnomalyType
from core.intelligence.anomaly.detector import AnomalyDetector


class TestAnomalyDetector:
    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_detect_cashflow_divergence(self):
        anomalies = self.detector.detect(
            symbol="AAPL",
            metrics={"net_income": 1000000, "operating_cashflow": -500000},
        )
        assert len(anomalies) > 0
        assert anomalies[0].anomaly_type == AnomalyType.CASHFLOW_DIVERGENCE

    def test_detect_margin_anomaly(self):
        anomalies = self.detector.detect(
            symbol="AAPL",
            metrics={"revenue": 115, "gross_margin": 35},
            previous_metrics={"revenue": 100, "gross_margin": 40},
        )
        assert len(anomalies) > 0
        assert anomalies[0].anomaly_type == AnomalyType.MARGIN_ANOMALY

    def test_detect_working_capital(self):
        anomalies = self.detector.detect(
            symbol="AAPL",
            metrics={"receivables": 150},
            previous_metrics={"receivables": 100},
        )
        assert len(anomalies) > 0
        assert anomalies[0].anomaly_type == AnomalyType.WORKING_CAPITAL

    def test_detect_peer_relative(self):
        anomalies = self.detector.detect(
            symbol="AAPL",
            metrics={"pe_ratio": 50},
            peer_metrics={"MSFT": {"pe_ratio": 25}, "GOOG": {"pe_ratio": 22}},
        )
        assert len(anomalies) > 0
        assert anomalies[0].anomaly_type == AnomalyType.PEER_RELATIVE

    def test_no_anomaly_stable(self):
        anomalies = self.detector.detect(
            symbol="AAPL",
            metrics={"net_income": 1000000, "operating_cashflow": 1200000},
        )
        assert len(anomalies) == 0

    def test_get_anomalies_by_symbol(self):
        self.detector.detect("AAPL", {"net_income": 1000000, "operating_cashflow": -500000})
        self.detector.detect("MSFT", {"net_income": 1000000, "operating_cashflow": -500000})
        aapl = self.detector.get_anomalies("AAPL")
        assert all(a.symbol == "AAPL" for a in aapl)

    def test_investigation_priority(self):
        anomalies = self.detector.detect(
            symbol="AAPL",
            metrics={"net_income": 1000000, "operating_cashflow": -500000},
        )
        assert anomalies[0].investigation_priority != ""
