from pathlib import Path

import pytest

from src.memory import ActiveMemory


class TestActiveMemory:
    def test_remember_and_recall(self, tmp_path: Path):
        mem = ActiveMemory(str(tmp_path))
        mem.remember("The sky is blue", source="conversation", importance=0.8, tags=["fact"])
        results = mem.recall("sky")
        assert len(results) == 1
        assert results[0].content == "The sky is blue"

    def test_recall_by_tag(self, tmp_path: Path):
        mem = ActiveMemory(str(tmp_path))
        mem.remember("Important", tags=["critical"])
        results = mem.recall("critical")
        assert len(results) >= 1

    def test_forget(self, tmp_path: Path):
        mem = ActiveMemory(str(tmp_path))
        mem.remember("test")
        mem_id = mem.recall()[0].id
        assert mem.forget(mem_id) is True
        assert mem.forget("nonexistent") is False

    def test_update_importance(self, tmp_path: Path):
        mem = ActiveMemory(str(tmp_path))
        mem.remember("test", importance=0.5)
        mem_id = mem.recall()[0].id
        assert mem.update_importance(mem_id, 0.9) is True
        assert mem.update_importance("nonexistent", 0.9) is False

    def test_summarize(self, tmp_path: Path):
        mem = ActiveMemory(str(tmp_path))
        assert "No memories" in mem.summarize()
        mem.remember("Something important", importance=0.9)
        summary = mem.summarize()
        assert "Something" in summary

    def test_persistence(self, tmp_path: Path):
        data_dir = str(tmp_path / "memory")
        m1 = ActiveMemory(data_dir)
        m1.remember("persistent data")
        m2 = ActiveMemory(data_dir)
        assert len(m2.recall()) >= 1
