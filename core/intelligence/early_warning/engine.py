"""FININT OMEGA — Early Warning Engine."""

from __future__ import annotations

from core.intelligence.early_warning.models import (
    EarlyWarning,
    WarningCategory,
    WarningSeverity,
)


class EarlyWarningEngine:
    """Detect early warning signals from financial data changes."""

    _MAX_WARNINGS = 10000

    def __init__(self) -> None:
        self._thresholds: dict[str, dict] = {
            "revenue_growth": {"decline_pct": -10, "severity": WarningSeverity.HIGH},
            "operating_margin": {"decline_pct": -5, "severity": WarningSeverity.HIGH},
            "net_margin": {"decline_pct": -5, "severity": WarningSeverity.MEDIUM},
            "operating_cashflow": {"decline_pct": -15, "severity": WarningSeverity.CRITICAL},
            "free_cashflow": {"decline_pct": -20, "severity": WarningSeverity.HIGH},
            "debt_equity": {"increase_pct": 25, "severity": WarningSeverity.MEDIUM},
            "interest_coverage": {"decline_pct": -30, "severity": WarningSeverity.CRITICAL},
            "inventory_turnover": {"decline_pct": -15, "severity": WarningSeverity.MEDIUM},
            "receivables_turnover": {"decline_pct": -15, "severity": WarningSeverity.MEDIUM},
            "pe_ratio": {"increase_pct": 50, "severity": WarningSeverity.LOW},
            "volume": {"increase_pct": 200, "severity": WarningSeverity.LOW},
        }
        self._warnings: list[EarlyWarning] = []

    def scan(
        self,
        symbol: str,
        current_metrics: dict[str, float],
        previous_metrics: dict[str, float] | None = None,
    ) -> list[EarlyWarning]:
        warnings = []
        prev = previous_metrics or {}

        for metric, threshold_config in self._thresholds.items():
            if metric not in current_metrics:
                continue

            current_val = current_metrics[metric]
            previous_val = prev.get(metric)

            if previous_val is None or previous_val == 0:
                continue

            change_pct = ((current_val - previous_val) / abs(previous_val)) * 100

            decline_pct = threshold_config.get("decline_pct", 0)
            increase_pct = threshold_config.get("increase_pct", 0)
            severity = threshold_config.get("severity", WarningSeverity.MEDIUM)

            triggered = False
            if decline_pct < 0 and change_pct <= decline_pct:
                triggered = True
            elif increase_pct > 0 and change_pct >= increase_pct:
                triggered = True

            if triggered:
                category = self._metric_to_category(metric)
                description = self._generate_description(metric, change_pct, decline_pct or increase_pct)
                investigation = self._generate_investigation(metric, category)

                warning = EarlyWarning(
                    symbol=symbol,
                    category=category,
                    severity=severity,
                    indicator=metric,
                    current_value=current_val,
                    threshold=previous_val * (1 + (decline_pct or increase_pct) / 100),
                    deviation_pct=change_pct,
                    description=description,
                    recommended_investigation=investigation,
                    confidence=0.7,
                )
                warnings.append(warning)
                self._warnings.append(warning)

        # Prune old warnings to prevent memory leak
        if len(self._warnings) > self._MAX_WARNINGS:
            self._warnings = self._warnings[-self._MAX_WARNINGS:]

        return warnings

    def get_warnings(self, symbol: str | None = None) -> list[EarlyWarning]:
        if symbol:
            return [w for w in self._warnings if w.symbol == symbol]
        return list(self._warnings)

    def get_warnings_by_severity(self, severity: WarningSeverity) -> list[EarlyWarning]:
        return [w for w in self._warnings if w.severity == severity]

    def _metric_to_category(self, metric: str) -> WarningCategory:
        mapping = {
            "revenue_growth": WarningCategory.REVENUE_DETERIORATION,
            "operating_margin": WarningCategory.MARGIN_COMPRESSION,
            "net_margin": WarningCategory.MARGIN_COMPRESSION,
            "operating_cashflow": WarningCategory.CASHFLOW_DIVERGENCE,
            "free_cashflow": WarningCategory.CASHFLOW_DIVERGENCE,
            "debt_equity": WarningCategory.LEVERAGE_INCREASE,
            "interest_coverage": WarningCategory.LEVERAGE_INCREASE,
            "inventory_turnover": WarningCategory.INVENTORY_BUILDUP,
            "receivables_turnover": WarningCategory.RECEIVABLES_GROWTH,
            "pe_ratio": WarningCategory.VALUATION_EXTREME,
            "volume": WarningCategory.UNUSUAL_VOLUME,
        }
        return mapping.get(metric, WarningCategory.REVENUE_DETERIORATION)

    def _generate_description(self, metric: str, change_pct: float, threshold_pct: float) -> str:
        direction = "declined" if change_pct < 0 else "increased"
        return f"{metric} {direction} {abs(change_pct):.1f}% (threshold: {abs(threshold_pct):.1f}%)"

    def _generate_investigation(self, metric: str, category: WarningCategory) -> str:
        investigations = {
            WarningCategory.REVENUE_DETERIORATION: "Investigate demand trends, competitive dynamics, and market share changes",
            WarningCategory.MARGIN_COMPRESSION: "Analyze cost structure, pricing power, and input cost trends",
            WarningCategory.CASHFLOW_DIVERGENCE: "Compare earnings quality, working capital changes, and capex patterns",
            WarningCategory.LEVERAGE_INCREASE: "Review debt maturity schedule, refinancing risk, and interest coverage",
            WarningCategory.INVENTORY_BUILDUP: "Assess inventory aging, obsolescence risk, and demand outlook",
            WarningCategory.RECEIVABLES_GROWTH: "Examine customer payment terms, collectability, and DSO trends",
            WarningCategory.VALUATION_EXTREME: "Compare valuation to historical range, peers, and growth expectations",
            WarningCategory.UNUSUAL_VOLUME: "Investigate news flow, institutional activity, and insider transactions",
        }
        return investigations.get(category, "Investigate the metric trend and underlying drivers")
