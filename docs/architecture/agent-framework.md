# Workflow Agent Framework — Architecture

## Overview

The Agent Framework provides typed, role-based research agents with configurable tool access, evidence policies, and a central registry. Each agent specializes in a financial analysis domain and executes via a standardized input/output contract.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  API Layer                           │
│  GET /agents    POST /agents/{id}/execute           │
├─────────────────────────────────────────────────────┤
│               Agent Registry                        │
│  register · get · list · create_agent               │
├─────────────────────────────────────────────────────┤
│              BaseAgent (ABC)                         │
│  execute(input) → output                            │
│  validate_input · build_output                      │
├──────────┬──────────┬──────────┬────────────────────┤
│ Company  │Earnings  │Valuation │Industry  │ Macro   │
│ Analyst  │ Analyst  │ Analyst  │ Analyst  │ Analyst │
├──────────┴──────────┴──────────┴────────────────────┤
│           Tool Access Control                        │
│  allowed_tools per agent config                     │
├─────────────────────────────────────────────────────┤
│           Evidence Policies                          │
│  strict · moderate · lenient                         │
└─────────────────────────────────────────────────────┘
```

## Key Components

### BaseAgent (`core/ai/agents/base.py`)

Abstract base class defining the agent contract:

```python
class BaseAgent(ABC):
    @abstractmethod
    def default_role(self) -> AgentRole: ...

    @abstractmethod
    def execute(self, input_data: AgentInput) -> AgentOutput: ...

    def _validate_input(self, input_data: AgentInput) -> None: ...
    def _build_output(self, input_data, answer, confidence, reasoning, tool_calls) -> AgentOutput: ...
```

### AgentRegistry (`core/ai/agents/registry.py`)

- **`register(agent_id, agent_class, config)`** — Register agent class with type validation
- **`get(agent_id)`** — Returns cached or new instance
- **`list_agents()`** — Returns all `AgentConfig` objects
- **`create_agent(role)`** — Creates agent by `AgentRole` enum
- **`has_agent(agent_id)`** — Existence check

### AgentConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `role` | `AgentRole` | required | Agent's specialization |
| `allowed_tools` | `list[str]` | `[]` | Tools the agent may use |
| `max_tokens` | `int` | 4096 | Max output tokens |
| `timeout_seconds` | `int` | 120 | Execution timeout |
| `retry_count` | `int` | 3 | Retry attempts |
| `evidence_policy` | `EvidencePolicy` | MODERATE | How strictly to require evidence |

### AgentInput / AgentOutput

```python
class AgentInput(BaseModel):
    research_id: str
    question: str
    context: dict[str, Any]      # e.g. {"symbol": "AAPL"}
    evidence: list[dict]          # Pre-collected evidence items

class AgentOutput(BaseModel):
    agent_id: str
    role: AgentRole
    answer: str
    evidence_ids: list[str]
    confidence: float             # 0.0–1.0
    reasoning_summary: str
    tool_calls: list[dict]
```

## Available Agents

| Agent | Role | Tools | Description |
|-------|------|-------|-------------|
| `CompanyAnalystAgent` | company_analyst | market_data, fundamentals, news, filings | Company fundamentals and market analysis |
| `EarningsAnalystAgent` | earnings_analyst | earnings_data, estimates, news | Earnings analysis and estimate tracking |
| `ValuationAnalystAgent` | valuation_analyst | fundamentals, comparables, dcf | Valuation analysis |
| `IndustryAnalystAgent` | industry_analyst | sector_data, comparables, news | Industry/sector analysis |
| `MacroAnalystAgent` | macro_analyst | macro_data, rates, indicators | Macroeconomic analysis |
| `PortfolioRiskAnalystAgent` | portfolio_risk_analyst | risk_analyzer, portfolio, var | Portfolio risk analysis |

## Tool Access Control

Each agent declares `allowed_tools` in its config. The registry enforces that agents only invoke tools in their allowlist. Tools are registered via `ToolRegistry` (`core/ai/tools/registry.py`) with typed parameter definitions:

```python
class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: list[ParameterDef]  # name, type, required, default
    tags: list[str]
    enabled: bool
```

## Evidence Policies

| Policy | Behavior |
|--------|----------|
| `STRICT` | Requires evidence for every claim; rejects unsupported outputs |
| `MODERATE` | Prefers evidence but allows confident assertions without it |
| `LENIENT` | Accepts assertions with minimal evidence requirements |

## Data Flow

```
Request: POST /agents/{id}/execute
  │
  ▼
AgentRegistry.get(agent_id)
  → BaseAgent instance
  │
  ▼
agent.execute(AgentInput)
  │
  ├─ _validate_input() → raises on empty question
  │
  ├─ Tool dispatch (per allowed_tools)
  │   → ToolRegistry.execute(name, **kwargs)
  │
  ├─ Evidence collection
  │   → filter by evidence_policy
  │
  └─ _build_output() → AgentOutput
```

## Design Decisions

1. **Typed interfaces** — Pydantic models for all inputs/outputs ensure validation at boundaries
2. **Registry pattern** — Central registration enables discovery, configuration, and lifecycle management
3. **Role-based access** — `AgentRole` enum constrains agent capabilities at the type level
4. **Evidence policies** — Configurable strictness allows different agents to have different evidence requirements
5. **Cached instances** — Registry caches agent instances for stateful agents

## Known Limitations

- Agents are stateless between executions (no memory of prior runs)
- Tool dispatch is synchronous; no async tool execution
- No inter-agent communication or chaining (orchestrated at API level)
- Evidence policies are advisory, not enforced at the framework level
- No built-in agent composition (multi-agent workflows)
