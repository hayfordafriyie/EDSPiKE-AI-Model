from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class SessionStatus(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"
    ERROR = "error"


@dataclass
class SessionEvent:
    id: str = ""
    session_id: str = ""
    event_type: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class Session:
    id: str = ""
    agent_id: str = "default"
    provider: str = "local"
    model: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


class SessionStore:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_dir = Path(os.getenv("EDSPIKE_DATA_DIR", "~/.edspike"))
            db_dir = db_dir.expanduser()
            db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(db_dir / "sessions.db")
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL DEFAULT 'default',
                provider TEXT NOT NULL DEFAULT 'local',
                model TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                messages TEXT NOT NULL DEFAULT '[]',
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_events (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                data TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );
            CREATE INDEX IF NOT EXISTS idx_events_session ON session_events(session_id);
        """)
        self._conn.commit()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _new_id(self) -> str:
        return uuid.uuid4().hex[:16]

    def create_session(self, agent_id: str = "default", provider: str = "local", model: str = "", metadata: dict | None = None) -> Session:
        sid = self._new_id()
        now = self._now()
        session = Session(
            id=sid, agent_id=agent_id, provider=provider, model=model,
            status=SessionStatus.ACTIVE, messages=[], metadata=metadata or {},
            created_at=now, updated_at=now,
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO sessions (id, agent_id, provider, model, status, messages, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sid, agent_id, provider, model, "active", "[]", json.dumps(metadata or {}), now, now),
            )
            self._conn.commit()
        self._emit_event(sid, "session.created", {"session_id": sid})
        return session

    def get_session(self, session_id: str) -> Session | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[Session]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?", (limit, offset),
            ).fetchall()
        return [self._row_to_session(r) for r in rows]

    def append_message(self, session_id: str, role: str, content: str | list, metadata: dict | None = None) -> Session | None:
        session = self.get_session(session_id)
        if session is None:
            return None
        msg = {"role": role, "content": content, "metadata": metadata or {}}
        messages = session.messages + [msg]
        now = self._now()
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET messages = ?, updated_at = ? WHERE id = ?",
                (json.dumps(messages), now, session_id),
            )
            self._conn.commit()
        session.messages = messages
        session.updated_at = now
        self._emit_event(session_id, "message.added", {"role": role})
        return session

    def update_status(self, session_id: str, status: SessionStatus) -> bool:
        now = self._now()
        with self._lock:
            cur = self._conn.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now, session_id),
            )
            self._conn.commit()
        if cur.rowcount > 0:
            self._emit_event(session_id, "session.status_changed", {"status": status.value})
            return True
        return False

    def _emit_event(self, session_id: str, event_type: str, data: dict[str, Any]):
        eid = self._new_id()
        now = self._now()
        with self._lock:
            self._conn.execute(
                "INSERT INTO session_events (id, session_id, event_type, data, created_at) VALUES (?, ?, ?, ?, ?)",
                (eid, session_id, event_type, json.dumps(data), now),
            )
            self._conn.commit()

    def get_events(self, session_id: str, limit: int = 100) -> list[SessionEvent]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM session_events WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        results: list[SessionEvent] = []
        for row in rows:
            results.append(SessionEvent(
                id=row["id"], session_id=row["session_id"],
                event_type=row["event_type"], data=json.loads(row["data"]),
                created_at=row["created_at"],
            ))
        return results

    def get_event_stream(self, session_id: str, after_id: str | None = None) -> list[SessionEvent]:
        with self._lock:
            if after_id:
                row = self._conn.execute("SELECT created_at, id FROM session_events WHERE id = ?", (after_id,)).fetchone()
                if row is None:
                    return []
                rows = self._conn.execute(
                    "SELECT * FROM session_events WHERE session_id = ? AND (created_at, id) > (?, ?) ORDER BY created_at ASC, id ASC",
                    (session_id, row["created_at"], row["id"]),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM session_events WHERE session_id = ? ORDER BY created_at ASC, id ASC",
                    (session_id,),
                ).fetchall()
        return [
            SessionEvent(id=r["id"], session_id=r["session_id"], event_type=r["event_type"], data=json.loads(r["data"]), created_at=r["created_at"])
            for r in rows
        ]

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            self._conn.execute("DELETE FROM session_events WHERE session_id = ?", (session_id,))
            cur = self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            self._conn.commit()
        return cur.rowcount > 0

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> Session:
        return Session(
            id=row["id"], agent_id=row["agent_id"], provider=row["provider"],
            model=row["model"], status=SessionStatus(row["status"]),
            messages=json.loads(row["messages"]), metadata=json.loads(row["metadata"]),
            created_at=row["created_at"], updated_at=row["updated_at"],
        )
