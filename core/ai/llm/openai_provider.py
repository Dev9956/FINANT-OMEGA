"""FININT OMEGA — OpenAI LLM provider implementation."""

from __future__ import annotations

import importlib
import os
import time
from typing import Any

import structlog

from core.ai.llm.base import LLMConfig, LLMMessage, LLMProvider, LLMResponse

logger = structlog.get_logger()

# Lazy import
_openai = None


def _get_openai():
    global _openai
    if _openai is None:
        try:
            _openai = importlib.import_module("openai")
        except ImportError:
            raise ImportError(
                "openai is required for LLM integration. "
                "Install with: pip install openai"
            )
    return _openai


# Model pricing (USD per 1K tokens)
MODEL_PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "o1": {"input": 0.015, "output": 0.06},
    "o1-mini": {"input": 0.003, "output": 0.012},
    "o3-mini": {"input": 0.0011, "output": 0.0044},
}


class OpenAIProvider(LLMProvider):
    """OpenAI API LLM provider.

    Supports GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo, o1, o1-mini, o3-mini.
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        api_key: str | None = None,
        organization: str | None = None,
    ) -> None:
        resolved_config = config or LLMConfig(model="gpt-4o-mini")
        super().__init__(provider_name="openai", config=resolved_config)
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._organization = organization or os.environ.get("OPENAI_ORG_ID")
        self._client = None

    def _get_client(self):
        if self._client is None:
            openai_mod = _get_openai()
            kwargs: dict[str, Any] = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            if self._organization:
                kwargs["organization"] = self._organization
            kwargs["timeout"] = self.config.timeout_seconds
            self._client = openai_mod.OpenAI(**kwargs)
        return self._client

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Complete using OpenAI API."""
        client = self._get_client()
        model = kwargs.get("model", self.config.model)
        temperature = kwargs.get("temperature", self.config.temperature)
        max_tokens = kwargs.get("max_tokens", self.config.max_tokens)

        api_messages = [m.to_dict() for m in messages]

        start = time.monotonic()

        # Handle reasoning models (o1, o1-mini, o3-mini) differently
        if model.startswith("o1") or model.startswith("o3"):
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                max_completion_tokens=max_tokens,
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        latency = (time.monotonic() - start) * 1000

        choice = response.choices[0]
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost
        pricing = MODEL_PRICING.get(model, MODEL_PRICING.get("gpt-4o-mini", {"input": 0.00015, "output": 0.0006}))
        cost = (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1000

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
            finish_reason=choice.finish_reason or "stop",
            latency_ms=latency,
            cost_usd=cost,
            metadata={
                "provider": "openai",
                "organization": self._organization,
            },
        )

    def health_check(self) -> bool:
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Say ok"}],
                max_tokens=5,
            )
            return bool(response.choices)
        except Exception as e:
            logger.error("openai_health_check_failed", error=str(e))
            return False
