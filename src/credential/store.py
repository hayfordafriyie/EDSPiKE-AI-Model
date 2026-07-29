from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any


class CredentialStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_dir = Path(os.getenv("EDSPIKE_DATA_DIR", "~/.edspike")).expanduser()
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "credentials.db")
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                provider TEXT NOT NULL,
                key_name TEXT NOT NULL DEFAULT 'api_key',
                value TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (provider, key_name)
            )
        """)
        self._conn.commit()

    def set(self, provider: str, value: str, key_name: str = "api_key", metadata: dict | None = None) -> None:
        self._conn.execute(
            """INSERT INTO credentials (provider, key_name, value, metadata, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'))
               ON CONFLICT(provider, key_name) DO UPDATE SET
                   value = excluded.value,
                   metadata = excluded.metadata,
                   updated_at = datetime('now')""",
            (provider, key_name, value, json.dumps(metadata or {})),
        )
        self._conn.commit()

    def get(self, provider: str, key_name: str = "api_key") -> str | None:
        row = self._conn.execute(
            "SELECT value FROM credentials WHERE provider = ? AND key_name = ?",
            (provider, key_name),
        ).fetchone()
        return row[0] if row else None

    def delete(self, provider: str, key_name: str = "api_key") -> bool:
        cur = self._conn.execute(
            "DELETE FROM credentials WHERE provider = ? AND key_name = ?",
            (provider, key_name),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def list_providers(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT provider, key_name, metadata, created_at, updated_at FROM credentials ORDER BY provider"
        ).fetchall()
        return [
            {
                "provider": r[0],
                "key_name": r[1],
                "metadata": json.loads(r[2]),
                "configured": True,
                "created_at": r[3],
                "updated_at": r[4],
            }
            for r in rows
        ]

    def has(self, provider: str, key_name: str = "api_key") -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM credentials WHERE provider = ? AND key_name = ?",
            (provider, key_name),
        ).fetchone()
        return row is not None

    def resolve_api_key(self, provider: str, key_name: str = "api_key") -> str | None:
        key = self.get(provider, key_name)
        if key:
            return key
        env_key = f"{provider.upper()}_API_KEY"
        return os.environ.get(env_key) or None
