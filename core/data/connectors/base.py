"""FININT OMEGA — Data connectors framework with production infrastructure."""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class DataQuality(Enum):
    """Data quality levels."""
    REAL = "real"
    SYNTHETIC = "synthetic"
    MOCK = "mock"
    UNKNOWN = "unknown"


@dataclass
class DataProvenance:
    """Provenance metadata for every data item."""
    source: str
    provider: str
    retrieved_at: datetime
    event_time: datetime | None = None
    publication_time: datetime | None = None
    available_time: datetime | None = None
    entity_id: str | None = None
    instrument_id: str | None = None
    raw_reference_id: str | None = None
    quality: DataQuality = DataQuality.UNKNOWN
    content_hash: str | None = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "provider": self.provider,
            "retrieved_at": self.retrieved_at.isoformat(),
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "publication_time": self.publication_time.isoformat() if self.publication_time else None,
            "available_time": self.available_time.isoformat() if self.available_time else None,
            "entity_id": self.entity_id,
            "instrument_id": self.instrument_id,
            "raw_reference_id": self.raw_reference_id,
            "quality": self.quality.value,
            "content_hash": self.content_hash,
        }


@dataclass
class DataRecord:
    """A single data record with provenance."""
    data: dict[str, Any]
    provenance: DataProvenance

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


@dataclass
class ConnectorConfig:
    """Configuration for a data connector."""
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    rate_limit_per_second: float = 10.0
    cache_ttl_seconds: float = 300.0
    max_cache_size: int = 1000
    enabled: bool = True


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float) -> None:
        self._rate = rate
        self._tokens = rate
        self._last_refill = time.monotonic()

    def acquire(self) -> bool:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
        self._last_refill = now
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    def wait(self) -> None:
        while not self.acquire():
            time.sleep(0.01)


class DataCache:
    """Simple in-memory LRU cache for data records."""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 300.0) -> None:
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, list[DataRecord]]] = {}

    def _make_key(self, **kwargs: Any) -> str:
        parts = [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return hashlib.md5("|".join(parts).encode()).hexdigest()

    def get(self, **kwargs: Any) -> list[DataRecord] | None:
        key = self._make_key(**kwargs)
        if key in self._cache:
            ts, records = self._cache[key]
            if time.time() - ts < self._ttl:
                return records
            del self._cache[key]
        return None

    def put(self, records: list[DataRecord], **kwargs: Any) -> None:
        key = self._make_key(**kwargs)
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), records)


class BaseConnector(ABC):
    """Base class for data connectors with retry, rate limiting, caching, and provenance."""

    def __init__(
        self,
        source_id: str,
        name: str,
        config: ConnectorConfig | None = None,
    ) -> None:
        self.source_id = source_id
        self.name = name
        self.config = config or ConnectorConfig()
        self._rate_limiter = RateLimiter(self.config.rate_limit_per_second)
        self._cache = DataCache(
            max_size=self.config.max_cache_size,
            ttl_seconds=self.config.cache_ttl_seconds,
        )
        self._quality = DataQuality.REAL
        self._call_count = 0
        self._error_count = 0
        self._last_error: str | None = None

    @abstractmethod
    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Provider-specific fetch implementation."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the source is reachable."""
        ...

    def fetch(self, **kwargs: Any) -> list[DataRecord]:
        """Fetch data with retry, rate limiting, caching, and provenance."""
        if not self.config.enabled:
            logger.warning("connector_disabled", source_id=self.source_id)
            return []

        # Check cache
        cached = self._cache.get(**kwargs)
        if cached is not None:
            logger.debug("cache_hit", source_id=self.source_id)
            return cached

        # Rate limit
        self._rate_limiter.wait()

        # Retry logic
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries):
            try:
                self._call_count += 1
                raw_records = self._fetch_raw(**kwargs)
                records = self._wrap_with_provenance(raw_records, **kwargs)
                self._cache.put(records, **kwargs)
                logger.info(
                    "fetch_success",
                    source_id=self.source_id,
                    records=len(records),
                    attempt=attempt + 1,
                )
                return records
            except Exception as e:
                last_error = e
                self._error_count += 1
                self._last_error = str(e)
                logger.warning(
                    "fetch_retry",
                    source_id=self.source_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay_seconds * (2 ** attempt))

        logger.error(
            "fetch_failed",
            source_id=self.source_id,
            error=str(last_error),
            attempts=self.config.max_retries,
        )
        return []

    def _wrap_with_provenance(self, raw_records: list[dict], **kwargs: Any) -> list[DataRecord]:
        """Wrap raw records with provenance metadata."""
        now = datetime.now(timezone.utc)
        records = []
        for raw in raw_records:
            content_hash = hashlib.sha256(
                str(sorted(raw.items())).encode()
            ).hexdigest()[:16]
            provenance = DataProvenance(
                source=raw.get("_source", self.source_id),
                provider=self.name,
                retrieved_at=now,
                event_time=self._parse_datetime(raw.get("_event_time")),
                publication_time=self._parse_datetime(raw.get("_publication_time")),
                available_time=self._parse_datetime(raw.get("_available_time")),
                entity_id=raw.get("_entity_id"),
                instrument_id=raw.get("_instrument_id", kwargs.get("symbol")),
                raw_reference_id=raw.get("_raw_reference_id"),
                quality=self._quality,
                content_hash=content_hash,
            )
            # Remove internal metadata keys
            clean_data = {k: v for k, v in raw.items() if not k.startswith("_")}
            records.append(DataRecord(data=clean_data, provenance=provenance))
        return records

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    def get_stats(self) -> dict:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "call_count": self._call_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "enabled": self.config.enabled,
        }


