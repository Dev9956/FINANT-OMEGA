# ADR-0003: Workflow Agent Framework

## Status

Accepted

## Date

2026-08-16

## Context

FININT OMEGA needs a framework for deploying specialized financial analysis agents that:
1. Have typed input/output contracts
2. Are registered in a central registry for discovery
3. Have configurable tool access (allowlisted tools only)
4. Have configurable evidence policies
5. Can be composed into multi-agent workflows

The framework must be simple, extensible, and enforce security (no arbitrary tool access).

## Decision

Implement a **role-based agent framework** with:

1. **BaseAgent ABC** — Abstract class defining `execute(input) → output` contract
2. **AgentRole enum** — Type-safe role definitions (company_analyst, earnings_analyst, valuation_analyst, industry_analyst, macro_analyst, portfolio_risk_analyst)
3. **AgentRegistry** — Central registration with caching and lifecycle management
4. **AgentConfig** — Role, allowed_tools, max_tokens, timeout, evidence_policy
5. **EvidencePolicy** — STRICT/MODERATE/LENIENT for evidence requirements

### Available Agents

| Agent | Role | Tools |
|-------|------|-------|
| CompanyAnalystAgent | company_analyst | market_data, fundamentals, news, filings |
| EarningsAnalystAgent | earnings_analyst | earnings_data, estimates, news |
| ValuationAnalystAgent | valuation_analyst | fundamentals, comparables, dcf |
| IndustryAnalystAgent | industry_analyst | sector_data, comparables, news |
| MacroAnalystAgent | macro_analyst | macro_data, rates, indicators |
| PortfolioRiskAnalystAgent | portfolio_risk_analyst | risk_analyzer, portfolio, var |

## Consequences

### Positive

- **Type safety** — Pydantic models validate all inputs/outputs
- **Security** — Tool allowlists prevent unauthorized tool access
- **Discoverability** — Registry enables dynamic agent listing and creation
- **Extensibility** — New agents implement BaseAgent and register
- **Testability** — Each agent testable in isolation

### Negative

- **Stateless** — No memory between executions
- **Synchronous** — No async tool execution
- **No inter-agent communication** — Chaining handled at API level
- **Evidence policies advisory** — Not enforced at framework level

### Mitigations

- Future: Add agent memory/context persistence
- Future: Async tool execution support
- Future: Agent composition DSL
- Future: Enforced evidence policies in BaseAgent

## Related

- See `docs/architecture/agent-framework.md` for detailed architecture
- See `core/ai/agents/` for implementation
- See `apps/api/routes/research.py` for API endpoints
