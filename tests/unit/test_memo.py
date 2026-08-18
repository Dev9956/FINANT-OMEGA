"""Tests for Investment Memo Engine."""

import pytest
from core.intelligence.memo.engine import MemoEngine


class TestMemoEngine:
    def setup_method(self):
        self.engine = MemoEngine()

    def test_generate_memo(self):
        memo = self.engine.generate(
            entity="AAPL",
            thesis="Apple is well-positioned for AI growth",
            bull_case="Services revenue accelerates",
            bear_case="iPhone demand weakens",
        )
        assert memo.entity == "AAPL"
        assert memo.thesis is not None
        assert memo.bull_case is not None
        assert memo.bear_case is not None

    def test_memo_has_executive_summary(self):
        memo = self.engine.generate(entity="AAPL", thesis="Test")
        assert memo.executive_summary is not None

    def test_memo_has_what_would_change_my_mind(self):
        memo = self.engine.generate(entity="AAPL")
        assert memo.what_would_change_my_mind is not None

    def test_render_markdown(self):
        memo = self.engine.generate(entity="AAPL", thesis="Test thesis")
        md = self.engine.render_markdown(memo)
        assert "# Investment Memo: AAPL" in md
        assert "Test thesis" in md

    def test_get_memo(self):
        memo = self.engine.generate(entity="AAPL")
        retrieved = self.engine.get_memo(memo.memo_id)
        assert retrieved is not None

    def test_get_memo_not_found(self):
        assert self.engine.get_memo("nonexistent") is None