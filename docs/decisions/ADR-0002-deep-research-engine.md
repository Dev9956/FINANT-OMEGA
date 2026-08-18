# ADR-0002: Deep Research Engine

## Status

Accepted

## Date

2026-08-16

## Context

FININT OMEGA needs a research engine that can:
1. Decompose complex financial questions into sub-questions
2. Execute research tasks in parallel with dependency management
3. Collect evidence with confidence scoring
4. Detect and resolve conflicting evidence
5. Synthesize findings with quality evaluation
6. Enforce budget and stopping limits

The engine must be deterministic (no LLM for planning), traceable (every claim linked to evidence), and composable (usable by agents and API consumers.

## Decision

Implement a **DAG-based deep research engine** with the following pipeline:

1. **Planner** — Keyword-based domain detection and sub-question generation
2. **Task Graph** — DAG with topological execution, cycle detection, dependency tracking
3. **Executor** — Parallel task execution with tool dispatch, retry, and exponential backoff
4. **Conflict Resolver** — Evidence conflict detection and confidence-based resolution
5. **Synthesizer** — Consensus/disagreement detection, confidence computation, limitation generation
6. **Evaluator** — Completeness, evidence quality, and consistency scoring
7. **Budget Controller** — Token, time, and task limits with enforcement

### Key Design Choices

- **Keyword-based planning** — Deterministic, no LLM dependency for question decomposition
- **Evidence as first-class objects** — Every claim traceable to source with confidence score
- **Conflict resolution by confidence** — Automatic resolution when confidence differs significantly; IRREDUCIBLE flag for manual review
- **Budget enforcement** — Prevents runaway research with configurable limits

## Consequences

### Positive

- **Reproducibility** — Deterministic planning produces same tasks for same question
- **Traceability** — Evidence → claim → synthesis chain is auditable
- **Scalability** — Parallel execution via ThreadPoolExecutor
- **Safety** — Budget limits prevent resource exhaustion
- **Composability** — Engine usable by API, agents, and workflows

### Negative

- **Keyword limitations** — Cannot handle ambiguous or complex question decomposition
- **Simple conflict resolution** — Confidence averaging, not Bayesian reasoning
- **No incremental synthesis** — Runs are atomic, no mid-run partial results
- **Thread-bound parallelism** — GIL limits true parallelism for CPU tasks

### Mitigations

- Future: LLM-assisted planning for complex questions
- Future: Bayesian conflict resolution
- Future: Async execution for I/O-bound tasks
- Future: ProcessPoolExecutor for CPU-bound tasks

## Related

- See `docs/architecture/deep-research.md` for detailed architecture
- See `core/research/deep_research/` for implementation
- See `apps/api/routes/research.py` for API endpoints
