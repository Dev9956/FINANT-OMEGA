"""FININT OMEGA — Ollama local LLM provider implementation."""

from __future__ import annotations

import os
import time
from typing import Any

import structlog

from core.ai.llm.base import LLMConfig, LLMMessage, LLMProvider, LLMResponse

logger = structlog.get_logger()

# Lazy import
httpx = None


def _get_httpx():
    global httpx
    if httpx is None:
        try:
            import httpx as _httpx
            httpx = _httpx
        except ImportError:
            raise ImportError("httpx is required for Ollama provider. Install with: pip install httpx")
    return httpx


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider.

    Connects to a local Ollama instance running at http://localhost:11434
    for completely free, private, offline AI research and reasoning.
    """

    def __init__(self, config: LLMConfig | None = None, base_url: str | None = None) -> None:
        default_config = LLMConfig(
            model=os.environ.get("OLLAMA_MODEL", "qwen3:4b"),
            temperature=0.2,
            max_tokens=4096,
            timeout_seconds=120.0,
            cost_per_1k_input_tokens=0.0,
            cost_per_1k_output_tokens=0.0,
        )
        super().__init__("ollama", config or default_config)
        self.base_url = (base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    def health_check(self) -> bool:
        """Check if Ollama local server is running."""
        try:
            _httpx = _get_httpx()
            resp = _httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception as e:
            logger.debug("ollama_health_check_failed", error=str(e))
            return False

    def _complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        """Execute chat completion via Ollama local API."""
        _httpx = _get_httpx()
        start = time.monotonic()

        formatted_messages = [msg.to_dict() for msg in messages]

        # Use Ollama native chat API
        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        url = f"{self.base_url}/api/chat"

        try:
            resp = _httpx.post(url, json=payload, timeout=self.config.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            latency = (time.monotonic() - start) * 1000

            content = data.get("message", {}).get("content", "")
            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)

            return LLMResponse(
                content=content,
                model=data.get("model", self.config.model),
                usage={
                    "prompt_tokens": prompt_eval_count,
                    "completion_tokens": eval_count,
                    "total_tokens": prompt_eval_count + eval_count,
                },
                finish_reason="done" if data.get("done") else "unknown",
                latency_ms=latency,
                cost_usd=0.0,  # Local inference is free
                metadata={"provider": "ollama", "done_reason": data.get("done_reason")},
            )

        except Exception as e:
            logger.error("ollama_completion_failed", url=url, model=self.config.model, error=str(e))
            raise RuntimeError(f"Ollama connection error: {e}")
