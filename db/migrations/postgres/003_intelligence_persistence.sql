-- FININT OMEGA — PostgreSQL schema for intelligence persistence

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    organization_id UUID,
    role VARCHAR(32) NOT NULL DEFAULT 'analyst',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) UNIQUE NOT NULL,
    plan VARCHAR(32) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    key_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(128) NOT NULL,
    permissions JSONB DEFAULT '[]',
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Research runs table
CREATE TABLE IF NOT EXISTS research_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    query TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    evidence_count INTEGER DEFAULT 0,
    confidence_score FLOAT,
    model_used VARCHAR(64),
    tokens_used INTEGER DEFAULT 0,
    cost_usd FLOAT DEFAULT 0.0,
    result JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Investment theses table
CREATE TABLE IF NOT EXISTS theses (
    thesis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    symbol VARCHAR(32) NOT NULL,
    title VARCHAR(255) NOT NULL,
    thesis_text TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    confidence FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    invalidated_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- Thesis versions table
CREATE TABLE IF NOT EXISTS thesis_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thesis_id UUID NOT NULL REFERENCES theses(thesis_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    thesis_text TEXT NOT NULL,
    confidence FLOAT,
    change_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),
    UNIQUE(thesis_id, version_number)
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    symbol VARCHAR(32),
    prediction_text TEXT NOT NULL,
    target_date DATE,
    prediction_value FLOAT,
    direction VARCHAR(16),
    confidence FLOAT DEFAULT 0.5,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    resolved_at TIMESTAMPTZ,
    resolution_value FLOAT,
    resolution_correct BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Evidence table
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_text TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    supporting BOOLEAN DEFAULT TRUE,
    retrieved_at TIMESTAMPTZ DEFAULT NOW(),
    publication_time TIMESTAMPTZ,
    data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- Claims table
CREATE TABLE IF NOT EXISTS claims (
    claim_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_run_id UUID REFERENCES research_runs(run_id),
    thesis_id UUID REFERENCES theses(thesis_id),
    claim_text TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    confidence FLOAT DEFAULT 0.5,
    evidence_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    verified_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    symbol VARCHAR(32),
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Agent executions table
CREATE TABLE IF NOT EXISTS agent_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    research_run_id UUID REFERENCES research_runs(run_id),
    agent_role VARCHAR(64) NOT NULL,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    tokens_used INTEGER DEFAULT 0,
    cost_usd FLOAT DEFAULT 0.0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Audit events table
CREATE TABLE IF NOT EXISTS audit_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    event_type VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(255),
    action VARCHAR(32) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for intelligence tables
CREATE INDEX IF NOT EXISTS idx_research_runs_user ON research_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_research_runs_status ON research_runs(status);
CREATE INDEX IF NOT EXISTS idx_theses_user ON theses(user_id);
CREATE INDEX IF NOT EXISTS idx_theses_symbol ON theses(symbol);
CREATE INDEX IF NOT EXISTS idx_theses_status ON theses(status);
CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source);
CREATE INDEX IF NOT EXISTS idx_claims_research ON claims(research_run_id);
CREATE INDEX IF NOT EXISTS idx_claims_thesis ON claims(thesis_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_symbol ON alerts(symbol);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_agent_executions_research ON agent_executions(research_run_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
