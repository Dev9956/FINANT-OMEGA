"""FININT OMEGA — Unit tests for Deep Research Engine."""

import pytest

from core.research.deep_research.conflict_resolution import ConflictResolver
from core.research.deep_research.evaluation import ResearchEvaluator
from core.research.deep_research.executor import ResearchExecutor
from core.research.deep_research.models import (
    ConflictItem,
    ConflictStatus,
    EvidenceItem,
    ResearchConfig,
    ResearchDepth,
    ResearchRun,
    ResearchTask,
    ResearchStatus,
    TaskStatus,
)
from core.research.deep_research.planner import ResearchPlanner
from core.research.deep_research.research_budget import BudgetExceeded, ResearchBudget
from core.research.deep_research.stopping import StoppingCriteria, StoppingState
from core.research.deep_research.synthesis import ResearchSynthesizer
from core.research.deep_research.task_graph import CircularDependencyError, TaskGraph


# ---- ResearchPlanner ----


class TestResearchPlanner:
    def test_analyze_question_generates_sub_questions(self):
        planner = ResearchPlanner()
        sub_qs = planner.analyze_question("Analyze TCS earnings and valuation")
        assert len(sub_qs) > 0
        assert any("TCS" in sq for sq in sub_qs)

    def test_analyze_question_empty_raises(self):
        planner = ResearchPlanner()
        with pytest.raises(ValueError):
            planner.analyze_question("")

    def test_create_task_graph_respects_max_tasks(self):
        planner = ResearchPlanner()
        config = ResearchConfig(max_tasks=3)
        sub_qs = ["q1", "q2", "q3", "q4", "q5", "q6"]
        tasks = planner.create_task_graph(sub_qs, config)
        assert len(tasks) <= 3

    def test_plan_returns_both_sub_questions_and_tasks(self):
        planner = ResearchPlanner()
        sub_qs, tasks = planner.plan("Analyze RELIANCE")
        assert len(sub_qs) > 0
        assert len(tasks) > 0
        assert all(isinstance(t, ResearchTask) for t in tasks)

    def test_shallow_depth_fewer_tasks(self):
        planner = ResearchPlanner()
        shallow_config = ResearchConfig.for_depth(ResearchDepth.SHALLOW)
        deep_config = ResearchConfig.for_depth(ResearchDepth.DEEP)
        _, shallow_tasks = planner.plan("Analyze TCS", shallow_config)
        _, deep_tasks = planner.plan("Analyze TCS", deep_config)
        assert shallow_config.max_tasks <= deep_config.max_tasks


# ---- TaskGraph ----


class TestTaskGraph:
    def test_topological_sort_returns_valid_order(self):
        t1 = ResearchTask(task_id="t1", question="q1")
        t2 = ResearchTask(task_id="t2", question="q2", dependencies=["t1"])
        t3 = ResearchTask(task_id="t3", question="q3", dependencies=["t2"])
        graph = TaskGraph([t1, t2, t3])
        order = graph.topological_sort()
        ids = [t.task_id for t in order]
        assert ids.index("t1") < ids.index("t2") < ids.index("t3")

    def test_circular_dependency_raises(self):
        t1 = ResearchTask(task_id="t1", question="q1", dependencies=["t2"])
        t2 = ResearchTask(task_id="t2", question="q2", dependencies=["t1"])
        with pytest.raises(CircularDependencyError):
            TaskGraph([t1, t2])

    def test_ready_tasks_returns_independent_tasks(self):
        t1 = ResearchTask(task_id="t1", question="q1")
        t2 = ResearchTask(task_id="t2", question="q2", dependencies=["t1"])
        graph = TaskGraph([t1, t2])
        ready = graph.ready_tasks()
        assert len(ready) == 1
        assert ready[0].task_id == "t1"

    def test_complete_task_marks_done(self):
        t1 = ResearchTask(task_id="t1", question="q1")
        graph = TaskGraph([t1])
        graph.complete_task("t1", result="done")
        task = graph.get_task("t1")
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "done"

    def test_is_complete(self):
        t1 = ResearchTask(task_id="t1", question="q1")
        graph = TaskGraph([t1])
        assert not graph.is_complete()
        graph.complete_task("t1")
        assert graph.is_complete()

    def test_fail_task(self):
        t1 = ResearchTask(task_id="t1", question="q1")
        graph = TaskGraph([t1])
        graph.fail_task("t1", "error occurred")
        task = graph.get_task("t1")
        assert task is not None
        assert task.status == TaskStatus.FAILED

    def test_nonexistent_task_raises(self):
        graph = TaskGraph([])
        with pytest.raises(KeyError):
            graph.complete_task("nonexistent")


