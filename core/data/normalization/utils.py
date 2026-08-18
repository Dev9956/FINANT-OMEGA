"""FININT OMEGA — Data normalization utilities."""

from __future__ import annotations

from datetime import date, datetime


def parse_date(value: str | date | datetime) -> date:
    """Parse a date from various formats."""
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {value}")
    raise TypeError(f"Unsupported date type: {type(value)}")


def normalize_string(value: str | None) -> str:
    """Normalize a string: strip, uppercase, collapse whitespace."""
    if value is None:
        return ""
    return " ".join(value.strip().split()).upper()


def normalize_symbol(symbol: str) -> str:
    """Normalize a financial symbol."""
    return normalize_string(symbol)


def normalize_currency(currency: str | None) -> str:
    """Normalize currency code to ISO 4217."""
    if not currency:
        return "USD"
    return normalize_string(currency)[:3]


def safe_float(value: float | int | str | None, default: float = 0.0) -> float:
    """Safely convert to float."""
    if value is None:
        return default
    try:
        result = float(value)
        if result != result:  # NaN check
            return default
        return result
    except (ValueError, TypeError):
        return default


def safe_int(value: float | int | str | None, default: int = 0) -> int:
    """Safely convert to int."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default
