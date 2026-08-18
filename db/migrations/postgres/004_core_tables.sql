-- FININT OMEGA — Portfolio, scenarios, digital twins, memos, and remaining tables

-- Portfolio positions
CREATE TABLE IF NOT EXISTS portfolio_positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    symbol VARCHAR(32) NOT NULL,
    quantity DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_cost DOUBLE PRECISION NOT NULL DEFAULT 0,
    side VARCHAR(16) NOT NULL DEFAULT 'long',
    cost_basis DOUBLE PRECISION NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scenarios
CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    title VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    variables JSONB DEFAULT '[]',
    change_table JSONB DEFAULT '[]',
    affected_metrics JSONB DEFAULT '{}',
    risk_level VARCHAR(32) DEFAULT 'medium',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Digital twins
CREATE TABLE IF NOT EXISTS digital_twins (
    twin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    entity VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    snapshots JSONB DEFAULT '[]',
    scenarios JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Investment memos
CREATE TABLE IF NOT EXISTS memos (
    memo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    entity VARCHAR(255) NOT NULL,
    thesis TEXT NOT NULL DEFAULT '',
    bull_case TEXT NOT NULL DEFAULT '',
    bear_case TEXT NOT NULL DEFAULT '',
    base_case TEXT NOT NULL DEFAULT '',
    valuation TEXT NOT NULL DEFAULT '',
    financial_quality TEXT NOT NULL DEFAULT '',
    risks JSONB DEFAULT '[]',
    contradicting_evidence JSONB DEFAULT '[]',
    scenario_analysis JSONB DEFAULT '{}',
    evidence JSONB DEFAULT '[]',
    evidence_limitations JSONB DEFAULT '[]',
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Cross-entity relationships
CREATE TABLE IF NOT EXISTS cross_entity_analyses (
    analysis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    entities JSONB DEFAULT '[]',
    criteria JSONB DEFAULT '[]',
    results JSONB DEFAULT '{}',
    summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Digital twin snapshots
CREATE TABLE IF NOT EXISTS twin_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    twin_id UUID NOT NULL REFERENCES digital_twins(twin_id) ON DELETE CASCADE,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Watchlist
CREATE TABLE IF NOT EXISTS watchlist_items (
    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    symbol VARCHAR(32) NOT NULL,
    notes TEXT DEFAULT '',
    priority VARCHAR(16) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduled research
CREATE TABLE IF NOT EXISTS scheduled_research (
    schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    query TEXT NOT NULL,
    frequency VARCHAR(32) NOT NULL DEFAULT 'daily',
    is_active BOOLEAN DEFAULT TRUE,
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Monitoring targets
CREATE TABLE IF NOT EXISTS monitoring_targets (
    target_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL DEFAULT 'dev-user',
    symbol VARCHAR(32) NOT NULL,
    alert_types JSONB DEFAULT '[]',
    thresholds JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio_positions(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_scenarios_user ON scenarios(user_id);
CREATE INDEX IF NOT EXISTS idx_digital_twins_user ON digital_twins(user_id);
CREATE INDEX IF NOT EXISTS idx_digital_twins_entity ON digital_twins(entity);
CREATE INDEX IF NOT EXISTS idx_memos_user ON memos(user_id);
CREATE INDEX IF NOT EXISTS idx_memos_entity ON memos(entity);
CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist_items(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist_items(symbol);
CREATE INDEX IF NOT EXISTS idx_scheduled_user ON scheduled_research(user_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_user ON monitoring_targets(user_id);

-- Update schema version
INSERT INTO schema_version (version, description) VALUES
(1, 'Portfolio, scenarios, digital twins, memos, watchlist tables')
ON CONFLICT (version) DO NOTHING;
