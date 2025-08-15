from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


class DataSplitter:
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed

    def split(
        self, input_file: str | Path, output_dir: str | Path,
        train_ratio: float = 0.8, val_ratio: float = 0.1, test_ratio: float = 0.1,
    ) -> dict[str, int]:
        if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-9:
            raise ValueError("Split ratios must total 1.0")
        with Path(input_file).open(encoding="utf-8") as stream:
            records = [json.loads(line) for line in stream if line.strip()]
        if len(records) < 3:
            raise ValueError("At least three records are required")
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            groups[str(record.get("category", "unknown"))].append(record)
        rng = random.Random(self.seed)
        splits = {"train": [], "val": [], "test": []}
        for group in groups.values():
            rng.shuffle(group)
            for index, record in enumerate(group):
                position = (index + 0.5) / len(group)
                name = "train" if position <= train_ratio else "val" if position <= train_ratio + val_ratio else "test"
                splits[name].append(record)
        self._rebalance_empty(splits)
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        for name, values in splits.items():
            rng.shuffle(values)
            with (target / f"{name}.jsonl").open("w", encoding="utf-8") as stream:
                for record in values:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {name: len(values) for name, values in splits.items()}

    @staticmethod
    def _rebalance_empty(splits: dict[str, list[dict[str, Any]]]) -> None:
        for name in ("val", "test"):
            if not splits[name] and len(splits["train"]) > 1:
                splits[name].append(splits["train"].pop())

