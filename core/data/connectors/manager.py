"""FININT OMEGA — Data Provider Manager orchestrates all connectors."""

from __future__ import annotations

from typing import Any

import structlog

from core.data.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    DataRecord,
    list_connectors,
)

logger = structlog.get_logger()


class DataProviderManager:
    """Manages multiple data providers with unified interface.

    Usage:
        manager = DataProviderManager()
        records = manager.fetch("yfinance_market", symbol="AAPL", period="1y")
    """

    def __init__(self, default_config: ConnectorConfig | None = None) -> None:
        self._default_config = default_config or ConnectorConfig()
        self._instances: dict[str, BaseConnector] = {}
        self._configs: dict[str, ConnectorConfig] = {}

    def register(self, source_id: str, config: ConnectorConfig | None = None) -> None:
        """Register a connector with optional custom config."""
        self._configs[source_id] = config or self._default_config

    def _get_instance(self, source_id: str) -> BaseConnector:
        """Get or create connector instance."""
        if source_id not in self._instances:
            from core.data.connectors.base import get_connector
            config = self._configs.get(source_id)
            self._instances[source_id] = get_connector(source_id, config=config)
        return self._instances[source_id]

    def fetch(self, source_id: str, **kwargs: Any) -> list[DataRecord]:
        """Fetch data from a specific provider."""
        connector = self._get_instance(source_id)
        return connector.fetch(**kwargs)

    def fetch_market(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> list[DataRecord]:
        """Convenience method for market data."""
        return self.fetch(
            "yfinance_market",
            symbol=symbol,
            period=period,
            interval=interval,
        )

    def fetch_fundamentals(self, symbol: str) -> list[DataRecord]:
        """Convenience method for fundamentals."""
        return self.fetch("yfinance_fundamentals", symbol=symbol)

    def fetch_earnings(self, symbol: str) -> list[DataRecord]:
        """Convenience method for earnings data."""
        return self.fetch("yfinance_earnings", symbol=symbol)

    def fetch_filings(self, symbol: str) -> list[DataRecord]:
        """Convenience method for SEC filings."""
        return self.fetch("sec_edgar", symbol=symbol)

    def fetch_macro(self, indicator: str, **kwargs: Any) -> list[DataRecord]:
        """Convenience method for macro data."""
        return self.fetch("fred", indicator_name=indicator, **kwargs)

    def health_check_all(self) -> dict[str, bool]:
        """Check health of all registered connectors."""
        results = {}
        for source_id in list_connectors():
            try:
                connector = self._get_instance(source_id)
                results[source_id] = connector.health_check()
            except Exception as e:
                results[source_id] = False
                logger.error("health_check_failed", source_id=source_id, error=str(e))
        return results

    def get_stats(self) -> dict[str, dict]:
        """Get statistics for all registered connectors."""
        stats = {}
        for source_id in list_connectors():
            try:
                connector = self._get_instance(source_id)
                stats[source_id] = connector.get_stats()
            except Exception:
                stats[source_id] = {"error": "failed to get stats"}
        return stats


# Singleton instance
_manager: DataProviderManager | None = None


def get_data_manager() -> DataProviderManager:
    """Get the global data provider manager."""
    global _manager
    if _manager is None:
        _manager = DataProviderManager()
    return _manager
