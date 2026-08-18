"""FININT OMEGA — Embedding providers with real and mock options."""

from __future__ import annotations

import hashlib
import importlib
import math
import os
from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger()

# Lazy imports
_openai = None


def _get_openai():
    global _openai
    if _openai is None:
        try:
            _openai = importlib.import_module("openai")
        except ImportError:
            raise ImportError("openai is required. Install with: pip install openai")
    return _openai


class BaseEmbedder(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Embed a single text."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        ...

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...


class OpenAIEmbedder(BaseEmbedder):
    """Real embeddings using OpenAI API.

    Supports text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002.
    """

    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = None
        self._dimension = self.MODEL_DIMENSIONS.get(model, 1536)

    def _get_client(self):
        if self._client is None:
            openai_mod = _get_openai()
            kwargs: dict[str, Any] = {}
            if self._api_key:
                kwargs["api_key"] = self._api_key
            self._client = openai_mod.OpenAI(**kwargs)
        return self._client

    def embed(self, text: str) -> list[float]:
        """Embed a single text."""
        client = self._get_client()
        response = client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
        client = self._get_client()
        response = client.embeddings.create(
            model=self._model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbedder(BaseEmbedder):
    """Deterministic mock embedding using hash-based pseudo-embeddings for development."""

    def __init__(self, dim: int = 128) -> None:
        self._dim = dim

    def _text_to_seed(self, text: str) -> int:
        return int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)

    def _seeded_random(self, seed: int, idx: int) -> float:
        val = math.sin(seed * 0.1 + idx * 0.01) * 10000
        return val - math.floor(val)

    def embed(self, text: str) -> list[float]:
        seed = self._text_to_seed(text)
        vec = [self._seeded_random(seed, i) * 2 - 1 for i in range(self._dim)]
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    @property
    def dimension(self) -> int:
        return self._dim


def get_embedder(use_real: bool = True) -> BaseEmbedder:
    """Get the appropriate embedder based on configuration.

    Args:
        use_real: If True, use OpenAI embeddings (requires API key).
                 If False, use mock embeddings for development.
    """
    if use_real and os.environ.get("OPENAI_API_KEY"):
        try:
            return OpenAIEmbedder()
        except Exception as e:
            logger.warning("openai_embedder_fallback", error=str(e))
            return MockEmbedder()
    return MockEmbedder()
