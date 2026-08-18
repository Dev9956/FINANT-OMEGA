"""FININT OMEGA — Async PostgreSQL connection pool with automatic table initialization."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()

_pool = None
_initialized = False


async def get_pool():
    """Get or create the asyncpg connection pool."""
    global _pool
    if _pool is not None:
        return _pool

    try:
        import asyncpg
        from apps.api.config import get_settings

        settings = get_settings()
        dsn = settings.postgres_dsn_async

        _pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=2,
            max_size=10,
            command_timeout=10,
        )
        logger.info("pg_pool_created", host=settings.postgres_host, db=settings.postgres_db)
        return _pool
    except Exception as e:
        logger.warning("pg_pool_failed", error=str(e), msg="PostgreSQL unavailable, using in-memory fallback")
        return None


async def init_db():
    """Initialize database tables on startup."""
    global _initialized
    if _initialized:
        return

    pool = await get_pool()
    if pool is None:
        return

    try:
        async with pool.acquire() as conn:
            # Enable extensions
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

            # Schema versioning
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Users
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL DEFAULT 'analyst',
                    org_id VARCHAR(128) DEFAULT 'dev-org',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Portfolio positions
            await conn.execute("""
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
                )
            """)

            # Research runs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS research_runs (
                    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
                    question TEXT NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    task_count INTEGER DEFAULT 0,
                    evidence JSONB DEFAULT '[]',
                    conflicts JSONB DEFAULT '[]',
                    synthesis JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    completed_at TIMESTAMPTZ,
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Theses
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS theses (
                    thesis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
                    symbol VARCHAR(32) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    thesis_text TEXT NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'active',
                    confidence FLOAT DEFAULT 0.5,
                    direction VARCHAR(16) DEFAULT 'long',
                    supporting_evidence JSONB DEFAULT '[]',
                    contradicting_evidence JSONB DEFAULT '[]',
                    invalidation_conditions JSONB DEFAULT '[]',
                    versions JSONB DEFAULT '[]',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Predictions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
                    entity VARCHAR(255) NOT NULL,
                    prediction_text TEXT NOT NULL,
                    target_metric VARCHAR(128),
                    target_value DOUBLE PRECISION,
                    direction VARCHAR(16),
                    confidence FLOAT DEFAULT 0.5,
                    horizon_days INTEGER DEFAULT 30,
                    assumptions JSONB DEFAULT '[]',
                    evidence JSONB DEFAULT '[]',
                    status VARCHAR(32) NOT NULL DEFAULT 'pending',
                    actual_value DOUBLE PRECISION,
                    error DOUBLE PRECISION,
                    direction_correct BOOLEAN,
                    resolved_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Digital twins
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS digital_twins (
                    twin_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
                    entity VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    snapshots JSONB DEFAULT '[]',
                    scenarios JSONB DEFAULT '[]',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Scenarios
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scenarios (
                    scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
                    title VARCHAR(255) NOT NULL,
                    description TEXT DEFAULT '',
                    status VARCHAR(32) NOT NULL DEFAULT 'active',
                    variables JSONB DEFAULT '[]',
                    change_table JSONB DEFAULT '[]',
                    affected_metrics JSONB DEFAULT '{}',
                    risk_level VARCHAR(32) DEFAULT 'medium',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'
                )
            """)

            # Memos
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    memo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
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
                )
            """)

            # Watchlist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS watchlist_items (
                    item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(255) DEFAULT 'dev-user',
                    symbol VARCHAR(32) NOT NULL,
                    notes TEXT DEFAULT '',
                    priority VARCHAR(16) DEFAULT 'medium',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Evidence graph
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_nodes (
                    node_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    label TEXT NOT NULL,
                    node_type VARCHAR(64) NOT NULL,
                    confidence FLOAT DEFAULT 0.5,
                    source TEXT DEFAULT '',
                    data JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_edges (
                    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_node_id UUID NOT NULL REFERENCES evidence_nodes(node_id) ON DELETE CASCADE,
                    target_node_id UUID NOT NULL REFERENCES evidence_nodes(node_id) ON DELETE CASCADE,
                    relationship VARCHAR(64) NOT NULL,
                    weight FLOAT DEFAULT 1.0,
                    data JSONB DEFAULT '{}',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_user ON portfolio_positions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_symbol ON portfolio_positions(symbol)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_research_user ON research_runs(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_theses_user ON theses(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_theses_symbol ON theses(symbol)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_predictions_entity ON predictions(entity)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_twins_user ON digital_twins(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_twins_entity ON digital_twins(entity)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_user ON scenarios(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_memos_user ON memos(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist_items(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_edges_source ON evidence_edges(source_node_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_edges_target ON evidence_edges(target_node_id)")

            # Seed default test user
            from core.auth.security import hash_password
            existing = await conn.fetchrow("SELECT user_id FROM users WHERE email = $1", "test@finint.dev")
            if not existing:
                await conn.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES ($1, $2, $3)",
                    "test@finint.dev",
                    hash_password("test123"),
                    "admin",
                )
                logger.info("pg_seeded_default_user")

        _initialized = True
        logger.info("pg_tables_initialized")

    except Exception as e:
        logger.error("pg_init_failed", error=str(e))
        _initialized = True


async def close_db():
    """Close the connection pool on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("pg_pool_closed")


def is_pg_available() -> bool:
    """Check if PostgreSQL pool is available."""
    return _pool is not None


def _row_to_dict(row) -> dict:
    """Convert asyncpg Record to dict, serializing special types."""
    if row is None:
        return {}
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, uuid.UUID):
            d[k] = str(v)
        elif isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def _rows_to_dicts(rows) -> list[dict]:
    """Convert list of asyncpg Records to list of dicts."""
    return [_row_to_dict(r) for r in rows]
