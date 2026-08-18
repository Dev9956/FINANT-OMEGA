"""FININT OMEGA — Base LLM provider abstraction."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class ModelTier(Enum):
    """Model tiers for routing decisions."""
    FAST = "fast"          # Quick tasks, simple queries
    BALANCED = "balanced"  # General purpose
    REASONING = "reasoning"  # Complex analysis, deep research


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_seconds: float = 60.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0


@dataclass
class LLMMessage:
    """A message in the LLM conversation."""
    role: str  # "system", "user", "assistant"
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    model: str
    usage: dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str
    latency_ms: float
    cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, provider_name: str, config: LLMConfig | None = None) -> None:
        self.provider_name = provider_name
        self.config = config or LLMConfig()
        self._call_count = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._error_count = 0

    @abstractmethod
    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Provider-specific completion implementation."""
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the provider is reachable."""
        ...

    def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Complete with retry logic and cost tracking."""
        config = LLMConfig(
            model=self.config.model,
            temperature=temperature if temperature is not None else self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            timeout_seconds=self.config.timeout_seconds,
            max_retries=self.config.max_retries,
        )

        last_error: Exception | None = None
        for attempt in range(config.max_retries):
            try:
                start = time.monotonic()
                response = self._complete(messages, **kwargs)
                latency = (time.monotonic() - start) * 1000

                self._call_count += 1
                self._total_tokens += response.usage.get("total_tokens", 0)
                self._total_cost += response.cost_usd

                logger.info(
                    "llm_complete",
                    provider=self.provider_name,
                    model=response.model,
                    tokens=response.usage.get("total_tokens", 0),
                    cost=response.cost_usd,
                    latency_ms=latency,
                    attempt=attempt + 1,
                )
                return response

            except Exception as e:
                last_error = e
                self._error_count += 1
                logger.warning(
                    "llm_retry",
                    provider=self.provider_name,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < config.max_retries - 1:
                    time.sleep(config.retry_delay_seconds * (2 ** attempt))

        logger.error(
            "llm_failed",
            provider=self.provider_name,
            error=str(last_error),
            attempts=config.max_retries,
        )
        raise last_error  # type: ignore

    def complete_simple(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Simple completion that returns just the text."""
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))
        response = self.complete(messages, temperature=temperature, max_tokens=max_tokens)
        return response.content

    def get_stats(self) -> dict:
        return {
            "provider": self.provider_name,
            "model": self.config.model,
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "total_cost_usd": self._total_cost,
            "error_count": self._error_count,
        }


class ModelRouter:
    """Routes queries to appropriate models based on complexity."""

    def __init__(self) -> None:
        self._providers: dict[ModelTier, LLMProvider] = {}
        self._fallback_provider: LLMProvider | None = None

    def register_provider(self, tier: ModelTier, provider: LLMProvider) -> None:
        """Register a provider for a specific tier."""
        self._providers[tier] = provider

    def set_fallback(self, provider: LLMProvider) -> None:
        """Set a fallback provider."""
        self._fallback_provider = provider

    def get_provider(self, tier: ModelTier) -> LLMProvider:
        """Get provider for a tier, with fallback."""
        if tier in self._providers:
            return self._providers[tier]
        if self._fallback_provider:
            return self._fallback_provider
        raise ValueError(f"No provider registered for tier {tier.value}")

    def route_query(self, query: str) -> LLMProvider:
        """Route a query to the appropriate tier based on complexity."""
        query_lower = query.lower()

        # Complex analysis keywords
        complex_keywords = [
            "analyze", "compare", "evaluate", "assess", "reason",
            "investigate", "deep research", "comprehensive", "detailed",
            "contradiction", "scenario", "counterfactual", "debate",
        ]
        if any(kw in query_lower for kw in complex_keywords):
            return self.get_provider(ModelTier.REASONING)

        # Simple query keywords
        simple_keywords = [
            "what is", "how much", "when", "where", "who",
            "price", "ratio", "growth", "revenue",
        ]
        if any(kw in query_lower for kw in simple_keywords):
            return self.get_provider(ModelTier.FAST)

        # Default to balanced
        return self.get_provider(ModelTier.BALANCED)
