from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ColumnType(str, Enum):
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BLOB = "BLOB"
    BOOLEAN = "INTEGER"
    JSON = "TEXT"
    DATETIME = "TEXT"


@dataclass
class Column:
    name: str
    type: ColumnType = ColumnType.TEXT
    primary_key: bool = False
    nullable: bool = True
    default: Any = None
    unique: bool = False
    foreign_key: str | None = None


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)

    def _schema(self) -> str:
        parts = []
        for col in self.columns:
            col_def = [f"    {col.name} {col.type.value}"]
            if col.primary_key:
                col_def.append("PRIMARY KEY")
            if not col.nullable:
                col_def.append("NOT NULL")
            if col.default is not None:
                if isinstance(col.default, str):
                    col_def.append(f"DEFAULT '{col.default}'")
                else:
                    col_def.append(f"DEFAULT {col.default}")
            if col.unique:
                col_def.append("UNIQUE")
            if col.foreign_key:
                col_def.append(f"REFERENCES {col.foreign_key}")
            parts.append(" ".join(col_def))
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n" + ",\n".join(parts) + "\n)"


@dataclass
class Migration:
    version: int
    description: str
    sql: str


class Database:
    def __init__(self, db_path: str):
        self._path = str(Path(db_path).expanduser().resolve())
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._schemas: dict[str, Table] = {}
        self._init_migrations()

    def _init_migrations(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def create_table(self, table: Table) -> None:
        self._schemas[table.name] = table
        with self._lock:
            self._conn.execute(table._schema())
            self._conn.commit()

    def insert(self, table: str, data: dict[str, Any]) -> int:
        cols = []
        vals = []
        for k, v in data.items():
            cols.append(k)
            if isinstance(v, (dict, list)):
                vals.append(json.dumps(v))
            else:
                vals.append(v)
        placeholders = ", ".join("?" for _ in cols)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        with self._lock:
            cur = self._conn.execute(sql, vals)
            self._conn.commit()
            return cur.lastrowid or 0

    def update(self, table: str, data: dict[str, Any], where: dict[str, Any]) -> int:
        set_clause = ", ".join(f"{k} = ?" for k in data)
        where_clause = " AND ".join(f"{k} = ?" for k in where)
        vals = list(data.values()) + list(where.values())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        with self._lock:
            cur = self._conn.execute(sql, vals)
            self._conn.commit()
            return cur.rowcount

    def delete(self, table: str, where: dict[str, Any]) -> int:
        where_clause = " AND ".join(f"{k} = ?" for k in where)
        sql = f"DELETE FROM {table} WHERE {where_clause}"
        with self._lock:
            cur = self._conn.execute(sql, list(where.values()))
            self._conn.commit()
            return cur.rowcount

    def _deserialize_row(self, row: dict[str, Any], table: str) -> dict[str, Any]:
        t = self._get_table_schema(table)
        if not t:
            return row
        result = dict(row)
        for col in t.columns:
            if col.type == ColumnType.JSON and isinstance(result.get(col.name), str):
                try:
                    result[col.name] = json.loads(result[col.name])
                except (json.JSONDecodeError, TypeError):
                    pass
        return result

    def _get_table_schema(self, table: str) -> Table | None:
        return self._schemas.get(table)

    def select(
        self,
        table: str,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        sql = f"SELECT * FROM {table}"
        params: list[Any] = []
        if where:
            sql += " WHERE " + " AND ".join(f"{k} = ?" for k in where)
            params = list(where.values())
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        if offset:
            sql += f" OFFSET {offset}"
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [self._deserialize_row(dict(r), table) for r in rows]

    def get(self, table: str, pk_value: Any, pk_name: str = "id") -> dict[str, Any] | None:
        rows = self.select(table, where={pk_name: pk_value}, limit=1)
        return rows[0] if rows else None

    def run_migration(self, migration: Migration) -> bool:
        with self._lock:
            existing = self._conn.execute(
                "SELECT 1 FROM _migrations WHERE version = ?", (migration.version,)
            ).fetchone()
            if existing:
                return False
            self._conn.executescript(migration.sql)
            self._conn.execute(
                "INSERT INTO _migrations (version, description) VALUES (?, ?)",
                (migration.version, migration.description),
            )
            self._conn.commit()
            logger.info("Applied migration %d: %s", migration.version, migration.description)
            return True

    def get_applied_migrations(self) -> list[dict[str, Any]]:
        return self.select("_migrations", order_by="version ASC")

    def close(self) -> None:
        self._conn.close()
