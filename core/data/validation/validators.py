"""FININT OMEGA — Data validation utilities."""

from __future__ import annotations

from datetime import date

from core.data.schemas import MarketOHLCV


def validate_ohlcv(record: dict) -> tuple[bool, list[str]]:
    """Validate an OHLCV record."""
    errors = []

    required = ["symbol", "date", "open", "high", "low", "close"]
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    if record["high"] < record["low"]:
        errors.append("High is less than low")

    if record["open"] <= 0 or record["close"] <= 0:
        errors.append("Open or close price is zero or negative")

    if record.get("volume", 0) < 0:
        errors.append("Volume is negative")

    return len(errors) == 0, errors


def validate_financial_statement(record: dict) -> tuple[bool, list[str]]:
    """Validate a financial statement record."""
    errors = []

    required = ["symbol", "period_end", "statement_type"]
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    if "statement_type" in record:
        valid_types = {"income_statement", "balance_sheet", "cash_flow"}
        if record["statement_type"] not in valid_types:
            errors.append(f"Invalid statement_type: {record['statement_type']}")

    return len(errors) == 0, errors


def validate_date_range(
    start: date | None, end: date | None
) -> tuple[bool, list[str]]:
    """Validate date range consistency."""
    errors = []
    if start and end and start > end:
        errors.append(f"Start date {start} is after end date {end}")
    if start and start.year < 1900:
        errors.append(f"Start date year {start.year} seems unreasonable")
    return len(errors) == 0, errors