# ---- ResearchBudget ----


class TestResearchBudget:
    def test_record_tokens(self):
        config = ResearchConfig(budget_tokens=1000)
        budget = ResearchBudget(config)
        budget.record_tokens(500)
        assert budget.tokens_used == 500

    def test_negative_tokens_raises(self):
        config = ResearchConfig()
        budget = ResearchBudget(config)
        with pytest.raises(ValueError):
            budget.record_tokens(-1)

    def test_enforce_budget_within_limits(self):
        config = ResearchConfig(budget_tokens=1000, timeout_seconds=300, max_tasks=5)
        budget = ResearchBudget(config)
        budget.record_tokens(500)
        budget.record_api_call()
        assert budget.enforce_budget() is True

    def test_enforce_budget_exceeded_tokens(self):
        config = ResearchConfig(budget_tokens=1000)
        budget = ResearchBudget(config)
        budget.record_tokens(1000)
        assert budget.enforce_budget() is False

    def test_enforce_budget_exceeded_tasks(self):
        config = ResearchConfig(max_tasks=2)
        budget = ResearchBudget(config)
        budget.record_task()
        budget.record_task()
        assert budget.enforce_budget() is False

    def test_check_and_enforce_raises(self):
        config = ResearchConfig(budget_tokens=1000)
        budget = ResearchBudget(config)
        budget.record_tokens(1000)
        with pytest.raises(BudgetExceeded):
            budget.check_and_enforce()

    def test_usage_report(self):
        config = ResearchConfig(budget_tokens=1000, timeout_seconds=300, max_tasks=5)
        budget = ResearchBudget(config)
        budget.record_tokens(200)
        budget.record_api_call()
        budget.record_task()
        report = budget.get_usage_report()
        assert report["tokens_used"] == 200
        assert report["tokens_budget"] == 1000
        assert report["api_calls"] == 1
        assert report["tasks_completed"] == 1
        assert "within_budget" in report


# ---- StoppingCriteria ----


class TestStoppingCriteria:
    def test_max_tasks_reached(self):
        config = ResearchConfig(max_tasks=2)
        criteria = StoppingCriteria(config)
        tasks = [
            ResearchTask(task_id="t1", question="q1", status=TaskStatus.COMPLETED),
            ResearchTask(task_id="t2", question="q2", status=TaskStatus.COMPLETED),
        ]
        state = StoppingState(tasks=tasks, config=config)
        assert criteria.max_tasks_reached(state) is True

    def test_all_tasks_complete(self):
        config = ResearchConfig()
        criteria = StoppingCriteria(config)
        tasks = [
            ResearchTask(task_id="t1", question="q1", status=TaskStatus.COMPLETED),
            ResearchTask(task_id="t2", question="q2", status=TaskStatus.FAILED),
        ]
        state = StoppingState(tasks=tasks, config=config)
        assert criteria.all_tasks_complete(state) is True

    def test_should_stop_on_all_tasks_complete(self):
        config = ResearchConfig()
        criteria = StoppingCriteria(config)
        tasks = [
            ResearchTask(task_id="t1", question="q1", status=TaskStatus.COMPLETED),
        ]
        state = StoppingState(tasks=tasks, config=config)
        should_stop, reason = criteria.should_stop(state)
        assert should_stop is True
        assert reason == "all_tasks_complete"

    def test_should_not_stop_when_pending(self):
        config = ResearchConfig()
        criteria = StoppingCriteria(config)
        tasks = [
            ResearchTask(task_id="t1", question="q1", status=TaskStatus.PENDING),
        ]
        state = StoppingState(tasks=tasks, config=config)
        should_stop, _ = criteria.should_stop(state)
        assert should_stop is False

    def test_no_new_evidence_convergence(self):
        config = ResearchConfig()
        criteria = StoppingCriteria(config)
        evidence = [EvidenceItem(source_type="test", source_id="s1", content="x")]
        tasks = [ResearchTask(task_id="t1", question="q1", status=TaskStatus.RUNNING)]
        # First call initializes hash, then 3 more calls with same hash to reach count >= 3
        for _ in range(4):
            state = StoppingState(tasks=tasks, evidence=evidence, config=config)
            stopped, reason = criteria.should_stop(state)
        assert stopped is True
        assert reason == "no_new_evidence"


