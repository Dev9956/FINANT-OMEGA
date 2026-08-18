"""FININT OMEGA — Evidence Execution Pipeline.

Connects: Question → Plan → Retrieval → Tools → Quant → Evidence →
Contradiction → LLM → Answer → Graph → Audit
"""

from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from core.ai.llm.base import LLMMessage, LLMProvider, ModelTier, ModelRouter
from core.evidence.audit.models import AuditEvent, AuditEventType, ModelCallRecord, ToolCallRecord
from core.evidence.audit.store import AuditTrailStore
from core.evidence.graph.graph import EvidenceGraph
from core.evidence.graph.models import (
    EvidenceEdge,
    EvidenceNode,
    EvidenceNodeType,
    GraphRelationship,
)
from core.research.deep_research.models import (
    ConflictItem,
    EvidenceItem,
    ResearchConfig,
    ResearchDepth,
    ResearchRun,
    ResearchSynthesis,
    ResearchTask,
    TaskStatus,
)
from core.research.deep_research.planner import ResearchPlanner
from core.research.deep_research.synthesis import ResearchSynthesizer
from core.ai.llm.base import ModelTier as _ModelTier

logger = structlog.get_logger()

# Tool registry type
ToolHandler = Any


class PipelineStage(str):
    """Pipeline stage identifiers."""
    PLAN = "plan"
    RETRIEVE = "retrieve"
    TOOLS = "tools"
    QUANT = "quant"
    EVIDENCE = "evidence"
    CONTRADICTION = "contradiction"
    LLM = "llm"
    SYNTHESIS = "synthesis"
    GRAPH = "graph"
    AUDIT = "audit"


class PipelineResult:
    """Result of a pipeline execution."""

    def __init__(self) -> None:
        self.research_id: str = ""
        self.question: str = ""
        self.stages: list[str] = []
        self.evidence: list[EvidenceItem] = []
        self.conflicts: list[ConflictItem] = []
        self.synthesis: ResearchSynthesis | None = None
        self.llm_answer: str = ""
        self.graph: EvidenceGraph | None = None
        self.duration_ms: float = 0.0
        self.stage_timings: dict[str, float] = {}
        self.metadata: dict[str, Any] = {}

    def to_dict(self) -> dict:
        return {
            "research_id": self.research_id,
            "question": self.question,
            "stages_executed": self.stages,
            "evidence_count": len(self.evidence),
            "conflict_count": len(self.conflicts),
            "synthesis": self.synthesis.model_dump() if self.synthesis else None,
            "llm_answer": self.llm_answer,
            "duration_ms": self.duration_ms,
            "stage_timings": self.stage_timings,
            "metadata": self.metadata,
        }


