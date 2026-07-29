from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT NOT NULL,
    response TEXT NOT NULL,
    score INTEGER CHECK(score BETWEEN 1 AND 5),
    corrected_response TEXT,
    domain TEXT DEFAULT 'general',
    created_at TEXT NOT NULL,
    trained BOOLEAN DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_feedback_trained ON feedback(trained);
CREATE INDEX IF NOT EXISTS idx_feedback_domain ON feedback(domain);
"""


class FeedbackCollector:
    def __init__(self, db_path: str | Path = "feedback.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(SCHEMA)
        logger.info("Feedback database ready at %s", self.db_path)

    def record(
        self,
        prompt: str,
        response: str,
        score: int | None = None,
        corrected_response: str | None = None,
        domain: str = "general",
    ) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                "INSERT INTO feedback (prompt, response, score, corrected_response, domain, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (prompt, response, score, corrected_response, domain, datetime.now(timezone.utc).isoformat()),
            )
            return cur.lastrowid

    def record_batch(self, records: list[dict[str, Any]]) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            data = [
                (
                    r["prompt"],
                    r["response"],
                    r.get("score"),
                    r.get("corrected_response"),
                    r.get("domain", "general"),
                    datetime.now(timezone.utc).isoformat(),
                )
                for r in records
            ]
            conn.executemany(
                "INSERT INTO feedback (prompt, response, score, corrected_response, domain, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                data,
            )
            return len(data)

    def untrained_count(self, domain: str | None = None) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            if domain:
                count = conn.execute(
                    "SELECT COUNT(*) FROM feedback WHERE trained = 0 AND domain = ?", (domain,)
                ).fetchone()[0]
            else:
                count = conn.execute("SELECT COUNT(*) FROM feedback WHERE trained = 0").fetchone()[0]
            return count

    def fetch_untrained(self, domain: str | None = None, limit: int = 1000) -> list[dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            if domain:
                rows = conn.execute(
                    "SELECT id, prompt, response, corrected_response, domain FROM feedback "
                    "WHERE trained = 0 AND domain = ? ORDER BY id LIMIT ?",
                    (domain, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, prompt, response, corrected_response, domain FROM feedback "
                    "WHERE trained = 0 ORDER BY id LIMIT ?",
                    (limit,),
                ).fetchall()
            return [
                {
                    "id": r[0],
                    "instruction": r[1],
                    "output": r[3] or r[2],
                    "domain": r[4],
                }
                for r in rows
            ]

    def mark_trained(self, ids: list[int]):
        with sqlite3.connect(str(self.db_path)) as conn:
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"UPDATE feedback SET trained = 1 WHERE id IN ({placeholders})", ids
            )

    def export_training_data(self, output_path: str | Path, domain: str | None = None):
        records = self.fetch_untrained(domain=domain, limit=100000)
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as stream:
            for rec in records:
                stream.write(json.dumps(rec, ensure_ascii=False) + "\n")
        logger.info("Exported %d training records to %s", len(records), output_path)
        return len(records)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Collect and manage feedback for continuous learning")
    parser.add_argument("--db", default="feedback.db", help="Path to feedback SQLite database")
    parser.add_argument("--export", type=str, help="Export untrained data to JSONL file")
    parser.add_argument("--domain", type=str, default=None, help="Filter by domain")
    args = parser.parse_args()
    collector = FeedbackCollector(args.db)
    if args.export:
        count = collector.export_training_data(args.export, args.domain)
        print(f"Exported {count} records to {args.export}")
    else:
        total = collector.untrained_count(args.domain)
        print(f"Untrained feedback records: {total}")


if __name__ == "__main__":
    main()
