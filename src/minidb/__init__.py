from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Document:
    id: str
    data: dict[str, Any] = field(default_factory=dict)


class MiniDB:
    def __init__(self, data_dir: str):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._docs: dict[str, Document] = {}
        self._wal: Path = self._data_dir / "wal.jsonl"
        self._snapshot: Path = self._data_dir / "snapshot.json"
        self._inverted_index: dict[str, set[str]] = defaultdict(set)
        self._load()

    def _load(self) -> None:
        if self._snapshot.exists():
            try:
                data = json.loads(self._snapshot.read_text())
                for item in data:
                    doc = Document(**item)
                    self._docs[doc.id] = doc
                    self._index_doc(doc)
            except Exception:
                pass

        if self._wal.exists():
            try:
                for line in self._wal.read_text().splitlines():
                    if line.strip():
                        entry = json.loads(line)
                        self._apply_wal_entry(entry)
            except Exception:
                pass

    def _save_snapshot(self) -> None:
        data = [{"id": d.id, "data": d.data} for d in self._docs.values()]
        self._snapshot.write_text(json.dumps(data, indent=2))

    def _append_wal(self, entry: dict[str, Any]) -> None:
        with self._wal.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    def _apply_wal_entry(self, entry: dict[str, Any]) -> None:
        op = entry.get("op")
        if op == "set":
            doc = Document(id=entry["id"], data=entry.get("data", {}))
            self._docs[doc.id] = doc
            self._index_doc(doc)
        elif op == "delete":
            self._docs.pop(entry["id"], None)
            self._rebuild_index()

    def _index_doc(self, doc: Document) -> None:
        text = json.dumps(doc.data).lower()
        words = re.findall(r"\w{2,}", text)
        for word in words:
            self._inverted_index[word].add(doc.id)

    def _rebuild_index(self) -> None:
        self._inverted_index.clear()
        for doc in self._docs.values():
            self._index_doc(doc)

    def set(self, id: str, data: dict[str, Any]) -> Document:
        doc = Document(id=id, data=data)
        entry = {"op": "set", "id": id, "data": data}
        self._apply_wal_entry(entry)
        self._append_wal(entry)
        return doc

    def get(self, id: str) -> dict[str, Any] | None:
        doc = self._docs.get(id)
        return doc.data if doc else None

    def delete(self, id: str) -> bool:
        if id not in self._docs:
            return False
        entry = {"op": "delete", "id": id}
        self._apply_wal_entry(entry)
        self._append_wal(entry)
        return True

    def search(self, query: str) -> list[dict[str, Any]]:
        words = re.findall(r"\w{2,}", query.lower())
        if not words:
            return self.list()
        matching: set[str] | None = None
        for word in words:
            ids = self._inverted_index.get(word, set())
            if matching is None:
                matching = set(ids)
            else:
                matching &= ids
        if matching is None:
            return []
        return [self._docs[doc_id].data for doc_id in sorted(matching) if doc_id in self._docs]

    def list(self) -> list[dict[str, Any]]:
        return [doc.data for doc in self._docs.values()]

    def count(self) -> int:
        return len(self._docs)

    def compact(self) -> None:
        self._save_snapshot()
        self._wal.write_text("")

    def clear(self) -> None:
        self._docs.clear()
        self._inverted_index.clear()
        self._save_snapshot()
        self._wal.write_text("")
