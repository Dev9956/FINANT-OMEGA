"""FININT OMEGA — Investment Memo Engine."""

from __future__ import annotations

from core.intelligence.memo.models import InvestmentMemo, MemoSection


class MemoEngine:
    """Generate structured investment memos."""

    def __init__(self) -> None:
        self._memos: dict[str, InvestmentMemo] = {}

    def generate(
        self,
        entity: str,
        thesis: str = "",
        bull_case: str = "",
        bear_case: str = "",
        base_case: str = "",
        valuation: str = "",
        financial_quality: str = "",
        risks: str = "",
        contradicting_evidence: str = "",
        scenario_analysis: str = "",
        evidence: list[str] | None = None,
        evidence_limitations: str = "",
    ) -> InvestmentMemo:
        ev = evidence or []

        exec_summary = f"Investment analysis of {entity}. " + (thesis[:200] if thesis else "Thesis pending.")
        what_change = f"What would change my mind about {entity}: " + (
            risks[:200] if risks else "Key risks and thesis invalidation conditions."
        )

        memo = InvestmentMemo(
            entity=entity,
            title=f"Investment Memo: {entity}",
            executive_summary=MemoSection(title="Executive Summary", content=exec_summary, evidence=ev),
            thesis=MemoSection(title="Thesis", content=thesis, evidence=ev) if thesis else None,
            bull_case=MemoSection(title="Bull Case", content=bull_case) if bull_case else None,
            bear_case=MemoSection(title="Bear Case", content=bear_case) if bear_case else None,
            base_case=MemoSection(title="Base Case", content=base_case) if base_case else None,
            valuation=MemoSection(title="Valuation", content=valuation) if valuation else None,
            financial_quality=MemoSection(title="Financial Quality", content=financial_quality) if financial_quality else None,
            risks=MemoSection(title="Risks", content=risks) if risks else None,
            contradicting_evidence=MemoSection(title="Contradicting Evidence", content=contradicting_evidence) if contradicting_evidence else None,
            scenario_analysis=MemoSection(title="Scenario Analysis", content=scenario_analysis) if scenario_analysis else None,
            what_would_change_my_mind=MemoSection(title="What Would Change My Mind", content=what_change, evidence=ev),
            evidence_limitations=MemoSection(title="Data Limitations", content=evidence_limitations) if evidence_limitations else None,
            confidence=0.6,
        )

        self._memos[memo.memo_id] = memo
        return memo

    def get_memo(self, memo_id: str) -> InvestmentMemo | None:
        return self._memos.get(memo_id)

    def render_markdown(self, memo: InvestmentMemo) -> str:
        parts = [f"# {memo.title}", f"\n**Entity:** {memo.entity}", f"**Confidence:** {memo.confidence:.0%}\n"]

        sections = [
            memo.executive_summary, memo.thesis, memo.bull_case, memo.bear_case,
            memo.base_case, memo.valuation, memo.financial_quality, memo.risks,
            memo.contradicting_evidence, memo.scenario_analysis,
            memo.what_would_change_my_mind, memo.evidence_limitations,
        ]

        for section in sections:
            if section:
                parts.append(f"\n## {section.title}\n")
                parts.append(section.content)
                if section.evidence:
                    parts.append(f"\n*Evidence: {', '.join(section.evidence[:3])}*")

        return "\n".join(parts)