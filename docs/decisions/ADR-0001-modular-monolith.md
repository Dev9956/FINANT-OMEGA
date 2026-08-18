# ADR-0001: Modular Monolith Architecture

## Status

Accepted

## Date

2026-08-16

## Context

FININT OMEGA requires a robust backend architecture that supports:
- Python-based AI orchestration, API, and data ingestion
- Rust-based high-performance quantitative engine
- Multiple database backends (PostgreSQL, ClickHouse, Redis)
- Future scaling without premature complexity

The team needs an architecture that:
1. Enables rapid development and iteration
2. Allows clear module boundaries
3. Supports testing at module level
4. Can evolve toward microservices if needed
5. Avoids operational overhead of distributed systems during early development

## Decision

Adopt a **modular monolith** architecture for initial development (M0–M8), with clear internal module boundaries and interfaces that permit future extraction into services.

### What This Means

- Single deployable Python application (`apps/api/`)
- Single Rust binary/library (`rust/finintel-engine/`)
- Internal modules organized under `core/`
- Module boundaries enforced by code conventions and typed interfaces
- Python-Rust interop via PyO3 bindings (future)
- Docker Compose manages infrastructure (databases, caches)
- No inter-service communication overhead during early development

### What This Does NOT Mean

- No module structure (monolith ≠ spaghetti)
- No plans for future service extraction
- No consideration of performance boundaries

## Consequences

### Positive

- **Simpler deployment** — One container to deploy for API
- **Faster iteration** — No network hops between modules
- **Easier debugging** — Single process, shared state
- **Lower operational complexity** — No service discovery, distributed tracing overhead
- **Clear evolution path** — Extract services when load/complexity demands it

### Negative

- **Deployment coupling** — All modules deploy together
- **Scaling limitations** — Cannot independently scale CPU-intensive quant from I/O-bound API
- **Shared memory** — Module boundaries are conventions, not硬 enforcement

### Mitigations

- Module interfaces are typed (Pydantic models, Rust pub traits)
- Tests exist at module boundaries
- Performance profiling identifies extraction candidates
- Docker Compose separation allows Rust engine to run as sidecar if needed

## Future Triggers for Service Extraction

Extract into separate services when:
1. A module requires independent scaling (e.g., quant engine under heavy load)
2. A module has different deployment lifecycle
3. Team grows and needs independent development
4. Latency requirements demand co-location with specific infrastructure

## Related

- See `docs/architecture/README.md` for system layer diagram
- See `IMPLEMENTATION_PLAN.md` for milestone plan
