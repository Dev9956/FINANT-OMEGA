-- FININT OMEGA — ClickHouse schema for market data and analytics

-- Source registry
CREATE TABLE IF NOT EXISTS source_registry (
    source_id String,
    source_name String,
    source_type String,
    provider String,
    license String,
    refresh_frequency String,
    coverage String,
    status String,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    metadata String DEFAULT '{}'
) ENGINE = MergeTree()
ORDER BY source_id;

-- Dataset registry
CREATE TABLE IF NOT EXISTS dataset_registry (
    dataset_id String,
    source_id String,
    name String,
    description String,
    stage String,
    schema_version UInt32,
    data_version UInt32,
    coverage_start Date,
    coverage_end Date,
    row_count UInt64,
    quality_status String,
    timezone String,
    currency String,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now(),
    metadata String DEFAULT '{}'
) ENGINE = MergeTree()
ORDER BY (dataset_id, source_id);

-- Market daily OHLCV
CREATE TABLE IF NOT EXISTS market_daily (
    symbol String,
    date Date,
    exchange String,
    currency String,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    adjusted_close Float64,
    volume UInt64,
    turnover Float64,
    data_version UInt32 DEFAULT 1,
    inserted_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (symbol, date);

-- Company identifiers
CREATE TABLE IF NOT EXISTS companies (
    symbol String,
    name String,
    exchange String,
    currency String,
    isin String DEFAULT '',
    sector String DEFAULT '',
    industry String DEFAULT '',
    country String DEFAULT '',
    is_active UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (symbol, exchange);

-- Financial statements
CREATE TABLE IF NOT EXISTS financial_statements (
    symbol String,
    period_end Date,
    statement_type String,
    fiscal_year UInt32,
    fiscal_quarter UInt32,
    currency String,
    revenue Float64 DEFAULT 0,
    cost_of_goods_sold Float64 DEFAULT 0,
    gross_profit Float64 DEFAULT 0,
    operating_expenses Float64 DEFAULT 0,
    ebitda Float64 DEFAULT 0,
    ebit Float64 DEFAULT 0,
    interest_expense Float64 DEFAULT 0,
    net_income Float64 DEFAULT 0,
    eps_diluted Float64 DEFAULT 0,
    eps_basic Float64 DEFAULT 0,
    shares_outstanding Float64 DEFAULT 0,
    total_assets Float64 DEFAULT 0,
    total_liabilities Float64 DEFAULT 0,
    total_equity Float64 DEFAULT 0,
    total_debt Float64 DEFAULT 0,
    cash_and_equivalents Float64 DEFAULT 0,
    operating_cash_flow Float64 DEFAULT 0,
    capital_expenditures Float64 DEFAULT 0,
    free_cash_flow Float64 DEFAULT 0,
    data_version UInt32 DEFAULT 1,
    inserted_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY (statement_type, toYYYYMM(period_end))
ORDER BY (symbol, period_end, statement_type);

-- Financial ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    symbol String,
    date Date,
    pe_ratio Float64 DEFAULT 0,
    pb_ratio Float64 DEFAULT 0,
    ev_ebitda Float64 DEFAULT 0,
    ev_sales Float64 DEFAULT 0,
    roe Float64 DEFAULT 0,
    roce Float64 DEFAULT 0,
    roa Float64 DEFAULT 0,
    gross_margin Float64 DEFAULT 0,
    operating_margin Float64 DEFAULT 0,
    net_margin Float64 DEFAULT 0,
    debt_equity Float64 DEFAULT 0,
    current_ratio Float64 DEFAULT 0,
    quick_ratio Float64 DEFAULT 0,
    revenue_growth_yoy Float64 DEFAULT 0,
    earnings_growth_yoy Float64 DEFAULT 0,
    fcf_yield Float64 DEFAULT 0,
    dividend_yield Float64 DEFAULT 0,
    inserted_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (symbol, date);

-- Macro indicators
CREATE TABLE IF NOT EXISTS macro_indicators (
    indicator_id String,
    indicator_name String,
    country String,
    date Date,
    value Float64,
    unit String,
    source String,
    frequency String,
    inserted_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (indicator_id, country, date);

-- Corporate actions
CREATE TABLE IF NOT EXISTS corporate_actions (
    symbol String,
    action_type String,
    ex_date Date,
    effective_date Date,
    ratio Float64 DEFAULT 0,
    dividend_per_share Float64 DEFAULT 0,
    description String,
    inserted_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(ex_date)
ORDER BY (symbol, ex_date, action_type);

-- Data quality issues
CREATE TABLE IF NOT EXISTS data_quality_issues (
    issue_id String,
    dataset_id String,
    check_name String,
    severity String,
    description String,
    affected_rows UInt64 DEFAULT 0,
    detected_at DateTime DEFAULT now(),
    resolved UInt8 DEFAULT 0
) ENGINE = MergeTree()
ORDER BY (dataset_id, detected_at);

-- Data lineage
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id String,
    target_dataset_id String,
    source_dataset_ids Array(String),
    transformation String,
    pipeline_run_id String,
    input_row_count UInt64 DEFAULT 0,
    output_row_count UInt64 DEFAULT 0,
    started_at DateTime DEFAULT now(),
    completed_at DateTime,
    success UInt8 DEFAULT 1,
    error_message String DEFAULT ''
) ENGINE = MergeTree()
ORDER BY (target_dataset_id, started_at);
