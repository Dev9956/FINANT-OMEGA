"""FININT OMEGA — Benchmark runner for evaluating research quality."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class BenchmarkCase(BaseModel):
    """A single benchmark test case."""

    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    expected_answer: str = ""
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    """Result of running a benchmark case."""

    case_id: str
    query: str
    predicted: str = ""
    expected: str = ""
    score: float = 0.0
    passed: bool = False
    latency_ms: float = 0.0
    metadata: dict = Field(default_factory=dict)


class BenchmarkSummary(BaseModel):
    """Summary of a benchmark run."""

    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_cases: int = 0
    passed: int = 0
    failed: int = 0
    avg_score: float = 0.0
    avg_latency_ms: float = 0.0
    results: list[BenchmarkResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BenchmarkRunner:
    """Run benchmark cases and evaluate research quality."""

    def __init__(self) -> None:
        self._cases: list[BenchmarkCase] = []
        self._evaluators: dict[str, callable] = {}

    def add_case(self, query: str, expected_answer: str = "", category: str = "general", tags: list[str] | None = None) -> BenchmarkCase:
        case = BenchmarkCase(query=query, expected_answer=expected_answer, category=category, tags=tags or [])
        self._cases.append(case)
        return case

    def register_evaluator(self, name: str, evaluator: callable) -> None:
        self._evaluators[name] = evaluator

    def _default_score(self, predicted: str, expected: str) -> float:
        if not expected:
            return 1.0 if predicted else 0.0
        pred_words = set(predicted.lower().split())
        exp_words = set(expected.lower().split())
        if not exp_words:
            return 1.0 if not pred_words else 0.5
        overlap = len(pred_words & exp_words)
        return overlap / len(exp_words)

    def run_case(self, case: BenchmarkCase, handler: callable, evaluator_name: str | None = None) -> BenchmarkResult:
        start = datetime.now(timezone.utc)
        try:
            predicted = handler(case.query)
        except Exception as e:
            predicted = f"Error: {e}"
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000

        if evaluator_name and evaluator_name in self._evaluators:
            score = self._evaluators[evaluator_name](predicted, case.expected_answer)
        else:
            score = self._default_score(predicted, case.expected_answer)

        return BenchmarkResult(
            case_id=case.case_id,
            query=case.query,
            predicted=predicted,
            expected=case.expected_answer,
            score=score,
            passed=score >= 0.5,
            latency_ms=elapsed,
        )

    def run_all(self, handler: callable, evaluator_name: str | None = None) -> BenchmarkSummary:
        results = [self.run_case(c, handler, evaluator_name) for c in self._cases]
        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / max(len(results), 1)
        avg_latency = sum(r.latency_ms for r in results) / max(len(results), 1)
        return BenchmarkSummary(
            total_cases=len(results), passed=passed, failed=len(results) - passed,
            avg_score=avg_score, avg_latency_ms=avg_latency, results=results,
        )

    def list_cases(self) -> list[BenchmarkCase]:
        return list(self._cases)

    def filter_cases(self, category: str | None = None, tags: list[str] | None = None) -> list[BenchmarkCase]:
        cases = self._cases
        if category:
            cases = [c for c in cases if c.category == category]
        if tags:
            tag_set = set(tags)
            cases = [c for c in cases if tag_set & set(c.tags)]
        return cases
