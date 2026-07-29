from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class SQLiteStore:
    def __init__(self, db_path: str):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init()

    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self._path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init(self) -> None:
        with self._lock:
            conn = self._conn()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS store (
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    created_at REAL NOT NULL DEFAULT (julianday('now')),
                    updated_at REAL NOT NULL DEFAULT (julianday('now')),
                    PRIMARY KEY (key, namespace)
                );
                CREATE TABLE IF NOT EXISTS kv_json (
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    namespace TEXT NOT NULL DEFAULT 'default',
                    PRIMARY KEY (key, namespace)
                );
            """)
            conn.commit()

    def set(self, key: str, value: str, namespace: str = "default") -> None:
        with self._lock:
            self._conn().execute(
                "INSERT INTO store (key, value, namespace) VALUES (?, ?, ?) "
                "ON CONFLICT(key, namespace) DO UPDATE SET value=excluded.value, updated_at=julianday('now')",
                (key, value, namespace),
            )
            self._conn().commit()

    def get(self, key: str, namespace: str = "default") -> str | None:
        row = self._conn().execute(
            "SELECT value FROM store WHERE key=? AND namespace=?", (key, namespace)
        ).fetchone()
        return row[0] if row else None

    def delete(self, key: str, namespace: str = "default") -> bool:
        with self._lock:
            cursor = self._conn().execute(
                "DELETE FROM store WHERE key=? AND namespace=?", (key, namespace)
            )
            self._conn().commit()
            return cursor.rowcount > 0

    def set_json(self, key: str, value: Any, namespace: str = "default") -> None:
        self.set(key, json.dumps(value), namespace)

    def get_json(self, key: str, namespace: str = "default") -> Any | None:
        val = self.get(key, namespace)
        return json.loads(val) if val else None

    def list_namespace(self, namespace: str) -> list[tuple[str, str]]:
        rows = self._conn().execute(
            "SELECT key, value FROM store WHERE namespace=? ORDER BY key", (namespace,)
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def count(self, namespace: str = "") -> int:
        if namespace:
            row = self._conn().execute("SELECT COUNT(*) FROM store WHERE namespace=?", (namespace,)).fetchone()
        else:
            row = self._conn().execute("SELECT COUNT(*) FROM store").fetchone()
        return row[0] if row else 0

    def clear_namespace(self, namespace: str) -> None:
        with self._lock:
            self._conn().execute("DELETE FROM store WHERE namespace=?", (namespace,))
            self._conn().commit()

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
