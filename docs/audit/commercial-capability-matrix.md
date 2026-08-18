# Commercial Capability Matrix

## Classification System

- **MUST HAVE**: Required for institutional-grade platform
- **IMPORTANT**: Significant competitive requirement
- **DIFFERENTIATOR**: Unique capability that sets platform apart
- **FUTURE**: Planned for later phases
- **NOT FEASIBLE**: License-restricted or proprietary

---

## A. Market Data

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Real-time equity prices | Bloomberg/LSEG/FactSet | Mock only | MISSING | No real data connector | MUST HAVE |
| Historical OHLCV | Bloomberg/LSEG/FactSet | Schema exists, no data | PARTIAL | Need real connector | MUST HAVE |
| Fixed income pricing | Bloomberg/LSEG | Not implemented | MISSING | Architecture supports it | IMPORTANT |
| FX rates | Bloomberg/LSEG | Not implemented | MISSING | Architecture supports it | IMPORTANT |
| Commodities | Bloomberg/LSEG | Not implemented | MISSING | Architecture supports it | IMPORTANT |
| Crypto | Bloomberg/Koyfin | Not implemented | MISSING | Architecture supports it | FUTURE |
| Indices | Bloomberg/LSEG/FactSet | Not implemented | MISSING | Architecture supports it | MUST HAVE |
| ETF data | Koyfin/FactSet | Not implemented | MISSING | Architecture supports it | IMPORTANT |

## B. Fundamental Data

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Financial statements | All platforms | Schema only | PARTIAL | No real data | MUST HAVE |
| Ratios/calculations | All platforms | Some ratios in grid | PARTIAL | Need 50+ standard ratios | MUST HAVE |
| Peer comparison | Bloomberg/LSEG | Cross-entity module | REAL | In-memory only | IMPORTANT |
| Industry classification | Bloomberg/LSEG | Basic sector mapping | PARTIAL | Need GICS/NAICS | IMPORTANT |
| Company profiles | All platforms | Not implemented | MISSING | Need entity master | MUST HAVE |

## C. Estimates

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Consensus estimates | Bloomberg/LSEG/FactSet | Estimates engine | REAL | No real data source | MUST HAVE |
| Earnings surprises | Bloomberg/LSEG/FactSet | Surprise calculation | REAL | In-memory only | MUST HAVE |
| Estimate revisions | Bloomberg/LSEG/FactSet | Revision tracking | REAL | In-memory only | IMPORTANT |
| Guidance tracking | AlphaSense | Not implemented | MISSING | Need earnings call parsing | IMPORTANT |
| Historical estimates | FactSet (point-in-time) | Not implemented | MISSING | Critical for temporal correctness | MUST HAVE |

## D. Corporate Actions

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Splits/dividends | All platforms | Corporate actions engine | REAL | No real data | MUST HAVE |
| M&A tracking | Bloomberg/LSEG/FactSet | M&A intelligence | REAL | No real data | IMPORTANT |
| Spin-offs/demerger | Bloomberg | Not implemented | MISSING | Architecture supports it | IMPORTANT |
| Delisting support | Bloomberg | Not implemented | MISSING | Need handling | MUST HAVE |

## E. News & Research

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| News ingestion | Bloomberg/LSEG/AlphaSense | Not implemented | MISSING | Need news API | IMPORTANT |
| Sell-side research | Bloomberg/LSEG/FactSet | Not implemented | MISSING | Need 800+ providers | IMPORTANT |
| Expert transcripts | AlphaSense (280K+) | Not implemented | MISSING | Not feasible to replicate | NOT FEASIBLE |
| Earnings transcripts | Bloomberg/LSEG/AlphaSense | Not implemented | MISSING | Need transcript API | IMPORTANT |
| SEC filings | Bloomberg/LSEG/AlphaSense | Not implemented | MISSING | Need EDGAR connector | MUST HAVE |

## F. AI Research

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Conversational AI | Bloomberg ASKB/LSEG AI Search/AlphaSense | Planner (keyword only) | PARTIAL | No LLM integration | MUST HAVE |
| Deep research | LSEG/AlphaSense | Deep research engine | REAL | No LLM calls, template-only | MUST HAVE |
| Multi-agent research | Bloomberg/AlphaSense | Agent framework (stubs) | STUB | No real execution | MUST HAVE |
| Workflow automation | Bloomberg/AlphaSense | Scheduled research | REAL | In-memory only | IMPORTANT |
| Source attribution | Bloomberg/LSEG/AlphaSense | Evidence graph | REAL | Not wired to execution | IMPORTANT |
| Research memory | AlphaSense | Memory store | REAL | Basic substring search | IMPORTANT |

