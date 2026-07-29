import json

import pytest

from src.data_pipeline.collector import DataCollector
from src.data_pipeline.preprocessor import DataPreprocessor
from src.data_pipeline.splitter import DataSplitter


def test_collector_anonymizes_personal_data(tmp_path):
    collector = DataCollector(tmp_path, salt="test")
    record = collector.anonymize({
        "employee_id": "EMP123", "full_name": "John Doe", "score": 92,
    })
    assert record["employee_id"] != "EMP123"
    assert "full_name" not in record
    assert record["score"] == 92


def test_preprocessor_deduplicates(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    value = {"question": "What is our return policy?", "answer": "Our return policy is 30 days."}
    (raw / "a.jsonl").write_text("\n".join(json.dumps(value) for _ in range(2)), encoding="utf-8")
    output = tmp_path / "processed.jsonl"
    assert DataPreprocessor().process_all_sources(raw, output) == 1


def test_splitter_is_deterministic_and_complete(tmp_path):
    source = tmp_path / "data.jsonl"
    rows = [
        {"instruction": f"Question {i}", "input": "", "output": f"Answer {i}", "category": "general"}
        for i in range(20)
    ]
    source.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    counts = DataSplitter(seed=42).split(source, tmp_path / "splits")
    assert sum(counts.values()) == 20
    assert all(counts[name] > 0 for name in ("train", "val", "test"))


def test_bad_split_ratios_rejected(tmp_path):
    with pytest.raises(ValueError, match="total"):
        DataSplitter().split(tmp_path / "missing", tmp_path, 0.5, 0.5, 0.5)

