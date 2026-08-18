"""FININT OMEGA — M2 tests for market and fundamentals analytics."""

import math
import pytest
from datetime import date

from core.analytics.market.prices import MarketPriceAnalyzer
from core.analytics.fundamentals.ratios import FinancialRatioCalculator
from core.analytics.earnings.analyzer import EarningsAnalyzer, EarningsRecord
from core.analytics.screening.engine import StockScreener, ScreeningFilter
from core.data.schemas import FinancialStatement, MarketOHLCV


class TestMarketPriceAnalyzer:
    def setup_method(self):
        self.analyzer = MarketPriceAnalyzer()

    def test_compute_returns(self):
        prices = [100, 110, 105, 120]
        returns = self.analyzer.compute_returns(prices)
        assert len(returns) == 3
        assert returns[0] == pytest.approx(0.10)
        assert returns[1] == pytest.approx(-0.04545, abs=1e-4)

    def test_compute_returns_empty(self):
        assert self.analyzer.compute_returns([]) == []

    def test_compute_log_returns(self):
        prices = [100, 110, 105]
        log_returns = self.analyzer.compute_log_returns(prices)
        assert len(log_returns) == 2
        assert log_returns[0] == pytest.approx(math.log(110 / 100))

    def test_compute_cagr(self):
        # (121/100)^(1/1) - 1 = 0.21
        prices = [100, 121]
        cagr = self.analyzer.compute_cagr(prices)
        assert cagr == pytest.approx(0.21)

    def test_compute_cagr_single(self):
        assert self.analyzer.compute_cagr([100]) is None

    def test_compute_volatility(self):
        returns = [0.01, -0.01, 0.02, -0.02, 0.015]
        vol = self.analyzer.compute_volatility(returns)
        assert vol is not None
        assert vol > 0

    def test_compute_volatility_single(self):
        assert self.analyzer.compute_volatility([0.01]) is None

    def test_compute_max_drawdown(self):
        prices = [100, 110, 90, 95, 100]
        dd = self.analyzer.compute_max_drawdown(prices)
        assert dd == pytest.approx((110 - 90) / 110)

    def test_compute_max_drawdown_empty(self):
        assert self.analyzer.compute_max_drawdown([]) is None

    def test_compute_sharpe_ratio(self):
        returns = [0.01, 0.015, 0.008, 0.012, 0.01]
        sr = self.analyzer.compute_sharpe_ratio(returns)
        assert sr is not None

    def test_compute_sma(self):
        prices = [1, 2, 3, 4, 5]
        sma = self.analyzer.compute_sma(prices, 3)
        assert sma[0] is None
        assert sma[1] is None
        assert sma[2] == pytest.approx(2.0)
        assert sma[3] == pytest.approx(3.0)

    def test_compute_ema(self):
        prices = [1, 2, 3, 4, 5]
        ema = self.analyzer.compute_ema(prices, 3)
        assert ema[0] is None
        assert ema[1] is None
        assert ema[2] == pytest.approx(2.0)
        assert ema[3] is not None

    def test_compute_rsi(self):
        # Create trending prices
        prices = [100 + i for i in range(30)]
        rsi = self.analyzer.compute_rsi(prices)
        assert rsi[-1] is not None
        assert 0 <= rsi[-1] <= 100

    def test_compute_bollinger_bands(self):
        prices = [100 + i * 0.5 for i in range(30)]
        upper, mid, lower = self.analyzer.compute_bollinger_bands(prices, 20)
        assert upper[-1] is not None
        assert lower[-1] is not None
        assert upper[-1] > mid[-1] > lower[-1]

    def test_compute_macd(self):
        prices = [100 + i * 0.5 for i in range(50)]
        macd, signal, hist = self.analyzer.compute_macd(prices)
        assert macd[-1] is not None


