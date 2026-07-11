"""
Persistent memory for Seven Real.
SQLite: conversations, facts, goals, tasks, audit log of tool actions.
"""
from __future__ import annotations

import json
import hashlib
import re
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


_SENSITIVE_KEYS = re.compile(
    r"(?:password|passwd|passphrase|secret|token|api[_-]?key|authorization|cookie|private[_-]?key)",
    re.IGNORECASE,
)
_SENSITIVE_TEXT = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|password|passwd|secret)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"\b(?:sk|ghp|github_pat)_[A-Za-z0-9_\-]{12,}\b"),
]


def _redact_audit(value: Any, key: str = "") -> Any:
    if key and _SENSITIVE_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact_audit(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_audit(item) for item in value]
    if isinstance(value, str):
        text = value
        for pattern in _SENSITIVE_TEXT:
            if pattern.groups:
                text = pattern.sub(r"\1[REDACTED]", text)
            else:
                text = pattern.sub("[REDACTED]", text)
        return text
    return value


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
            conn.execute("PRAGMA foreign_keys=ON")
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
                CREATE TABLE IF NOT EXISTS beliefs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    stance TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    evidence TEXT,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_beliefs_topic ON beliefs(topic);
                CREATE TABLE IF NOT EXISTS working_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    kind TEXT DEFAULT 'item',
                    priority REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    steps_json TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    goal_id INTEGER,
                    steps_json TEXT NOT NULL,
                    current_step INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ref_type TEXT NOT NULL,
                    ref_id INTEGER,
                    text TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS digests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT NOT NULL UNIQUE,
                    text TEXT NOT NULL,
                    source_message_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    task_id INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(source_message_id) REFERENCES messages(id) ON DELETE SET NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
                );
                CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status, id);
                CREATE TABLE IF NOT EXISTS legacy_imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_sha256 TEXT NOT NULL UNIQUE,
                    source_path TEXT NOT NULL,
                    imported_at TEXT NOT NULL,
                    report_json TEXT NOT NULL
                );
                """
            )
            task_columns = {row["name"] for row in c.execute("PRAGMA table_info(tasks)").fetchall()}
            if "reminded_at" not in task_columns:
                c.execute("ALTER TABLE tasks ADD COLUMN reminded_at TEXT")
            if "reminder_attempts" not in task_columns:
                c.execute("ALTER TABLE tasks ADD COLUMN reminder_attempts INTEGER DEFAULT 0")
            action_columns = {row["name"] for row in c.execute("PRAGMA table_info(action_items)").fetchall()}
            if "source_kind" not in action_columns:
                c.execute("ALTER TABLE action_items ADD COLUMN source_kind TEXT")
            if "source_ref" not in action_columns:
                c.execute("ALTER TABLE action_items ADD COLUMN source_ref TEXT")
            c.execute("PRAGMA user_version=3")

    def schema_version(self) -> int:
        with self._conn() as c:
            return int(c.execute("PRAGMA user_version").fetchone()[0])

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

    # ── locally extracted action candidates ───────────────────────────

    @staticmethod
    def action_fingerprint(text: str) -> str:
        normalized = re.sub(r"\s+", " ", (text or "").strip().casefold())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def add_action_item(self, text: str, source_message_id: Optional[int] = None) -> Optional[int]:
        text = re.sub(r"\s+", " ", (text or "").strip())
        if not text:
            return None
        now = _utcnow()
        with self._conn() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO action_items(fingerprint,text,source_message_id,status,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                (self.action_fingerprint(text), text, source_message_id, "pending", now, now),
            )
            return int(cur.lastrowid) if cur.rowcount else None

    def list_action_items(self, status: str = "pending", limit: int = 30) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM action_items WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, max(1, min(int(limit), 200))),
            ).fetchall()
        return [dict(row) for row in rows]

    def resolve_action_item(self, item_id: int, accept: bool) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM action_items WHERE id=?", (int(item_id),)).fetchone()
            if not row or row["status"] != "pending":
                return None
            task_id = None
            status = "dismissed"
            if accept:
                now = _utcnow()
                cur = c.execute(
                    "INSERT INTO tasks(title,due_at,status,created_at,updated_at) VALUES (?,?,?,?,?)",
                    (row["text"], None, "open", now, now),
                )
                task_id = int(cur.lastrowid)
                status = "accepted"
            c.execute(
                "UPDATE action_items SET status=?,task_id=?,updated_at=? WHERE id=?",
                (status, task_id, _utcnow(), int(item_id)),
            )
            result = dict(row)
            result.update(status=status, task_id=task_id)
            return result

    def due_tasks(self, now: Optional[datetime] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Open, undelivered tasks with ISO due times at or before `now`."""
        now = now or datetime.now(timezone.utc)
        due: List[Dict[str, Any]] = []
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM tasks WHERE status='open' AND due_at IS NOT NULL AND reminded_at IS NULL ORDER BY id ASC"
            ).fetchall()
        for row in rows:
            raw = (row["due_at"] or "").strip()
            try:
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.astimezone()
                if parsed.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
                    due.append(dict(row))
            except (TypeError, ValueError):
                continue
            if len(due) >= limit:
                break
        return due

    def mark_task_reminded(self, task_id: int):
        with self._conn() as c:
            c.execute(
                "UPDATE tasks SET reminded_at=?, reminder_attempts=IFNULL(reminder_attempts,0)+1, updated_at=? WHERE id=?",
                (_utcnow(), _utcnow(), int(task_id)),
            )

    def record_reminder_attempt(self, task_id: int):
        with self._conn() as c:
            c.execute(
                "UPDATE tasks SET reminder_attempts=IFNULL(reminder_attempts,0)+1, updated_at=? WHERE id=?",
                (_utcnow(), int(task_id)),
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
        safe_arguments = _redact_audit(arguments or {})
        preview = str(_redact_audit((result or "")[:2000]))
        with self._conn() as c:
            c.execute(
                "INSERT INTO audit(tool, arguments, result_preview, ok, created_at) VALUES (?,?,?,?,?)",
                (tool, json.dumps(safe_arguments), preview, 1 if ok else 0, _utcnow()),
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

    # ── beliefs ────────────────────────────────────────────────────────

    def set_belief(self, topic: str, stance: str, confidence: float = 0.5,
                   evidence: str = "", source: str = "self") -> int:
        now = _utcnow()
        conf = max(0.0, min(1.0, float(confidence)))
        with self._conn() as c:
            row = c.execute(
                "SELECT id FROM beliefs WHERE topic=? ORDER BY id DESC LIMIT 1",
                (topic,),
            ).fetchone()
            if row:
                c.execute(
                    "UPDATE beliefs SET stance=?, confidence=?, evidence=?, source=?, updated_at=? WHERE id=?",
                    (stance, conf, evidence, source, now, row["id"]),
                )
                return int(row["id"])
            cur = c.execute(
                "INSERT INTO beliefs(topic, stance, confidence, evidence, source, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (topic, stance, conf, evidence, source, now, now),
            )
            return int(cur.lastrowid)

    def list_beliefs(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM beliefs ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def search_beliefs(self, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        q = f"%{query}%"
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM beliefs WHERE topic LIKE ? OR stance LIKE ? OR IFNULL(evidence,'') LIKE ? ORDER BY id DESC LIMIT ?",
                (q, q, q, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── working memory ─────────────────────────────────────────────────

    def wm_add(self, content: str, kind: str = "item", priority: float = 0.5) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO working_memory(content, kind, priority, created_at) VALUES (?,?,?,?)",
                (content, kind, float(priority), _utcnow()),
            )
            # keep ~9 items (7±2)
            c.execute(
                """DELETE FROM working_memory WHERE id NOT IN (
                    SELECT id FROM working_memory ORDER BY priority DESC, id DESC LIMIT 9
                )"""
            )
            return int(cur.lastrowid)

    def wm_list(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM working_memory ORDER BY priority DESC, id DESC LIMIT 9"
            ).fetchall()
        return [dict(r) for r in rows]

    def wm_clear(self):
        with self._conn() as c:
            c.execute("DELETE FROM working_memory")

    # ── skills ─────────────────────────────────────────────────────────

    def save_skill(self, name: str, description: str, steps: list) -> int:
        now = _utcnow()
        payload = json.dumps(steps, ensure_ascii=False)
        with self._conn() as c:
            row = c.execute("SELECT id FROM skills WHERE name=?", (name,)).fetchone()
            if row:
                c.execute(
                    "UPDATE skills SET description=?, steps_json=?, updated_at=? WHERE id=?",
                    (description, payload, now, row["id"]),
                )
                return int(row["id"])
            cur = c.execute(
                "INSERT INTO skills(name, description, steps_json, success_count, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (name, description, payload, 0, now, now),
            )
            return int(cur.lastrowid)

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM skills WHERE name=?", (name,)).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["steps"] = json.loads(d.get("steps_json") or "[]")
        except json.JSONDecodeError:
            d["steps"] = []
        return d

    def list_skills(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT id, name, description, success_count, updated_at FROM skills ORDER BY success_count DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def skill_success(self, name: str):
        with self._conn() as c:
            c.execute(
                "UPDATE skills SET success_count=success_count+1, updated_at=? WHERE name=?",
                (_utcnow(), name),
            )

    # ── plans ──────────────────────────────────────────────────────────

    def create_plan(self, title: str, steps: list, goal_id: Optional[int] = None) -> int:
        now = _utcnow()
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO plans(title, goal_id, steps_json, current_step, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (title, goal_id, json.dumps(steps, ensure_ascii=False), 0, "active", now, now),
            )
            return int(cur.lastrowid)

    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM plans WHERE id=?", (int(plan_id),)).fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["steps"] = json.loads(d.get("steps_json") or "[]")
        except json.JSONDecodeError:
            d["steps"] = []
        return d

    def active_plans(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM plans WHERE status='active' ORDER BY id DESC"
            ).fetchall()
        out = []
        for row in rows:
            d = dict(row)
            try:
                d["steps"] = json.loads(d.get("steps_json") or "[]")
            except json.JSONDecodeError:
                d["steps"] = []
            out.append(d)
        return out

    def advance_plan(self, plan_id: int, note: str = "") -> Optional[Dict[str, Any]]:
        plan = self.get_plan(plan_id)
        if not plan:
            return None
        steps = plan.get("steps") or []
        cur = int(plan.get("current_step") or 0)
        if cur < len(steps) and isinstance(steps[cur], dict):
            steps[cur]["done"] = True
            steps[cur]["result"] = (note or "")[:500]
        cur += 1
        status = "done" if cur >= len(steps) else "active"
        with self._conn() as c:
            c.execute(
                "UPDATE plans SET steps_json=?, current_step=?, status=?, updated_at=? WHERE id=?",
                (json.dumps(steps, ensure_ascii=False), cur, status, _utcnow(), int(plan_id)),
            )
        return self.get_plan(plan_id)

    # ── embeddings / digests / prefs ───────────────────────────────────

    def add_embedding(self, ref_type: str, ref_id: Optional[int], text: str, vector: list) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO embeddings(ref_type, ref_id, text, vector_json, created_at) VALUES (?,?,?,?,?)",
                (ref_type, ref_id, text, json.dumps(vector), _utcnow()),
            )
            return int(cur.lastrowid)

    def all_embeddings(self, limit: int = 500) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM embeddings ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            try:
                d["vector"] = json.loads(d.get("vector_json") or "[]")
            except json.JSONDecodeError:
                d["vector"] = []
            out.append(d)
        return out

    def add_digest(self, period: str, body: str) -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO digests(period, body, created_at) VALUES (?,?,?)",
                (period, body, _utcnow()),
            )
            return int(cur.lastrowid)

    def recent_digests(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM digests ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def set_preference(self, key: str, value: str):
        with self._conn() as c:
            c.execute(
                "INSERT INTO preferences(key, value, updated_at) VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, value, _utcnow()),
            )

    def get_preference(self, key: str, default: str = "") -> str:
        with self._conn() as c:
            row = c.execute("SELECT value FROM preferences WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def all_preferences(self) -> Dict[str, str]:
        with self._conn() as c:
            rows = c.execute("SELECT key, value FROM preferences").fetchall()
        return {r["key"]: r["value"] for r in rows}

    def context_block(self) -> str:
        """Compact context string for system prompt."""
        facts = self.all_facts(12)
        goals = self.active_goals()[:5]
        tasks = self.open_tasks()[:6]
        beliefs = self.list_beliefs(8)
        wm = self.wm_list()
        skills = self.list_skills(8)
        prefs = self.all_preferences()
        plans = self.active_plans()[:3]
        lines = []
        if prefs:
            lines.append("Preferences:")
            for k, v in list(prefs.items())[:10]:
                lines.append(f"  - {k}: {v}")
        if wm:
            lines.append("Working memory (active focus):")
            for w in wm:
                lines.append(f"  - [{w.get('kind')}] {w['content'][:120]}")
        if beliefs:
            lines.append("Beliefs / opinions:")
            for b in beliefs:
                lines.append(
                    f"  - {b['topic']}: {b['stance']} "
                    f"(conf={b.get('confidence', 0):.2f})"
                )
        if facts:
            lines.append("Known facts:")
            for f in facts:
                k = f.get("key") or ""
                lines.append(f"  - {k + ': ' if k else ''}{f['value']}")
        if goals:
            lines.append("Active goals:")
            for g in goals:
                lines.append(
                    f"  - [{g['id']}] {g['title']} ({g['progress']:.0f}%) "
                    f"last={g.get('last_action') or '-'}"
                )
        if plans:
            lines.append("Active multi-step plans:")
            for p in plans:
                steps = p.get("steps") or []
                cur = int(p.get("current_step") or 0)
                nxt = steps[cur] if cur < len(steps) else None
                lines.append(
                    f"  - plan[{p['id']}] {p['title']} step {cur}/{len(steps)} "
                    f"next={nxt.get('action') if isinstance(nxt, dict) else nxt}"
                )
        if tasks:
            lines.append("Open tasks:")
            for t in tasks:
                lines.append(
                    f"  - [{t['id']}] {t['title']}"
                    + (f" due={t['due_at']}" if t.get("due_at") else "")
                )
        if skills:
            lines.append("Known skills:")
            for s in skills:
                lines.append(f"  - {s['name']}: {s.get('description') or ''}")
        dig = self.recent_digests(2)
        if dig:
            lines.append("Recent digests:")
            for d in dig:
                lines.append(f"  - [{d['period']}] {d['body'][:160]}…")
        return "\n".join(lines) if lines else "No long-term facts/goals stored yet."
