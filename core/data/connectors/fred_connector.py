"""FININT OMEGA — FRED (Federal Reserve Economic Data) connector."""

from __future__ import annotations

import hashlib
import importlib
import os
from datetime import datetime, timezone
from typing import Any

import structlog

from core.data.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    DataQuality,
    register_connector,
)

logger = structlog.get_logger()

httpx = None


def _get_httpx():
    global httpx
    if httpx is None:
        try:
            httpx = importlib.import_module("httpx")
        except ImportError:
            raise ImportError("httpx is required. Install with: pip install httpx")
    return httpx


# Common FRED series IDs
FRED_SERIES = {
    "gdp_growth": "A191RL1Q225SBEA",
    "unemployment": "UNRATE",
    "inflation_cpi": "CPIAUCSL",
    "inflation_core": "CPILFESL",
    "fed_funds_rate": "FEDFUNDS",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "treasury_3m": "DTB3",
    "yield_curve_10y2y": "T10Y2Y",
    "vix": "VIXCLS",
    "industrial_production": "INDPRO",
    "retail_sales": "RSAFS",
    "housing_starts": "HOUST",
    "consumer_confidence": "UMCSENT",
    "pmi_manufacturing": "MANEMP",
    "m2_money_supply": "M2SL",
    "dollar_index": "DTWEXBGS",
    "oil_wti": "DCOILWTICO",
    "gold_price": "GOLDAMGBD228NLBM",
    "sp500": "SP500",
}


class FREDConnector(BaseConnector):
    """Federal Reserve Economic Data connector.

    Requires a FRED API key (free from https://fred.stlouisfed.org/docs/api/api_key.html).
    """

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    def __init__(self, config: ConnectorConfig | None = None, api_key: str | None = None) -> None:
        super().__init__(
            source_id="fred",
            name="FRED (Federal Reserve Economic Data)",
            config=config or ConnectorConfig(
                timeout_seconds=30.0,
                max_retries=3,
                retry_delay_seconds=1.0,
                rate_limit_per_second=5.0,  # FRED allows 120 req/min
                cache_ttl_seconds=3600.0,
            ),
        )
        self._api_key = api_key or os.environ.get("FRED_API_KEY", "")
        self._quality = DataQuality.REAL

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Fetch data from FRED."""
        series_id = kwargs.get("series_id") or kwargs.get("indicator")
        if not series_id:
            # Try to map common names
            indicator_name = kwargs.get("indicator_name", "")
            series_id = FRED_SERIES.get(indicator_name, indicator_name)

        if not series_id:
            raise ValueError("series_id or indicator_name is required")

        if not self._api_key:
            logger.warning("fred_no_api_key")
            return self._fetch_without_api_key(series_id)

        httpx_mod = _get_httpx()
        params = {
            "series_id": series_id,
            "api_key": self._api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": kwargs.get("limit", 500),
        }

        # Add date range if provided
        if "start_date" in kwargs:
            params["observation_start"] = kwargs["start_date"]
        if "end_date" in kwargs:
            params["observation_end"] = kwargs["end_date"]

        try:
            resp = httpx_mod.get(
                self.BASE_URL,
                params=params,
                timeout=self.config.timeout_seconds,
            )
            resp.raise_for_status()
            data = resp.json()

            observations = data.get("observations", [])
            records = []
            for obs in observations:
                if obs.get("value") == ".":
                    continue  # Skip missing values
                records.append({
                    "series_id": series_id,
                    "indicator_name": kwargs.get("indicator_name", series_id),
                    "date": obs.get("date", ""),
                    "value": float(obs.get("value", 0)),
                    "unit": kwargs.get("unit", "value"),
                    "frequency": data.get("frequency", ""),
                    "title": data.get("title", ""),
                    "_source": self.source_id,
                    "_entity_id": series_id,
                    "_event_time": obs.get("date"),
                    "_publication_time": obs.get("date"),
                    "_raw_reference_id": f"fred:{series_id}:{obs.get('date')}",
                })

            return records

        except Exception as e:
            logger.error("fred_fetch_error", series_id=series_id, error=str(e))
            return []

    def _fetch_without_api_key(self, series_id: str) -> list[dict]:
        """Fetch data without API key using FRED's public CSV endpoint."""
        httpx_mod = _get_httpx()
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        try:
            resp = httpx_mod.get(url, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                return []

            records = []
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) == 2 and parts[1] != ".":
                    records.append({
                        "series_id": series_id,
                        "indicator_name": series_id,
                        "date": parts[0],
                        "value": float(parts[1]),
                        "unit": "value",
                        "frequency": "daily",
                        "title": series_id,
                        "_source": self.source_id,
                        "_entity_id": series_id,
                        "_event_time": parts[0],
                        "_publication_time": parts[0],
                        "_raw_reference_id": f"fred:{series_id}:{parts[0]}",
                    })
            return records
        except Exception as e:
            logger.error("fred_csv_fetch_error", series_id=series_id, error=str(e))
            return []

    def health_check(self) -> bool:
        try:
            httpx_mod = _get_httpx()
            if self._api_key:
                resp = httpx_mod.get(
                    "https://api.stlouisfed.org/fred/series",
                    params={
                        "series_id": "UNRATE",
                        "api_key": self._api_key,
                        "file_type": "json",
                    },
                    timeout=10.0,
                )
                return resp.status_code == 200
            else:
                resp = httpx_mod.get(
                    "https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE",
                    timeout=10.0,
                )
                return resp.status_code == 200
        except Exception:
            return False


register_connector("fred", FREDConnector)
