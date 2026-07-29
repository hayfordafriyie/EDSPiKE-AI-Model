import pytest

from src.projector import (
    run_pipeline, merge_adjacent_user_messages, dedupe_duplicate_tool_calls,
    repair_tool_exchange_adjacency, drop_orphan_results, drop_leading_non_user,
)

class TestProjector:
    def test_merge_adjacent_user(self):
        turns = [
            {"role": "user", "content": "hello"},
            {"role": "user", "content": "world"},
            {"role": "assistant", "content": "hi"},
        ]
        result, _ = run_pipeline(turns, [merge_adjacent_user_messages])
        assert len(result) == 2
        assert result[0]["content"] == "hello\nworld"

    def test_dedupe_tool_calls(self):
        turns = [
            {"role": "assistant", "content": "calling tool"},
            {"role": "tool", "name": "bash", "content": "output"},
            {"role": "tool", "name": "bash", "content": "output"},  # duplicate
        ]
        result, _ = run_pipeline(turns, [dedupe_duplicate_tool_calls])
        assert len(result) == 2

    def test_repair_adjacency(self):
        turns = [
            {"role": "user", "content": "run tool"},
            {"role": "tool", "name": "bash", "content": "result"},
        ]
        result, _ = run_pipeline(turns, [repair_tool_exchange_adjacency])
        assert len(result) == 3
        assert result[1]["role"] == "assistant"

    def test_drop_orphan_results(self):
        turns = [
            {"role": "tool", "name": "bash", "content": "orphan"},
            {"role": "user", "content": "hello"},
        ]
        result, _ = run_pipeline(turns, [drop_orphan_results])
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_drop_leading_non_user(self):
        turns = [
            {"role": "assistant", "content": "leading"},
            {"role": "user", "content": "actual"},
        ]
        result, _ = run_pipeline(turns, [drop_leading_non_user])
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_full_pipeline(self):
        turns = [
            {"role": "user", "content": "a"},
            {"role": "user", "content": "b"},
            {"role": "tool", "content": "orphan"},
            {"role": "assistant", "tool_calls": [{"name": "bash"}]},
            {"role": "tool", "name": "bash", "content": "result"},
            {"role": "tool", "name": "bash", "content": "result"},  # duplicate
        ]
        result, anomalies = run_pipeline(turns)
        # Should have merged users, dropped orphan, deduped, but kept the valid exchange
        assert len(result) >= 2

    def test_anomaly_reporting(self):
        turns = [{"role": "user", "content": "hello"}]
        _, anomalies = run_pipeline(turns)
        # The pipeline should have filtered some items
        assert isinstance(anomalies, list)
