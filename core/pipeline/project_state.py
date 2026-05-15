"""
Project state — SQLite-backed resume tracker.
Tracks which pipeline stages have completed so interrupted renders can resume.
"""

import sqlite3
import os
import json
from datetime import datetime


class ProjectState:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS stages (
                name      TEXT PRIMARY KEY,
                status    TEXT DEFAULT 'pending',
                output    TEXT,
                updated   TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id        INTEGER PRIMARY KEY,
                stage     TEXT,
                status    TEXT DEFAULT 'pending',
                output    TEXT,
                updated   TEXT
            )
        """)
        self.conn.commit()

    def is_done(self, stage_name: str) -> bool:
        row = self.conn.execute(
            "SELECT status FROM stages WHERE name=?", (stage_name,)
        ).fetchone()
        return row is not None and row[0] == "done"

    def mark_done(self, stage_name: str, output: str = None):
        self.conn.execute("""
            INSERT OR REPLACE INTO stages (name, status, output, updated)
            VALUES (?, 'done', ?, ?)
        """, (stage_name, output, datetime.now().isoformat()))
        self.conn.commit()

    def mark_pending(self, stage_name: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO stages (name, status, updated)
            VALUES (?, 'pending', ?)
        """, (stage_name, datetime.now().isoformat()))
        self.conn.commit()

    def get_pending_chunks(self, stage: str) -> list[int]:
        rows = self.conn.execute(
            "SELECT id FROM chunks WHERE stage=? AND status='pending'", (stage,)
        ).fetchall()
        return [r[0] for r in rows]

    def mark_chunk_done(self, chunk_id: int, stage: str, output: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO chunks (id, stage, status, output, updated)
            VALUES (?, ?, 'done', ?, ?)
        """, (chunk_id, stage, output, datetime.now().isoformat()))
        self.conn.commit()

    def reset(self):
        self.conn.execute("DELETE FROM stages")
        self.conn.execute("DELETE FROM chunks")
        self.conn.commit()

    def summary(self) -> dict:
        stages = self.conn.execute("SELECT name, status FROM stages").fetchall()
        return {name: status for name, status in stages}

    def close(self):
        self.conn.close()