# ---- ConflictResolver


class TestConflictResolver:
    def test_detect_conflicts(self):
        resolver = ConflictResolver()
        evidence = [
            EvidenceItem(
                source_type="test",
                source_id="s1",
                content="TCS is strong",
                supports_claim="TCS is strong",
                confidence=0.8,
            ),
            EvidenceItem(
                source_type="test",
                source_id="s2",
                content="TCS is weak",
                contradicts_claim="TCS is strong",
                confidence=0.7,
            ),
        ]
        conflicts = resolver.detect_conflicts(evidence)
        assert len(conflicts) == 1
        assert conflicts[0].resolution_status == ConflictStatus.UNRESOLVED

    def test_classify_conflict(self):
        resolver = ConflictResolver()
        assert resolver.classify_conflict(0.9) == "critical"
        assert resolver.classify_conflict(0.5, 0.2) == "moderate"
        assert resolver.classify_conflict(0.1) == "minor"

    def test_suggest_resolution(self):
        resolver = ConflictResolver()
        conflict = ConflictItem(
            claim_a="A",
            claim_b="B",
            severity=0.9,
        )
        suggestion = resolver.suggest_resolution(conflict)
        assert "Critical" in suggestion

    def test_resolve_conflict_higher_confidence_wins(self):
        resolver = ConflictResolver()
        ev_a = EvidenceItem(
            evidence_id="ea1",
            source_type="test",
            source_id="s1",
            content="A",
            confidence=0.9,
        )
        ev_b = EvidenceItem(
            evidence_id="eb1",
            source_type="test",
            source_id="s2",
            content="B",
            confidence=0.3,
        )
        conflict = ConflictItem(
            claim_a="claim1",
            claim_b="claim2",
            evidence_a_ids=["ea1"],
            evidence_b_ids=["eb1"],
            severity=0.6,
        )
        resolved = resolver.resolve_conflict(conflict, [ev_a, ev_b])
        assert resolved.resolution_status == ConflictStatus.RESOLVED
        assert "A" in resolved.resolution


# ---- ResearchSynthesizer ----


class TestResearchSynthesizer:
    def test_synthesize_empty_evidence(self):
        synthesizer = ResearchSynthesizer()
        synthesis = synthesizer.synthesize("r1", [], [])
        assert synthesis.confidence == 0.0
        assert "No evidence" in synthesis.conclusion

    def test_synthesize_with_evidence(self):
        synthesizer = ResearchSynthesizer()
        evidence = [
            EvidenceItem(
                source_type="test",
                source_id="s1",
                content="data1",
                confidence=0.8,
                supports_claim="claim1",
            ),
            EvidenceItem(
                source_type="test",
                source_id="s2",
                content="data2",
                confidence=0.7,
                supports_claim="claim1",
            ),
        ]
        synthesis = synthesizer.synthesize("r1", evidence, [])
        assert synthesis.confidence > 0
        assert len(synthesis.evidence_ids) == 2
        assert len(synthesis.methodology) > 0

    def test_synthesize_conflict_reduces_confidence(self):
        synthesizer = ResearchSynthesizer()
        evidence = [
            EvidenceItem(
                source_type="test",
                source_id="s1",
                content="data1",
                confidence=0.8,
                supports_claim="claim1",
            ),
        ]
        conflicts = [
            ConflictItem(
                claim_a="claim1",
                claim_b="claim2",
                severity=0.5,
                resolution=None,
            ),
        ]
        synthesis = synthesizer.synthesize("r1", evidence, conflicts)
        # Confidence should be penalized for unresolved conflict
        assert synthesis.confidence < 0.8


# ---- ResearchEvaluator ----


class TestResearchEvaluator:
    def test_evaluate_completeness_empty(self):
        evaluator = ResearchEvaluator()
        run = ResearchRun(question="test")
        assert evaluator.evaluate_completeness(run) == 0.0

    def test_evaluate_completeness_all_completed(self):
        evaluator = ResearchEvaluator()
        tasks = [
            ResearchTask(task_id="t1", question="q1", status=TaskStatus.COMPLETED),
            ResearchTask(task_id="t2", question="q2", status=TaskStatus.COMPLETED),
        ]
        run = ResearchRun(question="test", tasks=tasks)
        score = evaluator.evaluate_completeness(run)
        assert score > 0

    def test_evaluate_evidence_quality_empty(self):
        evaluator = ResearchEvaluator()
        assert evaluator.evaluate_evidence_quality([]) == 0.0

    def test_evaluate_consistency(self):
        evaluator = ResearchEvaluator()
        evidence = [
            EvidenceItem(source_type="test", source_id="s1", content="x"),
        ]
        run = ResearchRun(question="test", evidence=evidence)
        score = evaluator.evaluate_consistency(run)
        assert 0.0 <= score <= 1.0

    def test_get_evaluation_report(self):
        evaluator = ResearchEvaluator()
        run = ResearchRun(question="test")
        report = evaluator.get_evaluation_report(run)
        assert "overall_score" in report
        assert "completeness" in report
        assert "evidence_quality" in report
        assert "consistency" in report


