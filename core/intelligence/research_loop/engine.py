"""FININT OMEGA — Autonomous Research Loop Engine."""

from __future__ import annotations

import time

from core.intelligence.research_loop.models import (
    LoopConfig,
    LoopPhase,
    LoopResult,
    LoopStep,
    ResearchIteration,
)


class ResearchLoopEngine:
    """Controlled autonomous research loop with budget and stopping conditions."""

    def __init__(self, config: LoopConfig | None = None) -> None:
        self._config = config or LoopConfig()
        self._results: dict[str, LoopResult] = {}

    def run(
        self,
        question: str,
        initial_data: dict | None = None,
        config: LoopConfig | None = None,
    ) -> LoopResult:
        cfg = config or self._config
        result = LoopResult(question=question)
        start_time = time.time()

        for iteration_num in range(cfg.max_iterations):
            if time.time() - start_time > cfg.timeout_seconds:
                result.status = "timeout"
                break

            iteration = self._run_iteration(question, initial_data or {}, iteration_num)
            result.iterations.append(iteration)
            result.total_steps += len(iteration.steps)

            result.final_findings.extend(iteration.findings)
            result.final_hypotheses.extend(iteration.hypotheses)

            if self._should_stop(iteration, result, cfg):
                break

        result.confidence = self._compute_final_confidence(result)
        result.status = "completed"
        result.audit_trail = self._build_audit_trail(result)

        self._results[result.loop_id] = result
        return result

    def get_result(self, loop_id: str) -> LoopResult | None:
        return self._results.get(loop_id)

    def _run_iteration(
        self,
        question: str,
        data: dict,
        iteration_num: int,
    ) -> ResearchIteration:
        iteration = ResearchIteration()
        phases = [
            LoopPhase.OBSERVE,
            LoopPhase.DETECT,
            LoopPhase.INVESTIGATE,
            LoopPhase.HYPOTHESIZE,
            LoopPhase.TEST,
            LoopPhase.VERIFY,
        ]

        for phase in phases:
            step = LoopStep(
                phase=phase,
                description=f"Phase {phase.value} for: {question}",
                input_data=data,
                status="completed",
                duration_ms=10.0,
            )

            if phase == LoopPhase.OBSERVE:
                step.output_data = {"observations": f"Data collected for iteration {iteration_num}"}
            elif phase == LoopPhase.DETECT:
                step.output_data = {"anomalies": ["Potential signal detected"]}
                iteration.findings.append(f"Detection: signal found in iteration {iteration_num}")
            elif phase == LoopPhase.HYPOTHESIZE:
                step.output_data = {"hypothesis": f"Hypothesis for iteration {iteration_num}"}
                iteration.hypotheses.append(f"H{iteration_num}: Working hypothesis")

            iteration.steps.append(step)
            iteration.current_phase = phase

        iteration.status = "completed"
        iteration.confidence = 0.5 + iteration_num * 0.1
        return iteration

    def _should_stop(self, iteration: ResearchIteration, result: LoopResult, config: LoopConfig) -> bool:
        if len(result.iterations) >= config.max_iterations:
            return True
        if len(result.final_hypotheses) >= 10:
            return True
        if iteration.confidence >= 0.9:
            return True
        return False

    def _compute_final_confidence(self, result: LoopResult) -> float:
        if not result.iterations:
            return 0.0
        last = result.iterations[-1]
        return last.confidence

    def _build_audit_trail(self, result: LoopResult) -> list[dict]:
        trail = []
        for iteration in result.iterations:
            for step in iteration.steps:
                trail.append({
                    "iteration_id": iteration.iteration_id,
                    "phase": step.phase.value,
                    "status": step.status,
                    "duration_ms": step.duration_ms,
                })
        return trail
