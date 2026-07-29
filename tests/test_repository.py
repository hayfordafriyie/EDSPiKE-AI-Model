import tempfile
from pathlib import Path

import pytest

from src.repository import RepositoryCache


class TestRepositoryCache:
    def test_add_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            cache.add("https://github.com/user/repo", "/tmp/repo", branch="main")
            entry = cache.get("https://github.com/user/repo")
            assert entry is not None
            assert entry.url == "https://github.com/user/repo"
            assert entry.branch == "main"

    def test_get_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            assert cache.get("https://nonexistent") is None

    def test_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            cache.add("https://github.com/user/repo", "/tmp/repo")
            assert cache.remove("https://github.com/user/repo") is True
            assert cache.remove("https://github.com/user/repo") is False

    def test_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            cache.add("url1", "/tmp/r1")
            cache.add("url2", "/tmp/r2")
            assert len(cache.list()) == 2

    def test_update_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            cache.add("url", "/tmp/r")
            cache.update_fetch("url", last_commit="abc123")
            entry = cache.get("url")
            assert entry.last_commit == "abc123"
            assert entry.last_fetch > 0

    def test_exists_at(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            cache.add("url", "/tmp/r")
            entry = cache.exists_at("/tmp/r")
            assert entry is not None
            assert cache.exists_at("/nonexistent") is None

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = str(Path(tmp) / "repos")
            cache1 = RepositoryCache(data_dir)
            cache1.add("url1", "/tmp/r1", meta={"key": "val"})
            cache2 = RepositoryCache(data_dir)
            assert len(cache2.list()) == 1
            assert cache2.get("url1").meta == {"key": "val"}

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = RepositoryCache(str(Path(tmp) / "repos"))
            cache.add("url", "/tmp/r")
            cache.clear()
            assert cache.list() == []
