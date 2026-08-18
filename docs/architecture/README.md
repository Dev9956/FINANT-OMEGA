# FININT OMEGA — Architecture

## Design Principles

1. **Modular Monolith** — Single deployable unit with clear internal module boundaries. Microservices only when justified.
2. **Evidence-First** — Every financial claim is traceable to a source with provenance.
3. **Deterministic Quant** — LLM is the reasoning layer; numerical truth comes from typed tools and Rust engine.
4. **Data Quality Pipeline** — Raw → Bronze → Silver → Gold with explicit lineage.
5. **Security by Default** — No secrets in code, no arbitrary LLM tool access, typed allowlisted tools only.

## System Layers

```
┌─────────────────────────────────────────┐
│              API Layer (FastAPI)         │
│  Routes / Schemas / Auth / Rate Limits  │
├─────────────────────────────────────────┤
│           AI Orchestration              │
│  Planner / Agents / Tools / Guardrails  │
├─────────────────────────────────────────┤
│         Core Business Modules           │
│  Data / RAG / Analytics / Intelligence  │
│  Evidence / Research                    │
├─────────────────────────────────────────┤
│         Quantitative Engine (Rust)      │
│  Returns / Stats / Portfolio / Risk     │
├─────────────────────────────────────────┤
│            Data Layer                   │
│  PostgreSQL / ClickHouse / Redis        │
│  Parquet / Arrow / Object Storage       │
├─────────────────────────────────────────┤
│         Infrastructure                  │
│  Docker Compose / Migrations / Logging  │
└─────────────────────────────────────────┘
```

## Data Flow

```
External Data Sources
       │
       ▼
  Raw (ingested, immutable)
       │
       ▼
  Bronze (validated, typed)
       │
       ▼
  Silver (cleaned, joined, corporate actions handled)
       │
       ▼
  Gold (analytics-ready, pre-aggregated)
       │
       ▼
  Analytics / API / AI
```

## Module Boundaries

Each module in `core/` has:
- Typed interfaces (Pydantic models / Rust structs)
- Internal implementation hidden behind module API
- Tests scoped to module
- Data lineage where applicable

## Security Model

- Environment-based configuration (never hardcoded)
- Docker secrets pattern
- API key management via environment
- LLM tools are typed and allowlisted
- No arbitrary SQL/shell from LLM
- Prompt injection defenses on document ingestion
