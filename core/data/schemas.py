"""FININT OMEGA — Domain schemas for financial data."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    INR = "INR"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


class Exchange(str, Enum):
    """Supported exchanges."""

    NSE = "NSE"
    BSE = "BSE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    LSE = "LSE"
    OTHER = "OTHER"


class MarketOHLCV(BaseModel):
    """Daily OHLCV market data record."""

    symbol: str
    date: date
    exchange: Exchange = Exchange.OTHER
    currency: Currency = Currency.USD
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float | None = None
    volume: int = 0
    turnover: float | None = None


class CompanyIdentifier(BaseModel):
    """Company identification."""

    symbol: str
    name: str
    exchange: Exchange = Exchange.OTHER
    currency: Currency = Currency.USD
    isin: str | None = None
    cusip: str | None = None
    sedol: str | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None


class FinancialStatement(BaseModel):
    """Financial statement record (income statement, balance sheet, cash flow)."""

    symbol: str
    period_end: date
    statement_type: str  # income_statement, balance_sheet, cash_flow
    fiscal_year: int | None = None
    fiscal_quarter: int | None = None
    currency: Currency = Currency.USD
    # Income statement
    revenue: float | None = None
    cost_of_goods_sold: float | None = None
    gross_profit: float | None = None
    operating_expenses: float | None = None
    ebitda: float | None = None
    ebit: float | None = None
    interest_expense: float | None = None
    net_income: float | None = None
    eps_diluted: float | None = None
    eps_basic: float | None = None
    shares_outstanding: float | None = None
    # Balance sheet
    total_assets: float | None = None
    total_liabilities: float | None = None
    total_equity: float | None = None
    total_debt: float | None = None
    cash_and_equivalents: float | None = None
    short_term_investments: float | None = None
    accounts_receivable: float | None = None
    inventory: float | None = None
    # Cash flow
    operating_cash_flow: float | None = None
    capital_expenditures: float | None = None
    free_cash_flow: float | None = None
    dividends_paid: float | None = None
    share_repurchases: float | None = None


class FinancialRatios(BaseModel):
    """Derived financial ratios."""

    symbol: str
    date: date
    # Valuation
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    ev_ebitda: float | None = None
    ev_sales: float | None = None
    # Profitability
    roe: float | None = None
    roce: float | None = None
    roa: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    # Leverage
    debt_equity: float | None = None
    current_ratio: float | None = None
    quick_ratio: float | None = None
    # Growth
    revenue_growth_yoy: float | None = None
    earnings_growth_yoy: float | None = None
    # Yield
    fcf_yield: float | None = None
    dividend_yield: float | None = None


class MacroIndicator(BaseModel):
    """Macroeconomic indicator record."""

    indicator_id: str
    indicator_name: str
    country: str
    date: date
    value: float
    unit: str = ""
    source: str = ""
    frequency: str = "monthly"  # daily, weekly, monthly, quarterly, yearly


class CorporateAction(BaseModel):
    """Corporate action record (splits, dividends, etc.)."""

    symbol: str
    action_type: str  # split, dividend, bonus, rights
    ex_date: date
    effective_date: date | None = None
    ratio: float | None = None  # e.g. 2 for 2:1 split
    dividend_per_share: float | None = None
    description: str = ""
