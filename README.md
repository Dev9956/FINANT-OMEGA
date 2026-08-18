# FININT OMEGA

**Financial Intelligence & Quantitative Research Engine**

An evidence-grounded AI financial intelligence, quantitative research, portfolio analytics and investment research platform.

## Architecture

- **Python/FastAPI** — API layer, AI orchestration, data ingestion, RAG
- **Rust** — High-performance quantitative engine (returns, statistics, portfolio, risk)
- **PostgreSQL** — Metadata, research state, configuration
- **ClickHouse** — Large-scale analytics, time-series data
- **Redis** — Caching, queues, job coordination
- **Docker Compose** — Containerized infrastructure

## Quick Start

### Prerequisites

- Python 3.12+
- Rust 1.75+
- Docker & Docker Compose
- uv (recommended) or pip

### Development (Docker)

```bash
# Start all services
docker compose up -d --build

# Check health
curl http://localhost:8000/api/v1/system/health

# View logs
docker compose logs -f api
```

### Development (Local)

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Start databases via Docker
docker compose up -d postgres clickhouse redis

# Start API
python -m uvicorn apps.api.main:app --reload --port 8000
```

## Testing

```bash
# Run all tests
make test

# Python tests only
make test-python

# Rust tests only
make test-rust
```

## Project Structure

```
finintel-omega/
├── apps/api/          # FastAPI application
├── apps/worker/       # Background workers (future)
├── core/              # Business modules
│   ├── ai/            # AI orchestration
│   ├── data/          # Data connectors & quality
│   ├── rag/           # Retrieval-augmented generation
│   ├── analytics/     # Financial analytics
│   ├── intelligence/  # Events, thesis, knowledge graph
│   ├── evidence/      # Claim verification
│   └── research/      # Research workflows
├── rust/finintel-engine/  # Rust quantitative engine
├── db/                # Migrations & init scripts
├── data/              # Data lake (Parquet)
├── docs/              # Architecture & research docs
├── tests/             # Test suites
├── docker/            # Dockerfiles
└── scripts/           # Utility scripts
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/docs` | OpenAPI documentation |
| GET | `/api/v1/system/health` | Health check (API + databases) |

## Development Roadmap

| Milestone | Name | Status |
|-----------|------|--------|
| M0 | Foundation | ✅ Current |
| M1 | Data Infrastructure | Pending |
| M2 | Market + Fundamentals | Pending |
| M3 | Rust Quantitative Engine | Pending |
| M4 | Backtesting + Simulation | Pending |
| M5 | Document Intelligence | Pending |
| M6 | Hybrid RAG | Pending |
| M7 | NL Query Planner | Pending |
| M8 | Evidence + Verification | Pending |
| M9 | News + Earnings Intelligence | Pending |
| M10 | Portfolio + Risk + Factors | Pending |
| M11 | Scenario + Why-Moved + What-Changed | Pending |
| M12 | Research Memory + Thesis + KG | Pending |
| M13 | Alerts + Scheduled Research | Pending |
| M14 | FinResearchBench | Pending |
| M15 | Performance + Security | Pending |
| M16 | Dashboard | Pending |

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

**Never commit `.env` or any secrets.**

## License

Private — All rights reserved.
