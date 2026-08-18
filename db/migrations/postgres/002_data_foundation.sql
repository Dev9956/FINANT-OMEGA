-- FININT OMEGA — PostgreSQL schema for metadata, research, and configuration

-- Source registry
CREATE TABLE IF NOT EXISTS source_registry (
    source_id VARCHAR(64) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    license VARCHAR(128) DEFAULT 'unknown',
    terms_url TEXT,
    refresh_frequency VARCHAR(32) DEFAULT 'unknown',
    coverage TEXT DEFAULT '',
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Dataset registry
CREATE TABLE IF NOT EXISTS dataset_registry (
    dataset_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES source_registry(source_id),
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    stage VARCHAR(16) NOT NULL,
    schema_version INTEGER DEFAULT 1,
    data_version INTEGER DEFAULT 1,
    coverage_start TIMESTAMPTZ,
    coverage_end TIMESTAMPTZ,
    row_count BIGINT,
    quality_status VARCHAR(16) DEFAULT 'unknown',
    timezone VARCHAR(32) DEFAULT 'UTC',
    currency VARCHAR(8) DEFAULT 'USD',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Data quality issues
CREATE TABLE IF NOT EXISTS data_quality_issues (
    issue_id VARCHAR(64) PRIMARY KEY,
    dataset_id VARCHAR(64) NOT NULL REFERENCES dataset_registry(dataset_id),
    check_name VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    description TEXT NOT NULL,
    affected_rows BIGINT DEFAULT 0,
    affected_columns TEXT[] DEFAULT '{}',
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

-- Data lineage
CREATE TABLE IF NOT EXISTS data_lineage (
    lineage_id VARCHAR(64) PRIMARY KEY,
    target_dataset_id VARCHAR(64) NOT NULL REFERENCES dataset_registry(dataset_id),
    source_dataset_ids TEXT[] DEFAULT '{}',
    source_records TEXT[] DEFAULT '{}',
    transformation TEXT NOT NULL,
    pipeline_run_id VARCHAR(64),
    input_row_count BIGINT,
    output_row_count BIGINT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Pipeline runs
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    pipeline_name VARCHAR(128) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    input_rows BIGINT,
    output_rows BIGINT,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Companies
CREATE TABLE IF NOT EXISTS companies (
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(16) NOT NULL DEFAULT 'OTHER',
    name VARCHAR(255) NOT NULL,
    currency VARCHAR(8) DEFAULT 'USD',
    isin VARCHAR(16),
    sector VARCHAR(128),
    industry VARCHAR(128),
    country VARCHAR(64),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (symbol, exchange)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_dataset_source ON dataset_registry(source_id);
CREATE INDEX IF NOT EXISTS idx_quality_dataset ON data_quality_issues(dataset_id);
CREATE INDEX IF NOT EXISTS idx_lineage_target ON data_lineage(target_dataset_id);
CREATE INDEX IF NOT EXISTS idx_lineage_source ON data_lineage USING GIN(source_dataset_ids);
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);
