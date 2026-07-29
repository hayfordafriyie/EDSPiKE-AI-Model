import pytest

from src.compact import ContextCompressor


class TestCompact:
    def test_estimate_tokens(self):
        comp = ContextCompressor()
        tokens = comp.estimate_tokens("hello world")
        assert tokens > 0

    def test_needs_compression(self):
        comp = ContextCompressor(max_tokens=10)
        assert comp.needs_compression("this is a long text that exceeds limit")
        assert not comp.needs_compression("short")

    def test_compress_short_conversation(self):
        comp = ContextCompressor()
        msgs = [{"role": "user", "content": "hello"}]
        result = comp.compress(msgs)
        assert result.original_tokens > 0
        assert "hello" in result.summary

    def test_compress_long_conversation(self):
        comp = ContextCompressor(max_tokens=10)
        msgs = [{"role": "user", "content": "A" * 1000}]
        result = comp.compress(msgs)
        # Should be compressed
        assert len(result.summary) < 1000

    def test_compress_empty(self):
        comp = ContextCompressor()
        result = comp.compress([])
        assert result.summary == ""

    def test_summarize_session(self):
        comp = ContextCompressor()
        msgs = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        summary = comp.summarize_session(msgs)
        assert "hello" in summary
        assert "hi there" in summary

    def test_generate_title(self):
        comp = ContextCompressor()
        msgs = [{"role": "user", "content": "fix the login bug in the auth module"}]
        title = comp.generate_title(msgs)
        assert len(title) > 0
        assert "login" in title

    def test_generate_title_empty(self):
        comp = ContextCompressor()
        assert comp.generate_title([]) == "New Session"