# Mock connectors for backward compatibility and testing
class MockMarketConnector(BaseConnector):
    """Mock market data connector for development/testing."""

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(source_id="mock_market", name="Mock Market Data", config=config)
        self._quality = DataQuality.MOCK

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        from datetime import date, timedelta
        symbol = kwargs.get("symbol", "MOCK")
        days = kwargs.get("days", 30)
        base_price = kwargs.get("base_price", 100.0)
        records = []
        price = base_price
        for i in range(days):
            d = date.today() - timedelta(days=days - i)
            change = (hash(f"{symbol}{d}") % 20 - 10) / 100.0
            price = price * (1 + change)
            records.append({
                "symbol": symbol,
                "date": d.isoformat(),
                "open": round(price * 0.99, 2),
                "high": round(price * 1.02, 2),
                "low": round(price * 0.98, 2),
                "close": round(price, 2),
                "volume": 1000000 + (hash(f"{symbol}{d}") % 500000),
            })
        return records

    def health_check(self) -> bool:
        return True


class MockFundamentalsConnector(BaseConnector):
    """Mock fundamentals connector for development/testing."""

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(source_id="mock_fundamentals", name="Mock Fundamentals", config=config)
        self._quality = DataQuality.MOCK

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        from datetime import date
        symbol = kwargs.get("symbol", "MOCK")
        return [{
            "symbol": symbol,
            "period_end": date(2025, 3, 31).isoformat(),
            "statement_type": "income_statement",
            "fiscal_year": 2025,
            "revenue": 1000000000.0,
            "net_income": 150000000.0,
            "eps_diluted": 15.0,
        }]

    def health_check(self) -> bool:
        return True


class MockMacroConnector(BaseConnector):
    """Mock macro data connector for development/testing."""

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(source_id="mock_macro", name="Mock Macro Data", config=config)
        self._quality = DataQuality.MOCK

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        from datetime import date
        return [{
            "indicator_id": "us_gdp_growth",
            "indicator_name": "US GDP Growth Rate",
            "country": "US",
            "date": date(2025, 12, 31).isoformat(),
            "value": 2.5,
            "unit": "percent",
            "frequency": "quarterly",
        }]

    def health_check(self) -> bool:
        return True


# Connector registry
_CONNECTORS: dict[str, type[BaseConnector]] = {}


def register_connector(source_id: str, connector_class: type[BaseConnector]) -> None:
    """Register a connector class."""
    _CONNECTORS[source_id] = connector_class


def get_connector(source_id: str, **kwargs: Any) -> BaseConnector:
    """Get a connector instance by source_id."""
    if source_id not in _CONNECTORS:
        raise ValueError(f"No connector registered for source_id: {source_id}")
    return _CONNECTORS[source_id](**kwargs)


def list_connectors() -> list[str]:
    """List all registered connector source_ids."""
    return list(_CONNECTORS.keys())


# Register built-in mock connectors
register_connector("mock_market", MockMarketConnector)
register_connector("mock_fundamentals", MockFundamentalsConnector)
register_connector("mock_macro", MockMacroConnector)
