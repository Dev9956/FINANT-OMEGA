"""Tests for Ollama local LLM provider."""

from unittest.mock import MagicMock, patch

import pytest

from core.ai.llm.base import LLMMessage
from core.ai.llm.ollama_provider import OllamaProvider


class TestOllamaProvider:
    def test_init_defaults(self):
        provider = OllamaProvider()
        assert provider.provider_name == "ollama"
        assert provider.base_url == "http://localhost:11434"

    @patch("core.ai.llm.ollama_provider._get_httpx")
    def test_health_check_success(self, mock_get_httpx):
        mock_httpx = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_httpx.get.return_value = mock_resp
        mock_get_httpx.return_value = mock_httpx

        provider = OllamaProvider()
        assert provider.health_check() is True

    @patch("core.ai.llm.ollama_provider._get_httpx")
    def test_complete_success(self, mock_get_httpx):
        mock_httpx = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "model": "qwen3:4b",
            "message": {"content": "NVDA maintains a strong competitive moat in AI GPUs."},
            "prompt_eval_count": 15,
            "eval_count": 25,
            "done": True,
        }
        mock_httpx.post.return_value = mock_resp
        mock_get_httpx.return_value = mock_httpx

        provider = OllamaProvider()
        messages = [
            LLMMessage(role="system", content="You are a financial analyst."),
            LLMMessage(role="user", content="Analyze NVDA moat."),
        ]
        response = provider.complete(messages)

        assert response.content == "NVDA maintains a strong competitive moat in AI GPUs."
        assert response.usage["total_tokens"] == 40
        assert response.cost_usd == 0.0
