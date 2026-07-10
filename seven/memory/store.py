"""
Persistent memory for Seven Real.
SQLite: conversations, facts, goals, tasks, audit log of tool actions.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from seven import config


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Memory:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    @contextmanager
    def _conn(self):
        with self._lock:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def _init_db(self):
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT,
                    value TEXT NOT NULL,
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key);
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    detail TEXT,
                    status TEXT DEFAULT 'active',
                    progress REAL DEFAULT 0,
                    last_action TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_at TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool TEXT NOT NULL,
                    arguments TEXT,
                    result_preview TEXT,
                    ok INTEGER,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
                    value, key, content='facts', content_rowid='id'
                );
                """
            )

    # ── conversation ───────────────────────────────────────────────────

    def add_message(self, role: str, content: str, meta: Optional[dict] = None) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO messages(role, content, meta, created_at) VALUES (?,?,?,?)",
                (role, content, json.dumps(meta or {}), _utcnow()),
            )
            return int(cur.lastrowid)

    def recent_messages(self, limit: int = 40) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT role, content, meta, created_at FROM messages ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        out = []
        for r in reversed(rows):
            out.append({
                "role": r["role"],
                "content": r["content"],
                "meta": json.loads(r["meta"] or "{}"),
                "created_at": r["created_at"],
            })
        return out

    def clear_session_messages(self):
        """Clear chat history but keep facts/goals/tasks."""
        with self._conn() as c:
            c.execute("DELETE FROM messages")

    def message_count(self) -> int:
        with self._conn() as c:
            row = c.execute("SELECT COUNT(*) AS n FROM messages").fetchone()
            return int(row["n"] if row else 0)

    def compact_history(self, keep_recent: int = 12, max_summary_chars: int = 1500) -> Optional[str]:
        """
        Fold older chat turns into a single memory fact and delete them.
        Keeps the latest `keep_recent` messages intact.
        Returns summary text if compaction ran, else None.
        """
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, role, content FROM messages ORDER BY id ASC"
            ).fetchall()
            if len(rows) <= keep_recent + 4:
                return None
            old = rows[: len(rows) - keep_recent]
            keep_ids = {r["id"] for r in rows[len(rows) - keep_recent :]}
            bits = []
            for r in old:
                role = r["role"]
                content = (r["content"] or "").replace("\n", " ").strip()
                if len(content) > 200:
                    content = content[:200] + "…"
                bits.append(f"{role}: {content}")
            summary = " | ".join(bits)
            if len(summary) > max_summary_chars:
                summary = summary[:max_summary_chars] + "…"
            now = _utcnow()
            c.execute(
                "INSERT INTO facts(key, value, source, confidence, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                ("session.compact", summary, "compaction", 0.7, now, now),
            )
            old_ids = [r["id"] for r in old if r["id"] not in keep_ids]
            if old_ids:
                placeholders = ",".join("?" * len(old_ids))
                c.execute(f"DELETE FROM messages WHERE id IN ({placeholders})", old_ids)
            return summary

    # ── facts ──────────────────────────────────────────────────────────

    def remember(self, value: str, key: Optional[str] = None, source: str = "chat", confidence: float = 1.0):
        now = _utcnow()
        with self._conn() as c:
            c.execute(
                "INSERT INTO facts(key, value, source, confidence, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (key, value, source, confidence, now, now),
            )
            # keep FTS roughly in sync (simple rebuild on insert for small DBs)
            try:
                c.execute("INSERT INTO facts_fts(rowid, value, key) VALUES (last_insert_rowid(), ?, ?)", (value, key or ""))
            except sqlite3.OperationalError:
                pass

    def search_facts(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        with self._conn() as c:
            rows = c.execute(
                """
                SELECT id, key, value, source, confidence, created_at
                FROM facts
                WHERE value LIKE ? OR IFNULL(key,'') LIKE ?
                ORDER BY id DESC LIMIT ?
                """,
                (q, q, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def all_facts(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, key, value, source, confidence FROM facts ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── goals / tasks ──────────────────────────────────────────────────

    def add_goal(self, title: str, detail: str = "") -> int:
        now = _utcnow()
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO goals(title, detail, status, progress, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (title, detail, "active", 0.0, now, now),
            )
            return int(cur.lastrowid)

    def update_goal(self, goal_id: int, progress: Optional[float] = None, status: Optional[str] = None, last_action: Optional[str] = None):
        with self._conn() as c:
            row = c.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
            if not row:
                return
            progress = row["progress"] if progress is None else progress
            status = row["status"] if status is None else status
            last_action = row["last_action"] if last_action is None else last_action
            c.execute(
                "UPDATE goals SET progress=?, status=?, last_action=?, updated_at=? WHERE id=?",
                (progress, status, last_action, _utcnow(), goal_id),
            )

    def active_goals(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM goals WHERE status='active' ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_goal(self, goal_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM goals WHERE id=?", (int(goal_id),)).fetchone()
        return dict(row) if row else None

    def add_task(self, title: str, due_at: Optional[str] = None) -> int:
        now = _utcnow()
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO tasks(title, due_at, status, created_at, updated_at) VALUES (?,?,?,?,?)",
                (title, due_at, "open", now, now),
            )
            return int(cur.lastrowid)

    def open_tasks(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM tasks WHERE status='open' ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def complete_task(self, task_id: int):
        with self._conn() as c:
            c.execute(
                "UPDATE tasks SET status='done', updated_at=? WHERE id=?",
                (_utcnow(), task_id),
            )

    # ── notes / audit ──────────────────────────────────────────────────

    def add_note(self, body: str, title: str = "") -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO notes(title, body, created_at) VALUES (?,?,?)",
                (title, body, _utcnow()),
            )
            return int(cur.lastrowid)

    def list_notes(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def audit(self, tool: str, arguments: dict, result: str, ok: bool):
        preview = (result or "")[:2000]
        with self._conn() as c:
            c.execute(
                "INSERT INTO audit(tool, arguments, result_preview, ok, created_at) VALUES (?,?,?,?,?)",
                (tool, json.dumps(arguments or {}), preview, 1 if ok else 0, _utcnow()),
            )

    def recent_audit(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def audits_since(self, after_id: int) -> List[Dict[str, Any]]:
        """Audit rows with id > after_id, oldest first."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM audit WHERE id > ? ORDER BY id ASC",
                (int(after_id),),
            ).fetchall()
        return [dict(r) for r in rows]

    def context_block(self) -> str:
        """Compact context string for system prompt."""
        facts = self.all_facts(15)
        goals = self.active_goals()[:5]
        tasks = self.open_tasks()[:8]
        lines = []
        if facts:
            lines.append("Known facts:")
            for f in facts:
                k = f.get("key") or ""
                lines.append(f"  - {k + ': ' if k else ''}{f['value']}")
        if goals:
            lines.append("Active goals:")
            for g in goals:
                lines.append(f"  - [{g['id']}] {g['title']} ({g['progress']:.0f}%) last={g.get('last_action') or '-'}")
        if tasks:
            lines.append("Open tasks:")
            for t in tasks:
                lines.append(f"  - [{t['id']}] {t['title']}" + (f" due={t['due_at']}" if t.get("due_at") else ""))
        return "\n".join(lines) if lines else "No long-term facts/goals stored yet."
