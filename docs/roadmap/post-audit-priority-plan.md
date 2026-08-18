# Post-Audit Priority Plan

## Phase 1: Critical Fixes (P0) - Week 1

### 1.1 Rust Numerical Fixes
- Fix VaR NaN panic (add NaN validation before partial_cmp)
- Fix Box-Muller NaN bug (guard u1=0)
- Add NaN input validation across all risk modules
- Implement Welford's algorithm for variance

### 1.2 Security Fixes
- Fix path traversal vulnerability in file parser
- Remove default credentials, require explicit configuration
- Add basic API key authentication
- Add CORS configuration

### 1.3 Memory Fixes
- Add max-size pruning to early_warning, anomaly, company_monitoring
- Add TTL to unbounded lists

### 1.4 Evidence Chain
- Wire agents to claim extraction
- Wire claim extraction to confidence scoring
- Wire confidence scoring to audit trail

---

## Phase 2: Data Foundation (P0) - Weeks 2-3

### 2.1 Real Data Connectors
- Integrate yfinance for market data
- Integrate SEC EDGAR for filings
- Implement entity resolution with ticker mapping

### 2.2 Persistent Storage
- Implement PostgreSQL persistence for intelligence modules
- Implement ClickHouse persistence for analytics
- Add Redis caching for frequent queries

### 2.3 Point-in-Time Data
- Implement historical data snapshots
- Add publication time tracking
- Add survivorship bias handling

---

## Phase 3: AI Integration (P0) - Weeks 3-4

### 3.1 LLM Integration
- Add OpenAI/Anthropic client
- Implement prompt templates module
- Implement model router

### 3.2 Real Tools
- Register market data tool
- Register earnings tool
- Register news tool
- Register SEC filing tool

### 3.3 Agent Execution
- Wire agents to LLM calls
- Wire agents to tool execution
- Add dynamic confidence scoring

---

## Phase 4: RAG Hardening (P1) - Weeks 4-5

### 4.1 Real Embeddings
- Replace MockEmbedder with real model
- Add vector database (Chroma or pgvector)
- Implement persistent index

### 4.2 Document Parsing
- Add PDF parsing (PyPDF2/pdfplumber)
- Add HTML parsing (BeautifulSoup)
- Add table extraction

### 4.3 Retrieval Quality
- Add BM25 for keyword matching
- Add cross-encoder reranking
- Add freshness boosting

---

## Phase 5: Institutional Features (P1) - Weeks 5-6

### 5.1 Compliance
- Add MNPI detection
- Add data retention policies
- Add audit logging

### 5.2 Performance
- Add rayon for Rust parallelism
- Add connection pooling
- Add query optimization

### 5.3 Testing
- Add load testing framework
- Add chaos testing
- Add security penetration testing

---

## Success Metrics

| Metric | Current | Target |
|---|---|---|
| Institutional Readiness Score | 26/100 | 50/100 |
| Real data coverage | 0% | 50% |
| LLM integration | None | Basic |
| Authentication | None | JWT |
| Persistent storage | None | PostgreSQL + ClickHouse |
| Test coverage | 606 tests | 700+ tests |
| Security vulnerabilities | 8 HIGH | 0 HIGH |
