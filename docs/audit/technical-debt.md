# Technical Debt Audit

## Classification

- **CRITICAL**: Must fix before production
- **HIGH**: Should fix soon
- **MEDIUM**: Plan to fix
- **LOW**: Nice to have

---

## CRITICAL Debt

### 1. No Persistent Storage (ALL modules)
- **Impact**: All data lost on restart
- **Scope**: Every intelligence, analytics, research, evidence module
- **Fix**: PostgreSQL for metadata, ClickHouse for analytics, Redis for cache
- **Effort**: HIGH

### 2. Mock Embeddings (core/rag/embeddings/)
- **Impact**: RAG retrieval returns semantically meaningless results
- **Fix**: Integrate real embedding model (OpenAI, Cohere, or local)
- **Effort**: MEDIUM

### 3. Zero Tools Registered (core/ai/tools/)
- **Impact**: Agent framework completely non-functional
- **Fix**: Register market data, earnings, news, SEC filing tools
- **Effort**: HIGH

### 4. Missing Provenance Module (core/evidence/provenance/)
- **Impact**: No data lineage tracking from source to output
- **Fix**: Implement provenance tracking
- **Effort**: MEDIUM

---

## HIGH Debt

### 5. Missing AI Prompts Module (core/ai/prompts/)
- **Impact**: No structured prompt templates for agents
- **Fix**: Create financial-domain prompt templates
- **Effort**: MEDIUM

### 6. Missing Model Router (core/ai/model_router/)
- **Impact**: No intelligent model selection
- **Fix**: Implement model routing based on task complexity
- **Effort**: MEDIUM

### 7. Evidence Chain Disconnected
- **Impact**: Evidence components exist but not wired together
- **Scope**: ClaimsStore, ConfidenceScorer, EvidenceGraph, AuditTrail, Verification
- **Fix**: Wire agents -> claim extraction -> confidence -> audit -> verification
- **Effort**: HIGH

### 8. Audit Trail Never Records
- **Impact**: AuditTrailStore exists but never called
- **Fix**: Wire into all research/agent execution paths
- **Effort**: MEDIUM

### 9. 4 Missing Agent Roles
- **Impact**: AgentRole defines 10 roles, only 6 implemented
- **Missing**: COMPETITOR_ANALYST, THESIS_MONITOR, DUE_DILIGENCE, RESEARCH_SYNTHESIS
- **Fix**: Implement missing agents
- **Effort**: MEDIUM

### 10. VaR Panic on NaN (Rust risk/mod.rs)
- **Impact**: Runtime crash if returns contain NaN
- **Fix**: Add NaN validation before partial_cmp
- **Effort**: LOW

### 11. Box-Muller NaN Bug (Rust scenarios/mod.rs)
- **Impact**: Monte Carlo can produce NaN/Inf
- **Fix**: Guard against u1=0 in Box-Muller
- **Effort**: LOW

### 12. Catastrophic Cancellation in Variance (Rust statistics/mod.rs)
- **Impact**: Numerical precision loss for large-mean, small-variance data
- **Fix**: Implement Welford's algorithm
- **Effort**: LOW

### 13. No PDF/HTML Parsing (core/rag/parsing/)
- **Impact**: Cannot read SEC filings, earnings calls, research reports
- **Fix**: Integrate PyPDF2/pdfplumber, BeautifulSoup
- **Effort**: MEDIUM

### 14. Path Traversal Vulnerability (core/rag/parsing/parser.py)
- **Impact**: Arbitrary file read from filesystem
- **Fix**: Validate file_path against allowed directory
- **Effort**: LOW

### 15. Default Secret Key (apps/api/config.py)
- **Impact**: JWT tokens forgeable if not changed
- **Fix**: Require explicit configuration, fail on default
- **Effort**: LOW

---

## MEDIUM Debt

### 16. Knowledge Graph O(V*E) Performance
- **Impact**: Slow for large graphs
- **Fix**: Implement adjacency list index
- **Effort**: LOW

