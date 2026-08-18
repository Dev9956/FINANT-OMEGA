"""FININT OMEGA — Market Regime Detector."""

from __future__ import annotations

from core.intelligence.regime.models import (
    MarketRegime,
    RegimeConfidence,
    RegimeResult,
    RegimeSignal,
)


class RegimeDetector:
    """Detect current market regime from multi-dimensional signals."""

    def __init__(self) -> None:
        self._regime_signals: dict[MarketRegime, list[str]] = {
            MarketRegime.RISK_ON: ["rising_equity", "low_vix", "tight_credit", "strong_momentum"],
            MarketRegime.RISK_OFF: ["falling_equity", "high_vix", "wide_credit", "flight_to_quality"],
            MarketRegime.INFLATIONARY: ["rising_inflation", "rising_commodities", "rising_yields", "weak_currency"],
            MarketRegime.DEFLATIONARY: ["falling_inflation", "falling_commodities", "falling_yields", "strong_currency"],
            MarketRegime.STAGFLATION: ["rising_inflation", "falling_growth", "rising_unemployment", "weak_equity"],
            MarketRegime.HIGH_GROWTH: ["rising_gdp", "rising_earnings", "rising_sentiment", "low_unemployment"],
            MarketRegime.RECESSION: ["falling_gdp", "rising_unemployment", "falling_earnings", "yield_curve_inversion"],
            MarketRegime.LIQUIDITY_STRESS: ["spreading_credit", "rising_libor", "falling_liquidity", "bond_market_stress"],
            MarketRegime.RECOVERY: ["rising_gdp_from_low", "falling_unemployment", "rising_sentiment", "early_cycle_sectors"],
        }

    def detect(
        self,
        market_data: dict[str, float] | None = None,
        indicators: dict[str, float] | None = None,
    ) -> RegimeResult:
        data = market_data or {}
        ind = indicators or {}
        all_data = {**data, **ind}

        signals = self._extract_signals(all_data)
        regime_scores = self._score_regimes(signals)

        if not regime_scores:
            return RegimeResult(
                regime=MarketRegime.UNKNOWN,
                confidence=RegimeConfidence.LOW,
                confidence_score=0.0,
                signals=signals,
                summary="Insufficient data for regime classification",
            )

        best_regime = max(regime_scores, key=regime_scores.get)
        best_score = regime_scores[best_regime]
        total_score = sum(regime_scores.values())
        confidence_score = best_score / total_score if total_score > 0 else 0.0

        if confidence_score >= 0.6:
            confidence = RegimeConfidence.HIGH
        elif confidence_score >= 0.4:
            confidence = RegimeConfidence.MODERATE
        else:
            confidence = RegimeConfidence.LOW

        regime_indicators = self._regime_signals.get(best_regime, [])
        supporting = [s.description for s in signals if s.direction in ("bullish", "bearish") and any(ind in s.description.lower() for ind in regime_indicators)]
        conflicting = [s.description for s in signals if s.description not in supporting]

        historical = self._get_historical_similar(best_regime)

        summary = self._generate_summary(best_regime, confidence, confidence_score, len(supporting), len(conflicting))

        return RegimeResult(
            regime=best_regime,
            confidence=confidence,
            confidence_score=confidence_score,
            signals=signals,
            supporting_signals=supporting[:5],
            conflicting_signals=conflicting[:5],
            historical_similar=historical,
            summary=summary,
        )

    def _extract_signals(self, data: dict[str, float]) -> list[RegimeSignal]:
        signals = []

        signal_defs = [
            ("vix", 20, "high", "VIX level"),
            ("sp500_return", 0, "positive", "S&P 500 return"),
            ("yield_spread", 0, "positive", "Yield curve spread"),
            ("inflation_rate", 3, "high", "Inflation rate"),
            ("unemployment_rate", 5, "high", "Unemployment rate"),
            ("gdp_growth", 2, "positive", "GDP growth rate"),
            ("credit_spread", 2, "wide", "Credit spread"),
            ("momentum", 0, "positive", "Market momentum"),
        ]

        for indicator, threshold, direction_type, description in signal_defs:
            if indicator in data:
                value = data[indicator]
                if direction_type == "high":
                    direction = "bearish" if value > threshold else "bullish"
                elif direction_type == "positive":
                    direction = "bullish" if value > threshold else "bearish"
                elif direction_type == "wide":
                    direction = "bearish" if value > threshold else "bullish"
                else:
                    direction = "neutral"

                signals.append(RegimeSignal(
                    indicator=indicator,
                    value=value,
                    threshold=threshold,
                    direction=direction,
                    weight=1.0,
                    description=description,
                ))

        return signals

    def _score_regimes(self, signals: list[RegimeSignal]) -> dict[MarketRegime, float]:
        scores: dict[MarketRegime, float] = {r: 0.0 for r in MarketRegime if r != MarketRegime.UNKNOWN}

        for signal in signals:
            if signal.direction == "bullish":
                scores[MarketRegime.RISK_ON] += signal.weight
                scores[MarketRegime.HIGH_GROWTH] += signal.weight * 0.5
                scores[MarketRegime.RECOVERY] += signal.weight * 0.3
            elif signal.direction == "bearish":
                if signal.indicator not in ("inflation_rate",):
                    scores[MarketRegime.RISK_OFF] += signal.weight
                scores[MarketRegime.RECESSION] += signal.weight * 0.5
                scores[MarketRegime.LIQUIDITY_STRESS] += signal.weight * 0.3

            if signal.indicator == "inflation_rate" and signal.value > 5:
                scores[MarketRegime.INFLATIONARY] += 3.0
            elif signal.indicator == "inflation_rate" and signal.value > 3:
                scores[MarketRegime.INFLATIONARY] += 1.5
            elif signal.indicator == "inflation_rate" and signal.value < 1:
                scores[MarketRegime.DEFLATIONARY] += 3.0

            if signal.indicator == "gdp_growth" and signal.value < 0:
                scores[MarketRegime.RECESSION] += 1.5
                scores[MarketRegime.STAGFLATION] += 0.5
            elif signal.indicator == "gdp_growth" and signal.value < 2:
                scores[MarketRegime.STAGFLATION] += 1.0

            if signal.indicator == "vix" and signal.value > 30:
                scores[MarketRegime.RISK_OFF] += 2.0
                scores[MarketRegime.LIQUIDITY_STRESS] += 1.0

        return {k: v for k, v in scores.items() if v > 0}

    def _get_historical_similar(self, regime: MarketRegime) -> list[str]:
        historical = {
            MarketRegime.RISK_ON: ["Q4 2023", "Q1 2021", "H2 2017"],
            MarketRegime.RISK_OFF: ["March 2020", "Q4 2018", "Q3 2011"],
            MarketRegime.INFLATIONARY: ["1970s", "2022", "H1 2008"],
            MarketRegime.RECESSION: ["2008-2009", "2020", "2001"],
            MarketRegime.STAGFLATION: ["1974-1975", "1980"],
            MarketRegime.LIQUIDITY_STRESS: ["Sept 2008", "March 2020"],
            MarketRegime.RECOVERY: ["2009-2010", "2020-2021"],
        }
        return historical.get(regime, [])

    def _generate_summary(
        self,
        regime: MarketRegime,
        confidence: RegimeConfidence,
        confidence_score: float,
        supporting: int,
        conflicting: int,
    ) -> str:
        return (
            f"Current regime: {regime.value.replace('_', ' ').title()}. "
            f"Confidence: {confidence.value} ({confidence_score:.2f}). "
            f"Supporting signals: {supporting}. Conflicting signals: {conflicting}."
        )
