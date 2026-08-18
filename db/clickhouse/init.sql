-- FININT OMEGA — ClickHouse initialization

CREATE TABLE IF NOT EXISTS schema_version (
    version UInt32,
    description String,
    applied_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY version;

INSERT INTO schema_version (version, description) VALUES
(0, 'Initial schema');

-- Placeholder for future market data tables
-- CREATE TABLE IF NOT EXISTS market_daily (
--     ticker String,
--     date Date,
--     open Float64,
--     high Float64,
--     low Float64,
--     close Float64,
--     volume UInt64,
--     adj_close Float64
-- ) ENGINE = MergeTree()
-- PARTITION BY toYYYYMM(date)
-- ORDER BY (ticker, date);
