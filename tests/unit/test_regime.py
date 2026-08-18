"""Tests for Market Regime Detection."""

import pytest
from core.intelligence.regime.models import MarketRegime, RegimeConfidence
from core.intelligence.regime.detector import RegimeDetector


class TestRegimeDetector:
    def setup_method(self):
        self.detector = RegimeDetector()

    def test_detect_risk_on(self):
        result = self.detector.detect(market_data={
            "vix": 15,
            "sp500_return": 5.0,
            "momentum": 3.0,
            "credit_spread": 1.0,
        })
        assert result.regime in (MarketRegime.RISK_ON, MarketRegime.HIGH_GROWTH, MarketRegime.RECOVERY)
        assert len(result.signals) > 0

    def test_detect_risk_off(self):
        result = self.detector.detect(market_data={
            "vix": 35,
            "sp500_return": -8.0,
            "credit_spread": 4.0,
            "momentum": -5.0,
        })
        assert result.regime in (MarketRegime.RISK_OFF, MarketRegime.RECESSION, MarketRegime.LIQUIDITY_STRESS)

    def test_detect_inflationary(self):
        result = self.detector.detect(indicators={
            "inflation_rate": 7.0,
            "gdp_growth": 1.0,
        })
        assert result.regime in (MarketRegime.INFLATIONARY, MarketRegime.STAGFLATION)

    def test_detect_recession(self):
        result = self.detector.detect(indicators={
            "gdp_growth": -2.0,
            "unemployment_rate": 8.0,
            "inflation_rate": 1.5,
        })
        assert result.regime in (MarketRegime.RECESSION, MarketRegime.DEFLATIONARY)

    def test_detect_unknown_when_empty(self):
        result = self.detector.detect()
        assert result.regime == MarketRegime.UNKNOWN
        assert result.confidence == RegimeConfidence.LOW

    def test_has_signals(self):
        result = self.detector.detect(market_data={"vix": 25, "sp500_return": 2.0})
        assert len(result.signals) == 2

    def test_has_summary(self):
        result = self.detector.detect(market_data={"vix": 15})
        assert result.summary != ""

    def test_confidence_levels(self):
        result = self.detector.detect(market_data={
            "vix": 15,
            "sp500_return": 5.0,
            "momentum": 3.0,
            "credit_spread": 1.0,
            "gdp_growth": 3.0,
        })
        assert result.confidence in (RegimeConfidence.HIGH, RegimeConfidence.MODERATE, RegimeConfidence.LOW)
        assert result.confidence_score >= 0

    def test_historical_similar(self):
        result = self.detector.detect(market_data={"vix": 15, "sp500_return": 5.0})
        assert isinstance(result.historical_similar, list)