### 17. Memory Leaks in Unbounded Lists
- **Impact**: early_warning, anomaly, company_monitoring grow unboundedly
- **Fix**: Add TTL or max-size pruning
- **Effort**: LOW

### 18. ThesisStatus Enum Duplicated
- **Location**: thesis/models.py and thesis/tracker.py
- **Fix**: Import from single source
- **Effort**: LOW

### 19. Inline __import__("uuid")
- **Location**: thesis_engine.py:41
- **Fix**: Move to top-level import
- **Effort**: LOW

### 20. Inconsistent Error Handling in Rust
- **Impact**: Some modules use Result, others use Option
- **Fix**: Standardize on Result with custom error types
- **Effort**: LOW

### 21. Hardcoded Risk-Free Rate in Backtest
- **Location**: backtest/mod.rs:157
- **Fix**: Make configurable via BacktestConfig
- **Effort**: LOW

### 22. profit_factor Returns Infinity
- **Location**: backtest/mod.rs:187
- **Fix**: Return capped value or sentinel
- **Effort**: LOW

### 23. quality_factor Clamps ROE to [0,1]
- **Location**: factors/mod.rs:66-67
- **Fix**: Allow ROE > 100% for levered firms
- **Effort**: LOW

### 24. Dead Code in sector_attribution
- **Location**: attribution/mod.rs:41
- **Fix**: Remove unused _total variable
- **Effort**: LOW

### 25. No Semantic Chunking
- **Location**: core/rag/chunking/splitter.py
- **Fix**: Split at paragraph/section boundaries
- **Effort**: MEDIUM

### 26. No Token-Aware Chunking
- **Location**: core/rag/chunking/splitter.py
- **Fix**: Split by token count, not character count
- **Effort**: MEDIUM

### 27. Naive Reranking
- **Location**: core/rag/reranking/reranker.py
- **Fix**: Integrate cross-encoder model
- **Effort**: MEDIUM

### 28. Word-Overlap Benchmark Scoring
- **Location**: core/research/benchmark/runner.py
- **Fix**: Add semantic similarity scoring
- **Effort**: MEDIUM

### 29. No Automatic Citation Generation
- **Location**: core/rag/citations/manager.py
- **Fix**: Auto-cite when RAG generates text
- **Effort**: MEDIUM

### 30. Grid Calculation Functions Incomplete
- **Location**: core/research/grid/resolver.py
- **Impact**: Only 5 of 20+ metrics have real calculations
- **Fix**: Implement remaining metric calculations
- **Effort**: MEDIUM

---

## LOW Debt

### 31. No Coroutine Type Hints
- Some async functions lack proper return type annotations
- **Effort**: LOW

### 32. Missing __all__ in Some __init__.py
- A few modules don't export via __all__
- **Effort**: LOW

### 33. No Type Stubs for Rust
- PyO3 bindings are stubs, no type information
- **Effort**: MEDIUM

### 34. Docker Compose Uses HTTP
- No TLS configuration
- **Effort**: LOW

### 35. No Security Headers
- Missing X-Frame-Options, CSP, etc.
- **Effort**: LOW

---

## Summary

| Priority | Count | Total Effort |
|---|---|---|
| CRITICAL | 4 | HIGH |
| HIGH | 11 | MEDIUM-LOW |
| MEDIUM | 15 | LOW-MEDIUM |
| LOW | 5 | LOW |
| **Total** | **35** | |

### Top 5 Quick Wins (High Impact, Low Effort)
1. Fix VaR NaN panic (1 line fix)
2. Fix Box-Muller NaN bug (2 line fix)
3. Add path validation to file parser (5 lines)
4. Remove default secret key (1 line)
5. Remove dead code in sector_attribution (1 line)

### Top 5 Strategic Fixes (High Impact, High Effort)
1. Implement persistent storage for all modules
2. Integrate real LLM calls into agents
3. Wire evidence chain together
4. Register real tools in ToolRegistry
5. Replace mock embeddings with real model
