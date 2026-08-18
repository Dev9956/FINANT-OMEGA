# FININT OMEGA

**Financial Intelligence & Quantitative Research Engine**

An evidence-grounded AI financial intelligence, quantitative research, portfolio analytics and investment research platform with 133+ API endpoints, 13 integrated intelligence panels, and a Rust-powered quant engine.

## Architecture

- **Python/FastAPI** — API layer, AI orchestration, data ingestion, RAG (35+ route modules)
- **React + TypeScript + Vite** — Terminal-style frontend with 45+ interfaces
- **Rust** — High-performance quantitative engine (64 tests passing)
- **PostgreSQL** — Metadata, research state, configuration
- **ClickHouse** — Large-scale analytics, time-series data
- **Redis** — Caching, queues, job coordination
- **Docker Compose** — Containerized infrastructure

## Quick Start

### Prerequisites

- Python 3.12+
- Rust 1.75+
- Node.js 18+
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

# Start frontend
cd terminal
npm install
npm run dev
```

## Features

### Intelligence Modules

| Module | Description |
|--------|-------------|
| AI Chat | Conversational research with evidence-grounded answers |
| Deep Research | 10-stage research pipeline with task graph orchestration |
| Evidence Graph | Knowledge graph with nodes, edges, and confidence scoring |
| Thesis Engine | Create, track, and evaluate investment theses |
| Cross-Entity | Multi-entity relationship analysis, weakening patterns, cashflow |
| Predictions | Forecast creation with calibration and Brier score tracking |
| Digital Twin | Company simulation engine with scenario modeling |
| Quality Scoring | 8-dimension evidence quality evaluation |
| Investment Memo | Auto-generated memos with markdown export |
| Portfolio | CRUD positions with live market price refresh |
| Risk Analytics | Volatility, Sharpe ratio, max drawdown, VaR, anomaly detection |
| Scenario Analysis | Create scenarios with variable definitions and change tables |
| Bull/Bear Debate | AI-powered argumentation with bull, bear, and base cases |
| News & Alerts | Real-time monitoring alerts with early warning scan |
| Integration Control | 9 providers, health checks, secrets, model routing |

### Backend Highlights

- **133 API paths** across 35+ route modules
- **JWT authentication** with RBAC (4 roles, 15 permissions)
- **Evidence-first design** — deterministic calculations precede LLM explanation
- **Integration Control Plane** — OpenAI, Ollama, Anthropic, yfinance, SEC EDGAR, FRED, PostgreSQL, ClickHouse, Redis
- **Research engine** with task graph, conflict resolution, evaluation, synthesis, stopping criteria, budget management

### Frontend Highlights

- **Terminal-style UI** with dark theme and 20+ color palette
- **Workspace grid system** with draggable, resizable panels
- **Command palette** (Ctrl+K) with 20+ quick actions
- **Sidebar navigation** with 8 workspace categories
- **Real-time data** — all 13 panels wired to live backend APIs

## Project Structure

```
FININT OMEGA/
├── apps/
│   ├── api/               # FastAPI application (35+ route modules)
│   └── worker/            # Background workers
├── core/                  # Business modules
│   ├── ai/                # AI orchestration (agents, LLM providers, guardrails)
│   ├── analytics/         # Financial analytics (risk, portfolio, factors, scenarios)
│   ├── auth/              # JWT auth, RBAC, security
│   ├── data/              # Data connectors, quality, lineage, validation
│   ├── evidence/          # Claim verification, confidence scoring, audit
│   ├── integrations/      # Integration control plane (9 providers)
│   ├── intelligence/      # 15+ intelligence engines
│   ├── persistence/       # Database writers, thesis repository
│   ├── rag/               # Retrieval-augmented generation
│   ├── research/          # Research workflows, grid, scheduled, watchlist
│   └── storage/           # Storage abstraction
├── rust/finintel-engine/  # Rust quantitative engine
│   └── src/               # Returns, statistics, portfolio, risk, scenarios, backtest
├── terminal/              # React + TypeScript frontend
│   └── src/
│       ├── api/           # API client (40+ endpoints)
│       ├── components/    # 20+ panel components
│       ├── store/         # Zustand workspace state
│       └── types/         # 45+ TypeScript interfaces
├── tests/
│   ├── unit/              # 817+ Python unit tests
│   ├── integration/       # API integration tests
│   └── live/              # Live verification tests
├── db/
│   ├── clickhouse/        # ClickHouse schemas
│   └── migrations/        # PostgreSQL migrations
├── docs/                  # Architecture, audit, intelligence documentation
└── docker/                # Dockerfiles
```

## Testing

```bash
# Run all tests
make test

# Python tests only (817+)
make test-python

# Rust tests only (64)
make test-rust

# Live verification (69/69 endpoints)
python tests/live/comprehensive_verification.py
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

Key environment variables:

```env
DATABASE_URL=postgresql://...
CLICKHOUSE_URL=http://...
REDIS_URL=redis://...
OPENAI_API_KEY=sk-...          # Optional — enables real LLM synthesis
```

**Never commit `.env` or any secrets.**

## Credentials

Default test credentials:
- Email: `test@finint.dev`
- Password: `test123`

## License

Private — All rights reserved.