class TestFinancialRatioCalculator:
    def test_compute_basic_ratios(self):
        stmt = FinancialStatement(
            symbol="TEST",
            period_end=date(2025, 3, 31),
            statement_type="income_statement",
            revenue=1000000.0,
            net_income=150000.0,
            eps_diluted=15.0,
            total_equity=500000.0,
            total_assets=1000000.0,
            total_debt=300000.0,
        )
        calc = FinancialRatioCalculator()
        ratios = calc.compute_from_statement(stmt, market_price=150.0)
        assert ratios.pe_ratio == pytest.approx(10.0)
        assert ratios.net_margin == pytest.approx(0.15)
        assert ratios.roe == pytest.approx(0.30)
        assert ratios.debt_equity == pytest.approx(0.6)

    def test_compute_growth(self):
        current = FinancialStatement(
            symbol="TEST", period_end=date(2025, 3, 31),
            statement_type="income_statement", revenue=1200, net_income=180, eps_diluted=18,
        )
        previous = FinancialStatement(
            symbol="TEST", period_end=date(2024, 3, 31),
            statement_type="income_statement", revenue=1000, net_income=150, eps_diluted=15,
        )
        calc = FinancialRatioCalculator()
        growth = calc.compute_growth(current, previous)
        assert growth["revenue_growth"] == pytest.approx(0.20)
        assert growth["earnings_growth"] == pytest.approx(0.20)
        assert growth["eps_growth"] == pytest.approx(0.20)


class TestEarningsAnalyzer:
    def test_analyze_surprise_beat(self):
        record = EarningsRecord(
            symbol="TEST", report_date=date(2025, 1, 15),
            period_end=date(2024, 12, 31),
            eps_actual=15.0, eps_estimate=12.0,
        )
        analyzer = EarningsAnalyzer()
        result = analyzer.analyze_surprise(record)
        assert result["rating"] == "strong_beat"
        assert result["eps_surprise_pct"] == pytest.approx(0.25)

    def test_analyze_surprise_miss(self):
        record = EarningsRecord(
            symbol="TEST", report_date=date(2025, 1, 15),
            period_end=date(2024, 12, 31),
            eps_actual=10.0, eps_estimate=12.0,
        )
        analyzer = EarningsAnalyzer()
        result = analyzer.analyze_surprise(record)
        assert result["rating"] == "strong_miss"

    def test_earnings_momentum(self):
        records = [
            EarningsRecord(symbol="T", report_date=date(2025, 1, 15),
                          period_end=date(2024, 12, 31), eps_actual=15, eps_estimate=14),
            EarningsRecord(symbol="T", report_date=date(2024, 10, 15),
                          period_end=date(2024, 9, 30), eps_actual=13, eps_estimate=12),
        ]
        analyzer = EarningsAnalyzer()
        momentum = analyzer.compute_earnings_momentum(records)
        assert momentum["trend"] == "improving"


class TestStockScreener:
    def test_screen_passes(self):
        screener = StockScreener()
        screener.add_filter("pe_ratio", "<", 20)
        candidates = [
            {"symbol": "A", "pe_ratio": 15},
            {"symbol": "B", "pe_ratio": 25},
        ]
        results = screener.screen(candidates)
        assert len(results) == 1
        assert results[0]["symbol"] == "A"

    def test_screen_multiple_filters(self):
        screener = StockScreener()
        screener.add_filter("pe_ratio", "<", 20)
        screener.add_filter("roe", ">", 0.15)
        candidates = [
            {"symbol": "A", "pe_ratio": 15, "roe": 0.20},
            {"symbol": "B", "pe_ratio": 25, "roe": 0.20},
            {"symbol": "C", "pe_ratio": 15, "roe": 0.10},
        ]
        results = screener.screen(candidates)
        assert len(results) == 1
        assert results[0]["symbol"] == "A"

    def test_screen_empty(self):
        screener = StockScreener()
        screener.add_filter("pe_ratio", "<", 20)
        results = screener.screen([])
        assert results == []
