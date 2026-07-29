from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    id: str
    path: str
    size_bytes: int = 0
    file_count: int = 0
    created_at: float = 0.0
    hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class SnapshotManager:
    def __init__(self, snapshots_dir: str | None = None):
        if snapshots_dir is None:
            snapshots_dir = str(Path(os.getenv("EDSPIKE_DATA_DIR", "~/.edspike")).expanduser() / "snapshots")
        self._dir = Path(snapshots_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "_index.json"
        self._index: dict[str, dict[str, Any]] = {}
        self._load_index()

    def _load_index(self) -> None:
        if self._index_path.exists():
            try:
                self._index = json.loads(self._index_path.read_text())
            except (json.JSONDecodeError, OSError):
                self._index = {}

    def _save_index(self) -> None:
        self._index_path.write_text(json.dumps(self._index, indent=2))

    def create(self, source_dir: str, name: str = "", metadata: dict | None = None) -> Snapshot:
        source = Path(source_dir).resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        snap_id = hashlib.md5(f"{source}:{time.time()}".encode()).hexdigest()[:16]
        snap_dir = self._dir / snap_id
        snap_dir.mkdir(parents=True, exist_ok=True)

        file_count = 0
        total_size = 0
        hasher = hashlib.sha256()

        for entry in source.rglob("*"):
            if entry.is_file():
                rel = entry.relative_to(source)
                target = snap_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry, target)
                file_count += 1
                size = entry.stat().st_size
                total_size += size
                hasher.update(entry.read_bytes())

        snap = Snapshot(
            id=snap_id,
            path=str(snap_dir),
            size_bytes=total_size,
            file_count=file_count,
            created_at=time.time(),
            hash=hasher.hexdigest(),
            metadata={"name": name or snap_id, **(metadata or {})},
        )
        self._index[snap_id] = {
            "id": snap_id,
            "path": snap.path,
            "size_bytes": snap.size_bytes,
            "file_count": snap.file_count,
            "created_at": snap.created_at,
            "hash": snap.hash,
            "metadata": snap.metadata,
        }
        self._save_index()
        logger.info("Created snapshot %s: %d files, %d bytes", snap_id, file_count, total_size)
        return snap

    def restore(self, snap_id: str, target_dir: str) -> bool:
        snap_data = self._index.get(snap_id)
        if not snap_data:
            raise ValueError(f"Snapshot not found: {snap_id}")
        source = Path(snap_data["path"])
        if not source.exists():
            raise FileNotFoundError(f"Snapshot data missing: {source}")
        target = Path(target_dir)
        target.mkdir(parents=True, exist_ok=True)
        for entry in source.rglob("*"):
            if entry.is_file():
                rel = entry.relative_to(source)
                dest = target / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry, dest)
        logger.info("Restored snapshot %s to %s", snap_id, target_dir)
        return True

    def delete(self, snap_id: str) -> bool:
        snap_data = self._index.pop(snap_id, None)
        if not snap_data:
            return False
        snap_dir = Path(snap_data["path"])
        if snap_dir.exists():
            shutil.rmtree(snap_dir)
        self._save_index()
        return True

    def list(self) -> list[dict[str, Any]]:
        return [
            {
                "id": sid,
                "name": data.get("metadata", {}).get("name", sid),
                "file_count": data.get("file_count", 0),
                "size_bytes": data.get("size_bytes", 0),
                "created_at": data.get("created_at", 0),
            }
            for sid, data in sorted(self._index.items(), key=lambda x: x[1].get("created_at", 0), reverse=True)
        ]

    def get(self, snap_id: str) -> dict[str, Any] | None:
        return self._index.get(snap_id)
