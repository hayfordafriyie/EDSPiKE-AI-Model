from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class DataPreprocessor:
    def __init__(self, min_length: int = 20, max_length: int = 12000) -> None:
        self.min_length = min_length
        self.max_length = max_length

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r"\[(?:CITATION NEEDED|REDACTED)\]", "", str(text), flags=re.I)
        return re.sub(r"\s+", " ", text).strip()

    def process_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        if "question" in record and "answer" in record:
            instruction, output = record["question"], record["answer"]
            category = record.get("category", "education")
            context = record.get("context", "")
        elif "description" in record and "code" in record:
            language = record.get("language", "python")
            instruction = f"Write {language} code to: {record['description']}"
            output, context, category = record["code"], "", "coding"
        elif "messages" in record:
            turns = [
                f"{str(m.get('role', 'user')).upper()}: {m.get('content', '')}"
                for m in record["messages"]
            ]
            instruction, output, context, category = "Continue this conversation.", "\n".join(turns), "", "conversation"
        elif "text" in record:
            instruction = "Explain the following educational material."
            output, context, category = record["text"], "", record.get("category", "education")
        else:
            return None
        result = {
            "instruction": self.clean_text(instruction),
            "input": self.clean_text(context),
            "output": self.clean_text(output),
            "category": str(category),
            "source": str(record.get("source", "unknown")),
            "license": str(record.get("license", "internal")),
        }
        length = len(result["instruction"]) + len(result["input"]) + len(result["output"])
        return result if self.min_length <= length <= self.max_length else None

    def process_all_sources(self, raw_dir: str | Path, output_file: str | Path) -> int:
        seen: set[str] = set()
        processed: list[dict[str, Any]] = []
        for path in sorted(Path(raw_dir).glob("*.jsonl")):
            with path.open(encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    record = self.process_record(json.loads(line))
                    if not record:
                        continue
                    fingerprint = json.dumps(record, sort_keys=True, ensure_ascii=False)
                    if fingerprint not in seen:
                        seen.add(fingerprint)
                        processed.append(record)
        target = Path(output_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as stream:
            for record in processed:
                stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return len(processed)

