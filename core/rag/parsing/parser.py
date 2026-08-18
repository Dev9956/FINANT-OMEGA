"""FININT OMEGA — Document parser: text extraction from mock sources."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    TEXT = "text"
    FILE = "file"
    URL = "url"
    MOCK = "mock"


class ParsedDocument(BaseModel):
    """Result of parsing a document."""

    source_id: str
    source_type: SourceType
    title: str = ""
    text: str
    metadata: dict = Field(default_factory=dict)
    page_count: int = 1


class DocumentParser:
    """Parse documents from various sources into plain text."""

    def __init__(self) -> None:
        self._parsers: dict[SourceType, callable] = {
            SourceType.TEXT: self._parse_text,
            SourceType.FILE: self._parse_file,
            SourceType.URL: self._parse_url,
            SourceType.MOCK: self._parse_mock,
        }

    def register_parser(self, source_type: SourceType, parser_fn: callable) -> None:
        self._parsers[source_type] = parser_fn

    def parse(self, source_id: str, source_type: SourceType, content: str = "", **kwargs) -> ParsedDocument:
        parser_fn = self._parsers.get(source_type, self._parse_text)
        return parser_fn(source_id, content, **kwargs)

    def _parse_text(self, source_id: str, content: str, **kwargs) -> ParsedDocument:
        return ParsedDocument(
            source_id=source_id,
            source_type=SourceType.TEXT,
            text=content,
            metadata=kwargs.get("metadata", {}),
        )

    def _parse_file(self, source_id: str, content: str, **kwargs) -> ParsedDocument:
        file_path = kwargs.get("file_path", "")
        allowed_dir = kwargs.get("allowed_dir", None)
        text = content
        if file_path:
            resolved = Path(file_path).resolve()
            if allowed_dir:
                allowed = Path(allowed_dir).resolve()
                if not str(resolved).startswith(str(allowed)):
                    raise ValueError(f"Path traversal denied: {file_path}")
            if resolved.exists() and resolved.is_file():
                text = resolved.read_text(encoding="utf-8")
        return ParsedDocument(
            source_id=source_id,
            source_type=SourceType.FILE,
            title=Path(file_path).name if file_path else "",
            text=text,
            metadata=kwargs.get("metadata", {}),
        )

    def _parse_url(self, source_id: str, content: str, **kwargs) -> ParsedDocument:
        return ParsedDocument(
            source_id=source_id,
            source_type=SourceType.URL,
            text=content,
            metadata={"url": kwargs.get("url", ""), **kwargs.get("metadata", {})},
        )

    def _parse_mock(self, source_id: str, content: str, **kwargs) -> ParsedDocument:
        return ParsedDocument(
            source_id=source_id,
            source_type=SourceType.MOCK,
            title=kwargs.get("title", f"Mock Document {source_id}"),
            text=content,
            metadata=kwargs.get("metadata", {}),
        )

    def parse_batch(self, items: list[dict]) -> list[ParsedDocument]:
        results = []
        for item in items:
            results.append(self.parse(
                source_id=item.get("source_id", ""),
                source_type=SourceType(item.get("source_type", "text")),
                content=item.get("content", ""),
                **{k: v for k, v in item.items() if k not in ("source_id", "source_type", "content")},
            ))
        return results
