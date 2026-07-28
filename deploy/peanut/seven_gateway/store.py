from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .security import safe_json, sanitize


class GatewayStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._conn() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    csrf_hash TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_seen REAL NOT NULL,
                    expires_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_hash TEXT NOT NULL,
                    message TEXT NOT NULL,
                    reply TEXT,
                    status TEXT NOT NULL,
                    error_code TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_hash,id);
                CREATE TABLE IF NOT EXISTS activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )

    @contextmanager
    def _conn(self):
        with self._lock:
            db = sqlite3.connect(str(self.path), timeout=10)
            db.row_factory = sqlite3.Row
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()

    def health(self) -> bool:
        with self._conn() as db:
            return db.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    def create_session(self, token_hash: str, csrf_hash: str, ttl: int) -> None:
        now = time.time()
        with self._conn() as db:
            db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            db.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?)",
                (token_hash, csrf_hash, now, now, now + ttl),
            )

    def validate_session(
        self, token_hash: str, csrf_hash: str | None, idle_seconds: int, require_csrf: bool
    ) -> bool:
        now = time.time()
        with self._conn() as db:
            row = db.execute(
                "SELECT * FROM sessions WHERE token_hash=?", (token_hash,)
            ).fetchone()
            if not row:
                return False
            if row["expires_at"] <= now or row["last_seen"] + idle_seconds <= now:
                if row:
                    db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))
                return False
            if require_csrf and row["csrf_hash"] != csrf_hash:
                return False
            db.execute(
                "UPDATE sessions SET last_seen=? WHERE token_hash=?", (now, token_hash)
            )
            return True

    def destroy_session(self, token_hash: str) -> None:
        with self._conn() as db:
            db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))

    def rotate_csrf(self, token_hash: str, csrf_hash: str) -> bool:
        with self._conn() as db:
            cur = db.execute(
                "UPDATE sessions SET csrf_hash=?,last_seen=? WHERE token_hash=?",
                (csrf_hash, time.time(), token_hash),
            )
            return cur.rowcount == 1

    def create_turn(self, session_hash: str, message: str) -> int:
        now = time.time()
        with self._conn() as db:
            cur = db.execute(
                """INSERT INTO turns(session_hash,message,status,created_at,updated_at)
                   VALUES (?,?,'queued',?,?)""",
                (session_hash, message, now, now),
            )
            turn_id = int(cur.lastrowid)
        self.add_activity("turn_queued", {"turn_id": turn_id, "status": "queued"})
        return turn_id

    def update_turn(
        self, turn_id: int, status: str, reply: str | None = None, error_code: str | None = None
    ) -> None:
        with self._conn() as db:
            db.execute(
                """UPDATE turns SET status=?,reply=?,error_code=?,updated_at=? WHERE id=?""",
                (status, reply, error_code, time.time(), turn_id),
            )
        self.add_activity(
            "turn_status", {"turn_id": turn_id, "status": status, "error_code": error_code}
        )

    def get_turn(self, turn_id: int, session_hash: str) -> dict[str, Any] | None:
        with self._conn() as db:
            row = db.execute(
                """SELECT id,status,reply,error_code,created_at,updated_at
                   FROM turns WHERE id=? AND session_hash=?""",
                (turn_id, session_hash),
            ).fetchone()
        return dict(row) if row else None

    def get_turn_for_worker(self, turn_id: int) -> dict[str, Any] | None:
        with self._conn() as db:
            row = db.execute(
                "SELECT id,message,status FROM turns WHERE id=?", (turn_id,)
            ).fetchone()
        return dict(row) if row else None

    def add_activity(self, kind: str, payload: dict[str, Any]) -> int:
        now = time.time()
        with self._conn() as db:
            cur = db.execute(
                "INSERT INTO activity(kind,payload,created_at) VALUES (?,?,?)",
                (kind, safe_json(payload), now),
            )
            return int(cur.lastrowid)

    def activity_since(self, after_id: int, limit: int = 100) -> list[dict[str, Any]]:
        with self._conn() as db:
            rows = db.execute(
                """SELECT id,kind,payload,created_at FROM activity
                   WHERE id>? ORDER BY id LIMIT ?""",
                (max(0, after_id), max(1, min(limit, 100))),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "kind": row["kind"],
                "payload": sanitize(json.loads(row["payload"])),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
