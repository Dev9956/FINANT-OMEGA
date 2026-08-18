"""Tests for Early Warning System."""

import pytest
from core.intelligence.early_warning.models import WarningCategory, WarningSeverity
from core.intelligence.early_warning.engine import EarlyWarningEngine


class TestEarlyWarningEngine:
    def setup_method(self):
        self.engine = EarlyWarningEngine()

    def test_scan_detects_revenue_decline(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"revenue_growth": 5.0},
            previous_metrics={"revenue_growth": 20.0},
        )
        assert len(warnings) > 0
        assert warnings[0].category == WarningCategory.REVENUE_DETERIORATION

    def test_scan_detects_margin_compression(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"operating_margin": 15.0},
            previous_metrics={"operating_margin": 22.0},
        )
        assert len(warnings) > 0
        assert any(w.category == WarningCategory.MARGIN_COMPRESSION for w in warnings)

    def test_scan_detects_cashflow_decline(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"operating_cashflow": 500},
            previous_metrics={"operating_cashflow": 800},
        )
        assert len(warnings) > 0
        assert any(w.category == WarningCategory.CASHFLOW_DIVERGENCE for w in warnings)

    def test_scan_no_warning_when_stable(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"revenue_growth": 10.0},
            previous_metrics={"revenue_growth": 10.5},
        )
        assert len(warnings) == 0

    def test_scan_no_warning_without_previous(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"revenue_growth": 10.0},
        )
        assert len(warnings) == 0

    def test_get_warnings_by_symbol(self):
        self.engine.scan("AAPL", {"revenue_growth": 5.0}, {"revenue_growth": 20.0})
        self.engine.scan("MSFT", {"revenue_growth": 5.0}, {"revenue_growth": 20.0})
        aapl = self.engine.get_warnings(symbol="AAPL")
        assert all(w.symbol == "AAPL" for w in aapl)

    def test_severity_levels(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"operating_cashflow": 500},
            previous_metrics={"operating_cashflow": 800},
        )
        assert any(w.severity == WarningSeverity.CRITICAL for w in warnings)

    def test_warning_has_investigation(self):
        warnings = self.engine.scan(
            symbol="AAPL",
            current_metrics={"revenue_growth": 5.0},
            previous_metrics={"revenue_growth": 20.0},
        )
        assert warnings[0].recommended_investigation != ""
