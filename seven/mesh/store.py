"""Private SQLite state for Seven Mesh peers, relays, and local messages."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MeshStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init()

    @contextmanager
    def _conn(self):
        with self._lock:
            connection = sqlite3.connect(str(self.path), check_same_thread=False)
            connection.row_factory = sqlite3.Row
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def _init(self) -> None:
        with self._conn() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS peers (
                    node_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    endpoint TEXT NOT NULL DEFAULT '',
                    capabilities_json TEXT NOT NULL DEFAULT '[]',
                    source TEXT NOT NULL,
                    last_seen_epoch INTEGER NOT NULL,
                    last_seen_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mesh_peers_seen
                    ON peers(last_seen_epoch DESC);
                CREATE TABLE IF NOT EXISTS request_nonces (
                    nonce TEXT PRIMARY KEY,
                    seen_epoch INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mesh_nonces_seen
                    ON request_nonces(seen_epoch);
                CREATE TABLE IF NOT EXISTS relay_messages (
                    message_id TEXT PRIMARY KEY,
                    sender_node_id TEXT NOT NULL,
                    target_node_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    expires_epoch INTEGER NOT NULL,
                    delivered_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_mesh_relay_target
                    ON relay_messages(target_node_id, delivered_at, expires_epoch);
                CREATE TABLE IF NOT EXISTS local_messages (
                    message_id TEXT PRIMARY KEY,
                    direction TEXT NOT NULL,
                    peer_node_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL,
                    context_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mesh_local_direction
                    ON local_messages(direction, status, created_at DESC);
                PRAGMA user_version=1;
                """
            )

    def integrity_check(self) -> str:
        with self._conn() as connection:
            return str(connection.execute("PRAGMA integrity_check").fetchone()[0])

    def claim_nonce(self, nonce: str, seen_epoch: int) -> bool:
        cutoff = int(seen_epoch) - 900
        with self._conn() as connection:
            connection.execute(
                "DELETE FROM request_nonces WHERE seen_epoch < ?", (cutoff,)
            )
            try:
                connection.execute(
                    "INSERT INTO request_nonces(nonce,seen_epoch) VALUES (?,?)",
                    (str(nonce), int(seen_epoch)),
                )
            except sqlite3.IntegrityError:
                return False
        return True

    def upsert_peer(self, peer: dict[str, Any], *, source: str) -> None:
        node_id = str(peer["node_id"])
        now = int(time.time())
        capabilities = peer.get("capabilities")
        if not isinstance(capabilities, list):
            capabilities = []
        with self._conn() as connection:
            connection.execute(
                """
                INSERT INTO peers(
                    node_id,name,hostname,platform,endpoint,capabilities_json,
                    source,last_seen_epoch,last_seen_at
                ) VALUES (?,?,?,?,?,?,?,?,?)
                ON CONFLICT(node_id) DO UPDATE SET
                    name=excluded.name,
                    hostname=excluded.hostname,
                    platform=excluded.platform,
                    endpoint=excluded.endpoint,
                    capabilities_json=excluded.capabilities_json,
                    source=excluded.source,
                    last_seen_epoch=excluded.last_seen_epoch,
                    last_seen_at=excluded.last_seen_at
                """,
                (
                    node_id,
                    str(peer.get("name") or "Seven")[:120],
                    str(peer.get("hostname") or "")[:255],
                    str(peer.get("platform") or "")[:120],
                    str(peer.get("endpoint") or "")[:2048],
                    json.dumps([str(value)[:120] for value in capabilities[:64]]),
                    str(source)[:32],
                    now,
                    _utcnow(),
                ),
            )

    def peers(self, *, online_seconds: int = 180, include_offline: bool = True) -> list[dict]:
        cutoff = int(time.time()) - max(1, int(online_seconds))
        query = "SELECT * FROM peers"
        arguments: tuple[Any, ...] = ()
        if not include_offline:
            query += " WHERE last_seen_epoch >= ?"
            arguments = (cutoff,)
        query += " ORDER BY last_seen_epoch DESC, name COLLATE NOCASE"
        with self._conn() as connection:
            rows = connection.execute(query, arguments).fetchall()
        peers: list[dict] = []
        for row in rows:
            item = dict(row)
            item["capabilities"] = json.loads(item.pop("capabilities_json") or "[]")
            item["online"] = int(item["last_seen_epoch"]) >= cutoff
            peers.append(item)
        return peers

    def queue_relay(self, message: dict[str, Any], *, ttl_seconds: int) -> None:
        now = int(time.time())
        with self._conn() as connection:
            connection.execute(
                """
                INSERT INTO relay_messages(
                    message_id,sender_node_id,target_node_id,kind,content,
                    context_json,created_at,expires_epoch,delivered_at
                ) VALUES (?,?,?,?,?,?,?,?,NULL)
                """,
                (
                    str(message["message_id"]),
                    str(message["sender_node_id"]),
                    str(message["target_node_id"]),
                    str(message.get("kind") or "message")[:64],
                    str(message.get("content") or "")[:16000],
                    json.dumps(message.get("context") or {}, ensure_ascii=False),
                    str(message.get("created_at") or _utcnow()),
                    now + max(60, min(int(ttl_seconds), 604800)),
                ),
            )

    def take_relay(self, target_node_id: str, *, limit: int = 50) -> list[dict]:
        now = int(time.time())
        with self._conn() as connection:
            connection.execute(
                "DELETE FROM relay_messages WHERE expires_epoch < ?", (now,)
            )
            rows = connection.execute(
                """
                SELECT * FROM relay_messages
                WHERE target_node_id=? AND delivered_at IS NULL
                ORDER BY created_at LIMIT ?
                """,
                (str(target_node_id), max(1, min(int(limit), 100))),
            ).fetchall()
            delivered_at = _utcnow()
            if rows:
                connection.executemany(
                    "UPDATE relay_messages SET delivered_at=? WHERE message_id=?",
                    [(delivered_at, row["message_id"]) for row in rows],
                )
        output: list[dict] = []
        for row in rows:
            item = dict(row)
            item["context"] = json.loads(item.pop("context_json") or "{}")
            item.pop("expires_epoch", None)
            item["delivered_at"] = delivered_at
            output.append(item)
        return output

    def record_local(
        self,
        message: dict[str, Any],
        *,
        direction: str,
        peer_node_id: str,
        status: str,
    ) -> bool:
        try:
            with self._conn() as connection:
                connection.execute(
                    """
                    INSERT INTO local_messages(
                        message_id,direction,peer_node_id,kind,content,
                        context_json,created_at,status
                    ) VALUES (?,?,?,?,?,?,?,?)
                    """,
                    (
                        str(message["message_id"]),
                        str(direction),
                        str(peer_node_id),
                        str(message.get("kind") or "message")[:64],
                        str(message.get("content") or "")[:16000],
                        json.dumps(message.get("context") or {}, ensure_ascii=False),
                        str(message.get("created_at") or _utcnow()),
                        str(status),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def local_messages(
        self,
        *,
        direction: str | None = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[dict]:
        clauses: list[str] = []
        arguments: list[Any] = []
        if direction:
            clauses.append("direction=?")
            arguments.append(str(direction))
        if unread_only:
            clauses.append("status='unread'")
        query = "SELECT * FROM local_messages"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        arguments.append(max(1, min(int(limit), 200)))
        with self._conn() as connection:
            rows = connection.execute(query, tuple(arguments)).fetchall()
        result: list[dict] = []
        for row in rows:
            item = dict(row)
            item["context"] = json.loads(item.pop("context_json") or "{}")
            result.append(item)
        return result

    def mark_read(self, message_ids: list[str]) -> int:
        ids = [str(value) for value in message_ids if str(value).strip()][:200]
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self._conn() as connection:
            cursor = connection.execute(
                f"""
                UPDATE local_messages SET status='read'
                WHERE direction='in' AND message_id IN ({placeholders})
                """,
                tuple(ids),
            )
            return int(cursor.rowcount)
