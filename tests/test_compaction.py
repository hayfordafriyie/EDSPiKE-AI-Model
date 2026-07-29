import pytest

from src.compaction import DefaultCompactor, CompactResult


class TestCompaction:
    def test_no_compact_needed(self):
        comp = DefaultCompactor(max_context_tokens=100000)
        turns = [{"role": "user", "content": "hello"}]
        result = comp.compact(turns)
        assert result.ratio == 1.0

    def test_should_compact(self):
        comp = DefaultCompactor(max_context_tokens=100, threshold=0.5, reserve_tokens=10)
        assert comp.should_compact(60) is True
        assert comp.should_compact(30) is False

    def test_compact_large_context(self):
        comp = DefaultCompactor(max_context_tokens=100)
        turns = [{"role": "user", "content": "A" * 500} for _ in range(20)]
        result = comp.compact(turns)
        assert result.compressed_tokens < result.original_tokens

    def test_estimate_tokens(self):
        comp = DefaultCompactor()
        assert comp.estimate_tokens("hello world") > 0

    def test_simple_compress(self):
        comp = DefaultCompactor(max_context_tokens=50)
        turns = [{"role": "user", "content": "test " * 100}]
        result = comp.compact(turns)
        assert result.summary is not None

    def test_custom_provider(self):
        comp = DefaultCompactor(max_context_tokens=10)
        comp.set_provider(lambda msgs: "custom summary")
        turns = [{"role": "user", "content": "A" * 100}]
        result = comp.compact(turns)
        assert "custom summary" in result.summary
