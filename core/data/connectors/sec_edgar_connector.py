"""FININT OMEGA — SEC EDGAR data connector for real filings."""

from __future__ import annotations

import hashlib
import importlib
import json
import time
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

# Lazy import
httpx = None


def _get_httpx():
    global httpx
    if httpx is None:
        try:
            httpx = importlib.import_module("httpx")
        except ImportError:
            raise ImportError("httpx is required. Install with: pip install httpx")
    return httpx


class SECEdgarCompanyConnector(BaseConnector):
    """SEC EDGAR company facts connector.

    Fetches XBRL financial data directly from SEC EDGAR API.
    Free, no API key required, but must respect rate limits.
    """

    BASE_URL = "https://data.sec.gov"
    HEADERS = {
        "User-Agent": "FININT OMEGA Research Team research@finint-omega.com",
        "Accept": "application/json",
    }

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        super().__init__(
            source_id="sec_edgar",
            name="SEC EDGAR",
            config=config or ConnectorConfig(
                timeout_seconds=30.0,
                max_retries=3,
                retry_delay_seconds=2.0,
                rate_limit_per_second=0.5,  # SEC requires max 10 req/sec
                cache_ttl_seconds=86400.0,  # 24 hour cache for filings
            ),
        )
        self._quality = DataQuality.REAL

    def _get_cik(self, symbol: str) -> str | None:
        """Get CIK number from ticker symbol using SEC company tickers."""
        httpx_mod = _get_httpx()
        url = "https://www.sec.gov/files/company_tickers.json"
        try:
            resp = httpx_mod.get(url, headers=self.HEADERS, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == symbol.upper():
                    return str(entry["cik_str"]).zfill(10)
        except Exception as e:
            logger.warning("sec_edgar_cik_lookup_failed", symbol=symbol, error=str(e))
        return None

    def _fetch_raw(self, **kwargs: Any) -> list[dict]:
        """Fetch company facts from SEC EDGAR."""
        symbol = kwargs.get("symbol")
        if not symbol:
            raise ValueError("symbol is required")

        httpx_mod = _get_httpx()
        cik = self._get_cik(symbol)
        if not cik:
            logger.warning("sec_edgar_cik_not_found", symbol=symbol)
            return []

        records = []

        # Fetch company facts (XBRL data)
        url = f"{self.BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
        try:
            resp = httpx_mod.get(url, headers=self.HEADERS, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            facts = resp.json()

            company_name = facts.get("entityName", "")

            # Process US-GAAP facts
            us_gaap = facts.get("facts", {}).get("us-gaap", {})
            for concept, data in us_gaap.items():
                units = data.get("units", {})
                for unit_key, values in units.items():
                    if unit_key in ("USD", "USD/shares", "shares"):
                        for entry in values[-8:]:  # Last 8 filings
                            period_end = entry.get("end", "")
                            records.append({
                                "symbol": symbol,
                                "company_name": company_name,
                                "cik": cik,
                                "data_type": "xbrl_fact",
                                "concept": concept,
                                "value": entry.get("val"),
                                "unit": unit_key,
                                "period_end": period_end,
                                "period_type": entry.get("fp", ""),
                                "filing_date": entry.get("filed", ""),
                                "form_type": entry.get("form", ""),
                                "_source": self.source_id,
                                "_entity_id": symbol,
                                "_event_time": period_end,
                                "_publication_time": entry.get("filed"),
                                "_raw_reference_id": f"sec-edgar:{cik}:{concept}:{period_end}",
                            })

        except Exception as e:
            logger.error("sec_edgar_facts_error", symbol=symbol, error=str(e))

        # Fetch recent filings
        url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
        try:
            resp = httpx_mod.get(url, headers=self.HEADERS, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            submissions = resp.json()

            recent = submissions.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])

            for i in range(min(20, len(forms))):
                records.append({
                    "symbol": symbol,
                    "company_name": submissions.get("name", ""),
                    "data_type": "filing",
                    "form_type": forms[i] if i < len(forms) else "",
                    "filing_date": dates[i] if i < len(dates) else "",
                    "accession_number": accessions[i] if i < len(accessions) else "",
                    "primary_document": primary_docs[i] if i < len(primary_docs) else "",
                    "_source": self.source_id,
                    "_entity_id": symbol,
                    "_publication_time": dates[i] if i < len(dates) else "",
                    "_raw_reference_id": f"sec-edgar:{cik}:{accessions[i] if i < len(accessions) else ''}",
                })

        except Exception as e:
            logger.error("sec_edgar_submissions_error", symbol=symbol, error=str(e))

        return records

    def health_check(self) -> bool:
        try:
            httpx_mod = _get_httpx()
            resp = httpx_mod.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=self.HEADERS,
                timeout=10.0,
            )
            return resp.status_code == 200
        except Exception:
            return False


register_connector("sec_edgar", SECEdgarCompanyConnector)