class EvidencePipeline:
    """End-to-end evidence execution pipeline."""

    def __init__(
        self,
        tools: dict[str, ToolHandler] | None = None,
        llm_provider: LLMProvider | None = None,
        model_router: ModelRouter | None = None,
        graph: EvidenceGraph | None = None,
        audit_store: AuditTrailStore | None = None,
        retrieval: Any | None = None,
    ) -> None:
        self._tools = tools or {}
        self._llm = llm_provider
        self._router = model_router
        self._graph = graph or EvidenceGraph()
        self._audit = audit_store or AuditTrailStore()
        self._retrieval = retrieval  # VectorIndex-like object
        self._planner = ResearchPlanner()
        self._synthesizer = ResearchSynthesizer()
        self.stage_timings: dict[str, float] = {}

    def register_tool(self, name: str, handler: ToolHandler) -> None:
        """Register a tool for the tool stage."""
        self._tools[name] = handler

    def set_llm(self, provider: LLMProvider) -> None:
        """Set the LLM provider directly."""
        self._llm = provider

    def set_router(self, router: ModelRouter) -> None:
        """Set the model router."""
        self._router = router

    def set_retrieval(self, retrieval: Any) -> None:
        """Set the retrieval index (RAG)."""
        self._retrieval = retrieval

    def _get_llm(self, query: str) -> LLMProvider:
        """Get the appropriate LLM provider for a query."""
        if self._router:
            try:
                return self._router.route_query(query)
            except ValueError:
                pass
        if self._llm:
            return self._llm
        raise ValueError("No LLM provider configured")

    def _log_stage(self, stage: str, start: float, research_id: str) -> None:
        self.stage_timings[stage] = (time.monotonic() - start) * 1000
        logger.info("pipeline_stage", stage=stage, research_id=research_id, duration_ms=self.stage_timings[stage])

    def execute(
        self,
        question: str,
        config: ResearchConfig | None = None,
        symbol: str | None = None,
    ) -> PipelineResult:
        """Execute the full pipeline for a question."""
        result = PipelineResult()
        result.research_id = str(uuid.uuid4())
        result.question = question
        start = time.monotonic()

        # ---- Stage 1: PLAN ----
        s = time.monotonic()
        config = config or ResearchConfig.for_depth(ResearchDepth.STANDARD)
        try:
            sub_questions, tasks = self._planner.plan(question, config)
        except ValueError:
            sub_questions, tasks = [question], [ResearchTask(question=question)]
        result.stages.append(PipelineStage.PLAN)
        self._log_stage(PipelineStage.PLAN, s, result.research_id)
        self._audit.record_event(AuditEvent(
            research_id=result.research_id,
            event_type=AuditEventType.research_started,
            data={"question": question, "task_count": len(tasks), "sub_questions": sub_questions},
        ))

        # ---- Stage 2: RETRIEVE ----
        s = time.monotonic()
        retrieved_contexts: list[str] = []
        if self._retrieval:
            try:
                hits = self._retrieval.search(question, top_k=5)
                retrieved_contexts = [h.get("content", "") if isinstance(h, dict) else str(h) for h in hits]
            except Exception as e:
                logger.warning("pipeline_retrieval_failed", error=str(e))
        result.stages.append(PipelineStage.RETRIEVE)
        self._log_stage(PipelineStage.RETRIEVE, s, result.research_id)
        self._audit.record_event(AuditEvent(
            research_id=result.research_id,
            event_type=AuditEventType.evidence_collected,
            data={"query": question, "hits": len(retrieved_contexts)},
        ))

        # ---- Stage 3: TOOLS ----
        s = time.monotonic()
        evidence_from_tools = self._execute_tools(question, symbol, result.research_id)
        result.evidence.extend(evidence_from_tools)
        result.stages.append(PipelineStage.TOOLS)
        self._log_stage(PipelineStage.TOOLS, s, result.research_id)

        # ---- Stage 4: QUANT ----
        s = time.monotonic()
        quant_evidence = self._execute_quant(question, symbol, result.research_id)
        result.evidence.extend(quant_evidence)
        result.stages.append(PipelineStage.QUANT)
        self._log_stage(PipelineStage.QUANT, s, result.research_id)

        # ---- Stage 5: EVIDENCE ----
        s = time.monotonic()
        evidence_items = self._build_evidence(question, retrieved_contexts, result.research_id)
        result.evidence.extend(evidence_items)
        result.stages.append(PipelineStage.EVIDENCE)
        self._log_stage(PipelineStage.EVIDENCE, s, result.research_id)
        self._audit.record_event(AuditEvent(
            research_id=result.research_id,
            event_type=AuditEventType.evidence_collected,
            data={"evidence_count": len(result.evidence)},
        ))

        # ---- Stage 6: CONTRADICTION ----
        s = time.monotonic()
        result.conflicts = self._detect_contradictions(result.evidence)
        result.stages.append(PipelineStage.CONTRADICTION)
        self._log_stage(PipelineStage.CONTRADICTION, s, result.research_id)
        self._audit.record_event(AuditEvent(
            research_id=result.research_id,
            event_type=AuditEventType.evidence_verified,
            data={"conflicts_found": len(result.conflicts)},
        ))

        # ---- Stage 7: LLM ----
        s = time.monotonic()
        llm_answer, llm_response = self._synthesize_with_llm(question, result.evidence, result.conflicts, result.research_id)
        result.llm_answer = llm_answer
        result.stages.append(PipelineStage.LLM)
        self._log_stage(PipelineStage.LLM, s, result.research_id)
        if llm_response:
            import hashlib
            self._audit.record_event(AuditEvent(
                research_id=result.research_id,
                event_type=AuditEventType.model_called,
                data=ModelCallRecord(
                    model_id=llm_response.model,
                    prompt_hash=hashlib.sha256(question.encode()).hexdigest(),
                    response_hash=hashlib.sha256(llm_response.content.encode()).hexdigest(),
                    tokens_used=llm_response.usage.get("total_tokens", 0),
                    duration_ms=llm_response.latency_ms,
                    cost=llm_response.cost_usd,
                ).model_dump(),
            ))

        # ---- Stage 8: SYNTHESIS ----
        s = time.monotonic()
        result.synthesis = self._synthesizer.synthesize(
            result.research_id,
            result.evidence,
            result.conflicts,
            config,
        )
        result.stages.append(PipelineStage.SYNTHESIS)
        self._log_stage(PipelineStage.SYNTHESIS, s, result.research_id)

        # ---- Stage 9: GRAPH ----
        s = time.monotonic()
        self._build_evidence_graph(result)
        result.stages.append(PipelineStage.GRAPH)
        self._log_stage(PipelineStage.GRAPH, s, result.research_id)

        # ---- Stage 10: AUDIT ----
        s = time.monotonic()
        self._audit.record_event(AuditEvent(
            research_id=result.research_id,
            event_type=AuditEventType.research_completed,
            data={
                "evidence_count": len(result.evidence),
                "conflicts": len(result.conflicts),
                "synthesis_confidence": result.synthesis.confidence if result.synthesis else 0.0,
            },
        ))
        result.stages.append(PipelineStage.AUDIT)
        self._log_stage(PipelineStage.AUDIT, s, result.research_id)

        result.duration_ms = (time.monotonic() - start) * 1000
        result.metadata["symbol"] = symbol
        return result

    def _execute_tools(self, question: str, symbol: str | None, research_id: str) -> list[EvidenceItem]:
        """Execute registered tools matching the question."""
        evidence: list[EvidenceItem] = []
        q_lower = question.lower()

        tool_rules: list[tuple[list[str], str]] = [
            (["price", "quote", "market", "trading", "stock"], "market_data"),
            (["earnings", "eps", "revenue", "quarterly"], "earnings_data"),
            (["valuation", "pe", "fair value", "dcf", "fundamental"], "fundamentals"),
            (["risk", "volatility", "drawdown", "var", "sharpe"], "risk_analyzer"),
            (["macro", "economy", "gdp", "inflation", "interest"], "macro_data"),
            (["news", "headline", "announcement", "filing"], "news_search"),
        ]

        matched = {rule[1] for rule in tool_rules if any(kw in q_lower for kw in rule[0])}
        if symbol and not matched:
            matched.add("market_data")

        for tool_name in matched:
            handler = self._tools.get(tool_name)
            if not handler:
                continue
            start = time.monotonic()
            try:
                kwargs: dict[str, Any] = {"question": question}
                if symbol:
                    kwargs["symbol"] = symbol
                raw = handler(**kwargs)

                items = self._tool_output_to_evidence(raw, tool_name, research_id)
                evidence.extend(items)

                self._audit.record_event(AuditEvent(
                    research_id=research_id,
                    event_type=AuditEventType.tool_called,
                    data=ToolCallRecord(
                        tool_name=tool_name,
                        arguments_hash=hashlib.sha256(str(kwargs).encode()).hexdigest(),
                        result_hash=hashlib.sha256(str(raw)[:500].encode()).hexdigest(),
                        duration_ms=(time.monotonic() - start) * 1000,
                        success=True,
                    ).model_dump(),
                ))
            except Exception as e:
                self._audit.record_event(AuditEvent(
                    research_id=research_id,
                    event_type=AuditEventType.tool_called,
                    data=ToolCallRecord(
                        tool_name=tool_name,
                        arguments_hash=hashlib.sha256(str(kwargs).encode()).hexdigest(),
                        result_hash="",
                        duration_ms=(time.monotonic() - start) * 1000,
                        success=False,
                        error_message=str(e),
                    ).model_dump(),
                ))
                logger.warning("pipeline_tool_failed", tool=tool_name, error=str(e))

        return evidence

    def _execute_quant(self, question: str, symbol: str | None, research_id: str) -> list[EvidenceItem]:
        """Execute quant tools (deterministic numeric analysis first)."""
        evidence: list[EvidenceItem] = []
        if symbol and "risk_analyzer" in self._tools:
            handler = self._tools["risk_analyzer"]
            try:
                raw = handler(symbol=symbol, question=question)
                evidence.extend(self._tool_output_to_evidence(raw, "quant_risk", research_id))
            except Exception as e:
                logger.warning("pipeline_quant_failed", error=str(e))
        return evidence

    def _build_evidence(
        self,
        question: str,
        retrieved_contexts: list[str],
        research_id: str,
    ) -> list[EvidenceItem]:
        """Build evidence items from retrieved contexts."""
        items: list[EvidenceItem] = []
        for i, ctx in enumerate(retrieved_contexts):
            if not ctx or not ctx.strip():
                continue
            items.append(EvidenceItem(
                source_type="retrieval",
                source_id=f"retrieved_{i}",
                content=ctx,
                confidence=0.6,
                metadata={"research_id": research_id},
            ))
        return items

    def _tool_output_to_evidence(
        self,
        raw: Any,
        source_type: str,
        research_id: str,
    ) -> list[EvidenceItem]:
        """Convert a tool output into evidence items."""
        if raw is None:
            return []
        if isinstance(raw, list):
            return [
                EvidenceItem(
                    source_type=source_type,
                    source_id=f"{source_type}_{i}",
                    content=str(r),
                    confidence=0.7,
                    metadata={"research_id": research_id},
                )
                for i, r in enumerate(raw) if r is not None
            ]
        return [
            EvidenceItem(
                source_type=source_type,
                source_id=f"{source_type}_1",
                content=str(raw),
                confidence=0.7,
                metadata={"research_id": research_id},
            )
        ]

    def _detect_contradictions(self, evidence: list[EvidenceItem]) -> list[ConflictItem]:
        """Detect conflicts between evidence claims."""
        claims: dict[str, list[EvidenceItem]] = {}
        for ev in evidence:
            key = ev.supports_claim or ev.contradicts_claim
            if key:
                claims.setdefault(key, []).append(ev)

        conflicts: list[ConflictItem] = []
        for claim, items in claims.items():
            supporting = [e for e in items if e.supports_claim == claim]
            contradicting = [e for e in items if e.contradicts_claim == claim]
            if supporting and contradicting:
                conflicts.append(ConflictItem(
                    claim_a=claim,
                    claim_b=claim,
                    evidence_a_ids=[e.evidence_id for e in supporting],
                    evidence_b_ids=[e.evidence_id for e in contradicting],
                    severity=min(1.0, max(e.confidence for e in items)),
                ))
        return conflicts

    def _synthesize_with_llm(
        self,
        question: str,
        evidence: list[EvidenceItem],
        conflicts: list[ConflictItem],
        research_id: str,
    ) -> tuple[str, Any]:
        """Use the LLM to produce a narrative answer grounded in evidence."""
        if not self._llm and not self._router:
            return self._fallback_synthesis(question, evidence), None

        try:
            provider = self._get_llm(question)
        except ValueError as e:
            logger.warning("pipeline_no_llm", error=str(e))
            return self._fallback_synthesis(question, evidence), None

        # Deterministic evidence summary first — LLM explains, doesn't invent numbers
        evidence_lines = []
        for ev in evidence[:30]:
            evidence_lines.append(
                f"- [{ev.source_type} conf={ev.confidence:.2f}] {ev.content[:300]}"
            )
        conflict_lines = []
        for c in conflicts:
            conflict_lines.append(f"- {c.claim_a} (severity: {c.severity:.2f})")

        system_prompt = (
            "You are a financial research analyst. Your job is to explain and reason "
            "about the evidence provided, NEVER to invent new numbers or facts. "
            "All quantitative claims must be traceable to the evidence below. "
            "If the evidence does not support a claim, say so explicitly. "
            "Structure your answer with: Summary, Key Evidence, Contradictions, and Conclusion."
        )
        user_prompt = (
            f"QUESTION: {question}\n\n"
            f"EVIDENCE ({len(evidence)} items):\n" + "\n".join(evidence_lines) + "\n\n"
            f"CONTRADICTIONS ({len(conflicts)}):\n" + "\n".join(conflict_lines) + "\n\n"
            "Provide your evidence-grounded analysis."
        )

        try:
            response = provider.complete(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_prompt),
                ],
                temperature=0.1,
            )
            return response.content, response
        except Exception as e:
            logger.error("pipeline_llm_synthesis_failed", error=str(e))
            return self._fallback_synthesis(question, evidence), None

    def _fallback_synthesis(self, question: str, evidence: list[EvidenceItem]) -> str:
        """Deterministic synthesis when no LLM is available."""
        if not evidence:
            return "No evidence available. Cannot answer the question."
        lines = [
            f"Evidence-based analysis for: {question}",
            f"Gathered {len(evidence)} evidence items:",
        ]
        for ev in evidence[:10]:
            lines.append(f"  - [{ev.source_type}] {ev.content[:200]}")
        return "\n".join(lines)

    def _build_evidence_graph(self, result: PipelineResult) -> None:
        """Populate the evidence graph from pipeline results."""
        # Question node
        q_node = EvidenceNode(
            node_id=f"question_{result.research_id}",
            node_type=EvidenceNodeType.CLAIM,
            label="Research Question",
            content=result.question,
        )
        self._graph.add_node(q_node)

        # Evidence nodes
        for ev in result.evidence:
            node = EvidenceNode(
                node_id=ev.evidence_id,
                node_type=EvidenceNodeType.EVIDENCE,
                label=ev.source_type,
                content=ev.content,
                confidence=ev.confidence,
            )
            self._graph.add_node(node)
            # Evidence supports the question
            self._graph.add_edge(EvidenceEdge(
                source_node_id=node.node_id,
                target_node_id=q_node.node_id,
                relationship=GraphRelationship.SUPPORTS,
            ))

        # Conclusion node
        if result.synthesis:
            conclusion_node = EvidenceNode(
                node_id=f"conclusion_{result.research_id}",
                node_type=EvidenceNodeType.CONCLUSION,
                label="Conclusion",
                content=result.synthesis.conclusion,
                confidence=result.synthesis.confidence,
            )
            self._graph.add_node(conclusion_node)
            for ev in result.evidence[:20]:
                try:
                    self._graph.add_edge(EvidenceEdge(
                        source_node_id=ev.evidence_id,
                        target_node_id=conclusion_node.node_id,
                        relationship=GraphRelationship.SUPPORTS,
                    ))
                except ValueError:
                    continue
            self._graph.add_edge(EvidenceEdge(
                source_node_id=q_node.node_id,
                target_node_id=conclusion_node.node_id,
                relationship=GraphRelationship.DERIVED_FROM,
            ))
        result.graph = self._graph