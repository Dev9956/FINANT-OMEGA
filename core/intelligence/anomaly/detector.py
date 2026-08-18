"""FININT OMEGA — Financial Anomaly Detector."""

from __future__ import annotations

from core.intelligence.anomaly.models import (
    AnomalyItem,
    AnomalyScore,
    AnomalyType,
)


class AnomalyDetector:
    """Detect unusual financial patterns and anomalies."""

    _MAX_ANOMALIES = 10000

    def __init__(self) -> None:
        self._anomalies: list[AnomalyItem] = []

    def detect(
        self,
        symbol: str,
        metrics: dict[str, float],
        previous_metrics: dict[str, float] | None = None,
        peer_metrics: dict[str, dict[str, float]] | None = None,
    ) -> list[AnomalyItem]:
        anomalies = []
        prev = previous_metrics or {}
        peers = peer_metrics or {}

        cashflow_anomalies = self._detect_cashflow_divergence(symbol, metrics, prev)
        anomalies.extend(cashflow_anomalies)

        margin_anomalies = self._detect_margin_anomaly(symbol, metrics, prev)
        anomalies.extend(margin_anomalies)

        working_capital = self._detect_working_capital(symbol, metrics, prev)
        anomalies.extend(working_capital)

        peer_anomalies = self._detect_peer_relative(symbol, metrics, peers)
        anomalies.extend(peer_anomalies)
        self._anomalies.extend(anomalies)

        # Prune old anomalies to prevent memory leak
        if len(self._anomalies) > self._MAX_ANOMALIES:
            self._anomalies = self._anomalies[-self._MAX_ANOMALIES:]

        return anomalies

    def get_anomalies(self, symbol: str | None = None) -> list[AnomalyItem]:
        if symbol:
            return [a for a in self._anomalies if a.symbol == symbol]
        return list(self._anomalies)

    def _detect_cashflow_divergence(
        self,
        symbol: str,
        metrics: dict[str, float],
        previous: dict[str, float],
    ) -> list[AnomalyItem]:
        anomalies = []
        net_income = metrics.get("net_income", 0)
        operating_cf = metrics.get("operating_cashflow", 0)

        if net_income > 0 and operating_cf < 0:
            anomalies.append(AnomalyItem(
                symbol=symbol,
                anomaly_type=AnomalyType.CASHFLOW_DIVERGENCE,
                score=AnomalyScore(statistical_score=0.9, overall_score=0.9),
                affected_metrics=["net_income", "operating_cashflow"],
                description=f"Positive earnings ({net_income:,.0f}) but negative operating cashflow ({operating_cf:,.0f})",
                investigation_priority="high",
                evidence=["Earnings-cashflow divergence detected"],
            ))

        if net_income > 0 and previous.get("net_income", 0) > 0:
            earnings_growth = ((net_income - previous["net_income"]) / abs(previous["net_income"])) * 100
            if operating_cf < 0 and previous.get("operating_cashflow", 0) > 0:
                anomalies.append(AnomalyItem(
                    symbol=symbol,
                    anomaly_type=AnomalyType.CASHFLOW_DIVERGENCE,
                    score=AnomalyScore(statistical_score=0.85, overall_score=0.85),
                    affected_metrics=["operating_cashflow"],
                    description=f"Earnings grew {earnings_growth:.1f}% but cashflow turned negative",
                    investigation_priority="high",
                ))

        return anomalies

    def _detect_margin_anomaly(
        self,
        symbol: str,
        metrics: dict[str, float],
        previous: dict[str, float],
    ) -> list[AnomalyItem]:
        anomalies = []
        revenue = metrics.get("revenue", 0)
        gross_margin = metrics.get("gross_margin", 0)
        prev_revenue = previous.get("revenue", 0)
        prev_margin = previous.get("gross_margin", 0)

        if revenue > 0 and prev_revenue > 0:
            revenue_growth = ((revenue - prev_revenue) / abs(prev_revenue)) * 100
            if prev_margin > 0:
                margin_change = gross_margin - prev_margin
                if revenue_growth > 10 and margin_change < -3:
                    anomalies.append(AnomalyItem(
                        symbol=symbol,
                        anomaly_type=AnomalyType.MARGIN_ANOMALY,
                        score=AnomalyScore(statistical_score=0.75, overall_score=0.75),
                        affected_metrics=["gross_margin", "revenue"],
                        description=f"Revenue grew {revenue_growth:.1f}% but margin declined {abs(margin_change):.1f}pp",
                        investigation_priority="medium",
                    ))

        return anomalies

    def _detect_working_capital(
        self,
        symbol: str,
        metrics: dict[str, float],
        previous: dict[str, float],
    ) -> list[AnomalyItem]:
        anomalies = []
        receivables = metrics.get("receivables", 0)
        inventory = metrics.get("inventory", 0)
        prev_receivables = previous.get("receivables", 0)
        prev_inventory = previous.get("inventory", 0)

        if prev_receivables > 0:
            recv_growth = ((receivables - prev_receivables) / abs(prev_receivables)) * 100
            if recv_growth > 30:
                anomalies.append(AnomalyItem(
                    symbol=symbol,
                    anomaly_type=AnomalyType.WORKING_CAPITAL,
                    score=AnomalyScore(statistical_score=0.7, overall_score=0.7),
                    affected_metrics=["receivables"],
                    description=f"Receivables grew {recv_growth:.1f}% — potential collection issues",
                    investigation_priority="medium",
                ))

        if prev_inventory > 0:
            inv_growth = ((inventory - prev_inventory) / abs(prev_inventory)) * 100
            if inv_growth > 30:
                anomalies.append(AnomalyItem(
                    symbol=symbol,
                    anomaly_type=AnomalyType.WORKING_CAPITAL,
                    score=AnomalyScore(statistical_score=0.7, overall_score=0.7),
                    affected_metrics=["inventory"],
                    description=f"Inventory grew {inv_growth:.1f}% — potential obsolescence risk",
                    investigation_priority="medium",
                ))

        return anomalies

    def _detect_peer_relative(
        self,
        symbol: str,
        metrics: dict[str, float],
        peer_metrics: dict[str, dict[str, float]],
    ) -> list[AnomalyItem]:
        anomalies = []
        if not peer_metrics:
            return anomalies

        peer_pe_ratios = [p.get("pe_ratio", 0) for p in peer_metrics.values() if p.get("pe_ratio", 0) > 0]
        company_pe = metrics.get("pe_ratio", 0)

        if peer_pe_ratios and company_pe > 0:
            avg_pe = sum(peer_pe_ratios) / len(peer_pe_ratios)
            if company_pe > avg_pe * 2:
                anomalies.append(AnomalyItem(
                    symbol=symbol,
                    anomaly_type=AnomalyType.PEER_RELATIVE,
                    score=AnomalyScore(peer_score=0.8, overall_score=0.8),
                    affected_metrics=["pe_ratio"],
                    description=f"P/E ratio ({company_pe:.1f}x) is {company_pe/avg_pe:.1f}x peer average ({avg_pe:.1f}x)",
                    peer_context=f"Peer average P/E: {avg_pe:.1f}x",
                    investigation_priority="medium",
                ))

        return anomalies
