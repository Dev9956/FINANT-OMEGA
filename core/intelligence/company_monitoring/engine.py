"""FININT OMEGA — Monitoring engine: manages company registrations and alerts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from core.intelligence.company_monitoring.models import (
    CompanyState,
    MaterialityLevel,
    MonitoringAlert,
    MonitorMetric,
    StateDiff,
)
from core.intelligence.company_monitoring.monitor import CompanyMonitor

logger = structlog.get_logger()


class MonitoringEngine:
    """Engine that manages registered companies and generates alerts on state changes."""

    _MAX_ALERTS_PER_SYMBOL = 5000

    def __init__(self) -> None:
        self._monitor = CompanyMonitor()
        self._registered: dict[str, set[MonitorMetric]] = {}
        self._states: dict[str, CompanyState] = {}
        self._alerts: dict[str, list[MonitoringAlert]] = {}

    def register_company(self, symbol: str, metrics_to_monitor: list[MonitorMetric]) -> None:
        """Register a company for monitoring with specific metrics."""
        try:
            self._registered[symbol] = set(metrics_to_monitor)
            self._alerts[symbol] = []
            logger.info("company_registered", symbol=symbol, metrics=[m.value for m in metrics_to_monitor])
        except Exception as e:
            logger.error("register_company_failed", symbol=symbol, error=str(e))
            raise

    def unregister_company(self, symbol: str) -> None:
        """Unregister a company from monitoring."""
        try:
            self._registered.pop(symbol, None)
            self._states.pop(symbol, None)
            self._alerts.pop(symbol, None)
            logger.info("company_unregistered", symbol=symbol)
        except Exception as e:
            logger.error("unregister_company_failed", symbol=symbol, error=str(e))
            raise

    def update_state(self, symbol: str, new_data: dict) -> list[MonitoringAlert]:
        """Update company state and generate alerts for material changes."""
        if symbol not in self._registered:
            raise ValueError(f"Company {symbol} is not registered for monitoring")
        try:

            new_state = self._monitor.snapshot(symbol, new_data)
            alerts: list[MonitoringAlert] = []

            if symbol in self._states:
                previous_state = self._states[symbol]
                diffs = self._monitor.diff(previous_state, new_state)
                for diff in diffs:
                    materiality = self._monitor.score_materiality_level(diff)
                    if self._monitor.should_alert(diff, materiality):
                        alert = MonitoringAlert(
                            alert_id=str(uuid.uuid4()),
                            symbol=symbol,
                            metric=diff.metric,
                            diff=diff,
                            materiality=materiality,
                            thesis_impact="neutral",
                            created_at=datetime.now(timezone.utc),
                        )
                        alerts.append(alert)
                        self._alerts[symbol].append(alert)
                        # Prune old alerts to prevent memory leak
                        if len(self._alerts[symbol]) > self._MAX_ALERTS_PER_SYMBOL:
                            self._alerts[symbol] = self._alerts[symbol][-self._MAX_ALERTS_PER_SYMBOL:]
                        logger.info(
                            "alert_generated",
                            symbol=symbol,
                            metric=diff.metric,
                            materiality=materiality.value,
                        )

            self._states[symbol] = new_state
            return alerts
        except Exception as e:
            logger.error("update_state_failed", symbol=symbol, error=str(e))
            return []

    def get_alerts(self, symbol: str, since: datetime | None = None) -> list[MonitoringAlert]:
        """Get alerts for a company, optionally filtered by time."""
        try:
            alerts = self._alerts.get(symbol, [])
            if since:
                alerts = [a for a in alerts if a.created_at >= since]
            return alerts
        except Exception as e:
            logger.error("get_alerts_failed", symbol=symbol, error=str(e))
            return []

    def get_state(self, symbol: str) -> CompanyState | None:
        """Get the current state of a monitored company."""
        return self._states.get(symbol)
