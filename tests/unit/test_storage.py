"""Tests for object storage — M15.5 Phase 5."""

from __future__ import annotations

import pytest

from core.storage.base import MockObjectStorage, LocalObjectStorage, StorageConfig, get_storage


@pytest.fixture
def mock_storage():
    return MockObjectStorage()


class TestMockObjectStorage:
    def test_put_and_get(self, mock_storage):
        obj = mock_storage.put("docs/test.pdf", b"PDF-CONTENT", content_type="application/pdf")
        assert obj.key == "docs/test.pdf"
        assert obj.size_bytes == 11
        assert obj.content_type == "application/pdf"

        content, meta = mock_storage.get("docs/test.pdf")
        assert content == b"PDF-CONTENT"
        assert meta.key == "docs/test.pdf"

    def test_get_missing(self, mock_storage):
        result = mock_storage.get("nonexistent")
        assert result is None

    def test_exists(self, mock_storage):
        mock_storage.put("a.txt", b"hello")
        assert mock_storage.exists("a.txt") is True
        assert mock_storage.exists("b.txt") is False

    def test_delete(self, mock_storage):
        mock_storage.put("a.txt", b"hello")
        assert mock_storage.delete("a.txt") is True
        assert mock_storage.exists("a.txt") is False
        assert mock_storage.delete("a.txt") is False

    def test_list_prefix(self, mock_storage):
        mock_storage.put("docs/a.pdf", b"a")
        mock_storage.put("docs/b.pdf", b"b")
        mock_storage.put("data/c.csv", b"c")

        results = mock_storage.list(prefix="docs")
        assert len(results) == 2

    def test_content_hash(self, mock_storage):
        obj1 = mock_storage.put("a.txt", b"hello")
        obj2 = mock_storage.put("b.txt", b"hello")
        assert obj1.content_hash == obj2.content_hash

    def test_presigned_url(self, mock_storage):
        mock_storage.put("a.txt", b"hello")
        url = mock_storage.get_presigned_url("a.txt")
        assert url == "mock://a.txt"

    def test_to_dict(self, mock_storage):
        obj = mock_storage.put("a.txt", b"hello", metadata={"source": "sec"})
        d = obj.to_dict()
        assert d["key"] == "a.txt"
        assert d["metadata"]["source"] == "sec"


class TestGetStorage:
    def test_mock_backend(self):
        storage = get_storage(StorageConfig(backend="mock"))
        assert isinstance(storage, MockObjectStorage)

    def test_local_backend(self, tmp_path):
        storage = get_storage(StorageConfig(backend="local", local_path=str(tmp_path)))
        assert isinstance(storage, LocalObjectStorage)

    def test_unknown_backend_falls_back(self):
        storage = get_storage(StorageConfig(backend="s3"))
        assert isinstance(storage, MockObjectStorage)


class TestLocalObjectStorage:
    def test_put_get_roundtrip(self, tmp_path):
        storage = LocalObjectStorage(StorageConfig(local_path=str(tmp_path)))
        storage.put("sub/file.txt", b"content")
        assert storage.exists("sub/file.txt")

        content, obj = storage.get("sub/file.txt")
        assert content == b"content"

    def test_list(self, tmp_path):
        storage = LocalObjectStorage(StorageConfig(local_path=str(tmp_path)))
        storage.put("x/1.txt", b"a")
        storage.put("x/2.txt", b"b")
        results = storage.list(prefix="x")
        assert len(results) == 2

    def test_delete(self, tmp_path):
        storage = LocalObjectStorage(StorageConfig(local_path=str(tmp_path)))
        storage.put("a.txt", b"hello")
        assert storage.delete("a.txt") is True
        assert storage.delete("a.txt") is False