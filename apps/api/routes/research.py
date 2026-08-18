"""FININT OMEGA — Deep Research and Agent API routes."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.ai.agents import (
    AgentConfig,
    AgentInput,
    AgentRegistry,
    AgentRole,
    CompanyAnalystAgent,
    EarningsAnalystAgent,
    IndustryAnalystAgent,
    MacroAnalystAgent,
    PortfolioRiskAnalystAgent,
    ValuationAnalystAgent,
)
from core.research.deep_research import (
    ConflictResolver,
    ResearchConfig,
    ResearchDepth,
    ResearchEvaluator,
    ResearchExecutor,
    ResearchPlanner,
    ResearchRun,
    ResearchStatus,
    ResearchSynthesizer,
    TaskGraph,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1", tags=["research", "agents"])

# In-memory store for research runs
_research_runs: dict[str, ResearchRun] = {}

# Default agent registry
_default_registry: AgentRegistry | None = None


def _get_registry() -> AgentRegistry:
    """Get or create the default agent registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = AgentRegistry()
        _default_registry.register("company_analyst", CompanyAnalystAgent)
        _default_registry.register("earnings_analyst", EarningsAnalystAgent)
        _default_registry.register("valuation_analyst", ValuationAnalystAgent)
        _default_registry.register("industry_analyst", IndustryAnalystAgent)
        _default_registry.register("macro_analyst", MacroAnalystAgent)
        _default_registry.register("portfolio_risk_analyst", PortfolioRiskAnalystAgent)
    return _default_registry


# ---- Request / Response models ----


class DeepResearchRequest(BaseModel):
    """Request to start deep research."""

    question: str = Field(description="The research question")
    depth: ResearchDepth = Field(default=ResearchDepth.STANDARD)
    max_tasks: int = Field(default=8, ge=1, le=100)
    max_sources: int = Field(default=50, ge=1, le=1000)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    budget_tokens: int = Field(default=100_000, ge=1_000, le=10_000_000)


class DeepResearchResponse(BaseModel):
    """Response for a deep research request."""

    research_id: str
    question: str
    status: str
    task_count: int
    created_at: str


class ResearchStatusResponse(BaseModel):
    """Response for research status."""

    research_id: str
    question: str
    status: str
    task_count: int
    evidence_count: int
    conflict_count: int
    has_synthesis: bool
    created_at: str
    completed_at: str | None


class ResearchTasksResponse(BaseModel):
    """Response for research tasks."""

    research_id: str
    tasks: list[dict]


class ResearchEvidenceResponse(BaseModel):
    """Response for research evidence."""

    research_id: str
    evidence: list[dict]
    total_count: int


class AgentListResponse(BaseModel):
    """Response for listing agents."""

    agents: list[dict]
    total_count: int


class AgentExecuteRequest(BaseModel):
    """Request to execute an agent."""

    question: str
    context: dict = Field(default_factory=dict)
    evidence: list[dict] = Field(default_factory=list)


class AgentExecuteResponse(BaseModel):
    """Response from agent execution."""

    agent_id: str
    role: str
    answer: str
    confidence: float
    reasoning_summary: str
    tool_calls: list[dict]
    created_at: str


# ---- Endpoints ----


