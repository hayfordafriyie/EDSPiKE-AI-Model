from __future__ import annotations

import csv
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {
    "email", "phone", "first_name", "last_name", "full_name", "address",
    "employee_id", "customer_id", "national_id", "passport", "ssn",
}


class DataCollector:
    """Collect local, licensed sources and anonymize operational records."""

    def __init__(self, raw_data_dir: str | Path = "data/raw", salt: str = "edspike") -> None:
        self.raw_dir = Path(raw_data_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.salt = salt

    def collect_directory(self, source_dir: str | Path) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in sorted(Path(source_dir).rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() == ".jsonl":
                records.extend(self._read_jsonl(path))
            elif path.suffix.lower() == ".json":
                value = json.loads(path.read_text(encoding="utf-8"))
                records.extend(value if isinstance(value, list) else [value])
            elif path.suffix.lower() == ".csv":
                with path.open(encoding="utf-8", newline="") as stream:
                    records.extend(dict(row) for row in csv.DictReader(stream))
            elif path.suffix.lower() in {".txt", ".md"}:
                records.append({"text": path.read_text(encoding="utf-8"), "source": path.name})
        return records

    def anonymize(self, record: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in record.items():
            normalized = key.lower()
            if normalized in SENSITIVE_KEYS:
                if normalized in {"employee_id", "customer_id", "national_id"} or normalized.endswith("_id"):
                    result[key] = self._hash(str(value))
                continue
            result[key] = value
        return result

    def save_raw_data(self, data: Iterable[dict[str, Any]], name: str) -> Path:
        output = self.raw_dir / f"{name}.jsonl"
        count = 0
        with output.open("w", encoding="utf-8") as stream:
            for record in data:
                stream.write(json.dumps(self.anonymize(record), ensure_ascii=False) + "\n")
                count += 1
        logger.info("Saved %d anonymized records to %s", count, output)
        return output

    def _hash(self, value: str) -> str:
        return hashlib.sha256(f"{self.salt}:{value}".encode()).hexdigest()[:20]

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        with path.open(encoding="utf-8") as stream:
            return [json.loads(line) for line in stream if line.strip()]

