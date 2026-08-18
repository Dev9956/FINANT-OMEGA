"""FININT OMEGA — RAG (Retrieval-Augmented Generation) module."""

from core.rag.parsing import DocumentParser
from core.rag.chunking import TextChunker
from core.rag.embeddings import MockEmbedder
from core.rag.retrieval import HybridRetriever
from core.rag.reranking import SimpleReranker
from core.rag.citations import CitationManager

__all__ = [
    "DocumentParser",
    "TextChunker",
    "MockEmbedder",
    "HybridRetriever",
    "SimpleReranker",
    "CitationManager",
]