@router.post("/research/deep", response_model=DeepResearchResponse)
async def start_deep_research(request: DeepResearchRequest) -> DeepResearchResponse:
    """Start a deep research run."""
    try:
        config = ResearchConfig(
            depth=request.depth,
            max_tasks=request.max_tasks,
            max_sources=request.max_sources,
            timeout_seconds=request.timeout_seconds,
            budget_tokens=request.budget_tokens,
        )

        # Plan
        planner = ResearchPlanner()
        sub_questions, tasks = planner.plan(request.question, config)

        # Create the task graph
        graph = TaskGraph(tasks)

        # Execute tasks (synchronous for simplicity)
        executor = ResearchExecutor()
        for task in tasks:
            executor.execute_task(task)

        # Detect conflicts
        resolver = ConflictResolver()
        all_evidence: list = []
        for task in tasks:
            all_evidence.extend(
                executor._execute_with_tools(task)
                if task.status.value == "completed"
                else []
            )

        conflicts = resolver.detect_conflicts(all_evidence)

        # Synthesize
        synthesizer = ResearchSynthesizer()
        run = ResearchRun(
            question=request.question,
            config=config,
            tasks=tasks,
            evidence=all_evidence,
            conflicts=conflicts,
        )
        synthesis = synthesizer.synthesize(
            run.research_id, all_evidence, conflicts, config
        )
        run.synthesis = synthesis
        run.status = ResearchStatus.COMPLETED
        run.completed_at = datetime.now(timezone.utc)

        # Store
        _research_runs[run.research_id] = run

        logger.info(
            "deep_research_started",
            research_id=run.research_id,
            task_count=len(tasks),
            question=request.question,
        )

        return DeepResearchResponse(
            research_id=run.research_id,
            question=request.question,
            status=run.status.value,
            task_count=len(tasks),
            created_at=run.created_at.isoformat(),
        )

    except Exception as e:
        logger.error("deep_research_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Research failed: {e}")


@router.get("/research/{research_id}", response_model=ResearchStatusResponse)
async def get_research_status(research_id: str) -> ResearchStatusResponse:
    """Get the status of a research run."""
    run = _research_runs.get(research_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Research {research_id} not found")

    return ResearchStatusResponse(
        research_id=run.research_id,
        question=run.question,
        status=run.status.value,
        task_count=len(run.tasks),
        evidence_count=len(run.evidence),
        conflict_count=len(run.conflicts),
        has_synthesis=run.synthesis is not None,
        created_at=run.created_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


@router.get("/research/{research_id}/tasks", response_model=ResearchTasksResponse)
async def get_research_tasks(research_id: str) -> ResearchTasksResponse:
    """Get the tasks for a research run."""
    run = _research_runs.get(research_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Research {research_id} not found")

    tasks = [t.model_dump(mode="json") for t in run.tasks]
    return ResearchTasksResponse(research_id=research_id, tasks=tasks)


@router.get("/research/{research_id}/evidence", response_model=ResearchEvidenceResponse)
async def get_research_evidence(research_id: str) -> ResearchEvidenceResponse:
    """Get the evidence for a research run."""
    run = _research_runs.get(research_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Research {research_id} not found")

    evidence = [e.model_dump(mode="json") for e in run.evidence]
    return ResearchEvidenceResponse(
        research_id=research_id,
        evidence=evidence,
        total_count=len(evidence),
    )


@router.get("/agents", response_model=AgentListResponse)
async def list_agents() -> AgentListResponse:
    """List all available agents."""
    registry = _get_registry()
    agents = [
        {
            "role": config.role.value,
            "allowed_tools": config.allowed_tools,
            "max_tokens": config.max_tokens,
            "timeout_seconds": config.timeout_seconds,
            "evidence_policy": config.evidence_policy.value,
        }
        for config in registry.list_agents()
    ]
    return AgentListResponse(agents=agents, total_count=len(agents))


@router.post("/agents/{agent_id}/execute", response_model=AgentExecuteResponse)
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
) -> AgentExecuteResponse:
    """Execute an agent on a question."""
    registry = _get_registry()

    if not registry.has_agent(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    try:
        agent = registry.get(agent_id)
        agent_input = AgentInput(
            question=request.question,
            context=request.context,
            evidence=request.evidence,
        )
        output = agent.execute(agent_input)

        return AgentExecuteResponse(
            agent_id=output.agent_id,
            role=output.role.value,
            answer=output.answer,
            confidence=output.confidence,
            reasoning_summary=output.reasoning_summary,
            tool_calls=output.tool_calls,
            created_at=output.created_at.isoformat(),
        )

    except Exception as e:
        logger.error("agent_execution_failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")