## G. Portfolio Analytics

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Performance measurement | Bloomberg PORT/FactSet | Portfolio analyzer | REAL | No real data | MUST HAVE |
| Attribution | Bloomberg PORT/FactSet (10+ models) | Brinson + factor attribution | REAL | Basic implementation | IMPORTANT |
| Risk analytics | Bloomberg PORT/FactSet | VaR, CVaR, Sortino | REAL | Numerical issues | MUST HAVE |
| Factor exposure | FactSet (120+ models) | Fama-French factors | REAL | Basic implementation | IMPORTANT |
| Scenario analysis | Bloomberg PORT/FactSet | Scenario engine | REAL | No real data | IMPORTANT |
| Stress testing | FactSet | Monte Carlo | REAL | NaN bugs in Rust | IMPORTANT |

## H. Quantitative Research

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Backtesting | FactSet FPE | Backtest engine | REAL | No real data, hardcoded params | IMPORTANT |
| Factor construction | FactSet QFL | 6 factors implemented | REAL | Basic implementation | IMPORTANT |
| Signal research | FactSet Signal Selector | Not implemented | MISSING | Need ML framework | FUTURE |
| Optimization | FactSet FPO (4 optimizers) | Not implemented | MISSING | Need optimizer | IMPORTANT |
| Point-in-time data | FactSet | Not implemented | MISSING | Critical for bias elimination | MUST HAVE |

## I. Screening

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Fundamental screening | Koyfin (5,900+ filters) | Screening module | PARTIAL | Few metrics, no real data | IMPORTANT |
| Technical screening | Koyfin/FactSet | Indicators exist in Rust | PARTIAL | No screening integration | IMPORTANT |
| Factor screening | FactSet | Factors exist in Rust | PARTIAL | No screening integration | IMPORTANT |
| Custom calculated fields | Koyfin | Grid system | PARTIAL | Limited calculation functions | IMPORTANT |

## J. Security & Governance

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Authentication | All platforms | None | MISSING | No auth middleware | MUST HAVE |
| Authorization | All platforms | None | MISSING | No role-based access | MUST HAVE |
| Audit trail | Bloomberg/LSEG | Audit trail module | REAL | Never records events | MUST HAVE |
| Data lineage | Bloomberg/LSEG | Data lineage schema | PARTIAL | No real tracking | IMPORTANT |
| Tenant isolation | All platforms | Private RAG has basic | PARTIAL | Header-based, not validated | MUST HAVE |
| Rate limiting | All platforms | None | MISSING | Need API throttling | IMPORTANT |
| Input validation | All platforms | Guardrails checker | REAL | Minimal rules | IMPORTANT |

## K. Reproducibility

| Capability | Commercial | FININT OMEGA | Status | Gap | Priority |
|---|---|---|---|---|---|
| Research versioning | LSEG Deep Research | Not implemented | MISSING | Need research ID tracking | IMPORTANT |
| Data versioning | FactSet | Data lineage schema | PARTIAL | No actual versioning | IMPORTANT |
| Prompt versioning | LSEG | Not implemented | MISSING | Need prompt templates | IMPORTANT |
| Execution audit | LSEG | Audit trail module | REAL | Not wired | IMPORTANT |

---

## Summary by Priority

### MUST HAVE (15 items)
1. Real market data connector
2. Real fundamental data connector
3. SEC filings connector
4. LLM integration for agents
5. Real embedding model + vector DB
6. API authentication
7. Point-in-time data
8. Delisting handling
9. Historical estimates
10. Financial statements
11. Consensus estimates
12. Earnings surprises
13. Company profiles
14. Risk analytics (VaR/CVaR)
15. Performance measurement

### IMPORTANT (18 items)
1. News ingestion
2. Earnings transcripts
3. Estimate revisions
4. Industry classification (GICS)
5. Guidance tracking
6. Sell-side research
7. Workflow automation
8. Source attribution wiring
9. Research memory improvement
10. Attribution models
11. Factor exposure
12. Scenario analysis
13. Backtesting with real data
14. Factor construction
15. Fundamental screening
16. Technical screening
17. Data lineage
18. Rate limiting

### DIFFERENTIATOR (5 items)
1. Evidence graph (already implemented)
2. Contradiction hunter (already implemented)
3. Investment thesis engine (already implemented)
4. AI debate engine (already implemented)
5. Information decay engine (already implemented)

### FUTURE (3 items)
1. Crypto data
2. Signal research / ML framework
3. Mobile access

### NOT FEASIBLE (1 item)
1. Expert transcript library (280K+ calls - AlphaSense proprietary)
