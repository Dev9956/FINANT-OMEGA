"""FININT OMEGA — Text chunking: fixed-size and sentence-based splitting."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel


class Chunk(BaseModel):
    """A single text chunk."""

    chunk_id: str = ""
    text: str
    index: int = 0
    source_id: str = ""
    start_char: int = 0
    end_char: int = 0
    metadata: dict = field(default_factory=dict)


class TextChunker:
    """Split text into chunks using fixed-size or sentence-based strategies."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50, strategy: str = "fixed") -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy

    def chunk_fixed(self, text: str, source_id: str = "") -> list[Chunk]:
        chunks: list[Chunk] = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end]
            chunks.append(Chunk(
                chunk_id=f"{source_id}_chunk_{idx}",
                text=chunk_text,
                index=idx,
                source_id=source_id,
                start_char=start,
                end_char=end,
            ))
            start += self.chunk_size - self.overlap
            idx += 1
        return chunks

    def _split_sentences(self, text: str) -> list[str]:
        sentences: list[str] = []
        current = ""
        for char in text:
            current += char
            if char in ".!?\n":
                stripped = current.strip()
                if stripped:
                    sentences.append(stripped)
                current = ""
        if current.strip():
            sentences.append(current.strip())
        return sentences

    def chunk_sentences(self, text: str, source_id: str = "") -> list[Chunk]:
        sentences = self._split_sentences(text)
        chunks: list[Chunk] = []
        current_chunk = ""
        idx = 0
        char_offset = 0
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size and current_chunk:
                chunks.append(Chunk(
                    chunk_id=f"{source_id}_chunk_{idx}",
                    text=current_chunk.strip(),
                    index=idx,
                    source_id=source_id,
                    start_char=char_offset - len(current_chunk),
                    end_char=char_offset,
                ))
                idx += 1
                overlap_text = current_chunk[-self.overlap:] if self.overlap else ""
                current_chunk = overlap_text + " " + sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            char_offset += len(sentence) + 1
        if current_chunk.strip():
            chunks.append(Chunk(
                chunk_id=f"{source_id}_chunk_{idx}",
                text=current_chunk.strip(),
                index=idx,
                source_id=source_id,
                start_char=char_offset - len(current_chunk),
                end_char=char_offset,
            ))
        return chunks

    def chunk(self, text: str, source_id: str = "") -> list[Chunk]:
        if self.strategy == "sentence":
            return self.chunk_sentences(text, source_id)
        return self.chunk_fixed(text, source_id)