# ---- AgentRegistry ----


class TestAgentRegistry:
    def test_register_and_get(self):
        from core.ai.agents.base import AgentConfig, AgentRole, BaseAgent
        from core.ai.agents.company_analyst import CompanyAnalystAgent
        from core.ai.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("company_analyst", CompanyAnalystAgent)
        agent = registry.get("company_analyst")
        assert isinstance(agent, CompanyAnalystAgent)

    def test_list_agents(self):
        from core.ai.agents.base import AgentRole
        from core.ai.agents.company_analyst import CompanyAnalystAgent
        from core.ai.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("company_analyst", CompanyAnalystAgent)
        agents = registry.list_agents()
        assert len(agents) == 1
        assert agents[0].role == AgentRole.COMPANY_ANALYST

    def test_create_agent_by_role(self):
        from core.ai.agents.base import AgentRole
        from core.ai.agents.earnings_analyst import EarningsAnalystAgent
        from core.ai.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("earnings_analyst", EarningsAnalystAgent)
        agent = registry.create_agent(AgentRole.EARNINGS_ANALYST)
        assert isinstance(agent, EarningsAnalystAgent)

    def test_get_nonexistent_raises(self):
        from core.ai.agents.registry import AgentNotFoundError, AgentRegistry

        registry = AgentRegistry()
        with pytest.raises(AgentNotFoundError):
            registry.get("nonexistent")

    def test_unregister(self):
        from core.ai.agents.company_analyst import CompanyAnalystAgent
        from core.ai.agents.registry import AgentRegistry

        registry = AgentRegistry()
        registry.register("company_analyst", CompanyAnalystAgent)
        assert registry.has_agent("company_analyst")
        registry.unregister("company_analyst")
        assert not registry.has_agent("company_analyst")


# ---- Agent Implementations ----


class TestCompanyAnalystAgent:
    def test_execute_returns_output(self):
        from core.ai.agents.base import AgentInput, AgentRole
        from core.ai.agents.company_analyst import CompanyAnalystAgent

        agent = CompanyAnalystAgent()
        result = agent.execute(
            AgentInput(
                question="Analyze TCS",
                context={"symbol": "TCS", "period": "annual"},
            )
        )
        assert result.role == AgentRole.COMPANY_ANALYST
        assert "TCS" in result.answer
        assert result.confidence > 0
        assert len(result.tool_calls) > 0

    def test_default_role(self):
        from core.ai.agents.base import AgentRole
        from core.ai.agents.company_analyst import CompanyAnalystAgent

        agent = CompanyAnalystAgent()
        assert agent.default_role() == AgentRole.COMPANY_ANALYST

    def test_empty_question_raises(self):
        from core.ai.agents.base import AgentInput
        from core.ai.agents.company_analyst import CompanyAnalystAgent

        agent = CompanyAnalystAgent()
        with pytest.raises(ValueError):
            agent.execute(AgentInput(question=""))


class TestEarningsAnalystAgent:
    def test_execute_returns_output(self):
        from core.ai.agents.base import AgentInput, AgentRole
        from core.ai.agents.earnings_analyst import EarningsAnalystAgent

        agent = EarningsAnalystAgent()
        result = agent.execute(
            AgentInput(
                question="Analyze RELIANCE earnings",
                context={"symbol": "RELIANCE", "surprise": 5.2, "momentum": "positive"},
            )
        )
        assert result.role == AgentRole.EARNINGS_ANALYST
        assert "RELIANCE" in result.answer
        assert "5.2" in result.answer

    def test_default_role(self):
        from core.ai.agents.base import AgentRole
        from core.ai.agents.earnings_analyst import EarningsAnalystAgent

        agent = EarningsAnalystAgent()
        assert agent.default_role() == AgentRole.EARNINGS_ANALYST
