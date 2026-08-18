"""Tests for LLM provider abstraction — M15.5 Phase 2."""

from __future__ import annotations

import os

import pytest

from core.ai.llm.base import (
    LLMConfig,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    ModelRouter,
    ModelTier,
)


class TestLLMConfig:
    def test_default_config(self):
        config = LLMConfig()
        assert config.model == "gpt-4o-mini"
        assert config.temperature == 0.1
        assert config.max_tokens == 4096

    def test_custom_config(self):
        config = LLMConfig(model="gpt-4o", temperature=0.5, max_tokens=8192)
        assert config.model == "gpt-4o"
        assert config.temperature == 0.5
        assert config.max_tokens == 8192


class TestLLMMessage:
    def test_message_to_dict(self):
        msg = LLMMessage(role="user", content="What is AAPL's P/E ratio?")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "What is AAPL's P/E ratio?"

    def test_system_message(self):
        msg = LLMMessage(role="system", content="You are a financial analyst.")
        assert msg.role == "system"


class TestLLMResponse:
    def test_response_fields(self):
        response = LLMResponse(
            content="AAPL's P/E ratio is 28.5",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
            latency_ms=500.0,
            cost_usd=0.001,
        )
        assert response.content == "AAPL's P/E ratio is 28.5"
        assert response.model == "gpt-4o-mini"
        assert response.usage["total_tokens"] == 15
        assert response.cost_usd == 0.001


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, model: str = "mock-model"):
        super().__init__(provider_name="mock", config=LLMConfig(model=model))
        self._responses: list[str] = []
        self._call_count_internal = 0

    def set_responses(self, responses: list[str]) -> None:
        self._responses = responses
        self._call_count_internal = 0

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        if self._call_count_internal < len(self._responses):
            content = self._responses[self._call_count_internal]
        else:
            content = "Mock response"
        self._call_count_internal += 1

        return LLMResponse(
            content=content,
            model=self.config.model,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
            latency_ms=100.0,
            cost_usd=0.0001,
        )

    def health_check(self) -> bool:
        return True


# Need to import Any for the type hint
from typing import Any


class TestMockLLMProvider:
    def test_complete(self):
        provider = MockLLMProvider()
        provider.set_responses(["AAPL P/E is 28.5"])
        messages = [LLMMessage(role="user", content="What is AAPL P/E?")]
        response = provider.complete(messages)
        assert response.content == "AAPL P/E is 28.5"
        assert response.model == "mock-model"

    def test_complete_simple(self):
        provider = MockLLMProvider()
        provider.set_responses(["The revenue is $100B"])
        result = provider.complete_simple("What is the revenue?")
        assert result == "The revenue is $100B"

    def test_stats(self):
        provider = MockLLMProvider()
        provider.set_responses(["test"])
        provider.complete([LLMMessage(role="user", content="test")])
        stats = provider.get_stats()
        assert stats["call_count"] == 1
        assert stats["total_tokens"] == 15

    def test_health_check(self):
        provider = MockLLMProvider()
        assert provider.health_check() is True


class TestModelRouter:
    def test_register_provider(self):
        router = ModelRouter()
        mock_provider = MockLLMProvider()
        router.register_provider(ModelTier.FAST, mock_provider)
        provider = router.get_provider(ModelTier.FAST)
        assert provider.provider_name == "mock"

    def test_fallback(self):
        router = ModelRouter()
        fallback = MockLLMProvider()
        router.set_fallback(fallback)
        provider = router.get_provider(ModelTier.REASONING)
        assert provider.provider_name == "mock"

    def test_route_simple_query(self):
        router = ModelRouter()
        fast = MockLLMProvider("fast")
        balanced = MockLLMProvider("balanced")
        reasoning = MockLLMProvider("reasoning")
        router.register_provider(ModelTier.FAST, fast)
        router.register_provider(ModelTier.BALANCED, balanced)
        router.register_provider(ModelTier.REASONING, reasoning)

        provider = router.route_query("What is AAPL's price?")
        assert provider.config.model == "fast"

    def test_route_complex_query(self):
        router = ModelRouter()
        fast = MockLLMProvider("fast")
        balanced = MockLLMProvider("balanced")
        reasoning = MockLLMProvider("reasoning")
        router.register_provider(ModelTier.FAST, fast)
        router.register_provider(ModelTier.BALANCED, balanced)
        router.register_provider(ModelTier.REASONING, reasoning)

        provider = router.route_query("Analyze the contradictions in this earnings report")
        assert provider.config.model == "reasoning"

    def test_route_balanced_query(self):
        router = ModelRouter()
        fast = MockLLMProvider("fast")
        balanced = MockLLMProvider("balanced")
        reasoning = MockLLMProvider("reasoning")
        router.register_provider(ModelTier.FAST, fast)
        router.register_provider(ModelTier.BALANCED, balanced)
        router.register_provider(ModelTier.REASONING, reasoning)

        provider = router.route_query("Tell me about the company")
        assert provider.config.model == "balanced"


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="Set OPENAI_API_KEY to run real LLM tests"
)
class TestOpenAIProvider:
    def test_complete(self):
        from core.ai.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(config=LLMConfig(model="gpt-4o-mini", max_tokens=50))
        messages = [LLMMessage(role="user", content="Say 'hello' in one word")]
        response = provider.complete(messages)
        assert response.content
        assert response.model
        assert response.usage["total_tokens"] > 0

    def test_health_check(self):
        from core.ai.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider()
        assert provider.health_check() is True
