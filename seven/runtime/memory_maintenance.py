"""Dry-run-first legacy migration and backup-gated memory retention."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from seven import config
from seven.memory.store import Memory, _utcnow
from seven.runtime.backup import create_backup
from seven.runtime.memory_ops import memory_check

RETENTION_SCOPES = {
    "messages": ("messages", "created_at < ?"),
    "audit": ("audit", "created_at < ?"),
    "working_memory": ("working_memory", "created_at < ?"),
    "digests": ("digests", "created_at < ?"),
    "message_embeddings": ("embeddings", "ref_type='message' AND created_at < ?"),
    "completed_tasks": ("tasks", "status='done' AND updated_at < ?"),
    "dismissed_actions": ("action_items", "status='dismissed' AND updated_at < ?"),
}
DEFAULT_RETENTION_SCOPE = tuple(RETENTION_SCOPES)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _legacy_source(path: Path) -> tuple[sqlite3.Connection, dict[str, Any]]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"legacy database not found: {path}")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        connection.close()
        raise ValueError(f"legacy database integrity failed: {integrity}")
    columns = {
        table: {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
        for table in ("conversations", "utterances")
    }
    required = {
        "conversations": {"id", "started_at", "summary", "action_items"},
        "utterances": {"id", "conversation_id", "timestamp", "speaker", "text"},
    }
    missing = {table: sorted(names - columns[table]) for table, names in required.items() if names - columns[table]}
    if missing:
        connection.close()
        raise ValueError(f"not a supported v3 conversation database; missing columns: {missing}")
    return connection, {"path": str(path), "sha256": _sha256(path)}


def _parse_actions(raw: str | None) -> tuple[list[str], bool]:
    try:
        data = json.loads(raw or "[]")
        if not isinstance(data, list):
            return [], True
        return [str(item).strip() for item in data if str(item).strip()], False
    except (TypeError, json.JSONDecodeError):
        return [], True


def migrate_legacy_memory(source_db: Path, target_db: Path | None = None, apply: bool = False, backup_dir: Path | None = None) -> dict[str, Any]:
    target = Path(target_db or config.DB_PATH).expanduser().resolve()
    actual_target = target
    source = Path(source_db).expanduser().resolve()
    if source == target:
        raise ValueError("legacy source and current target must be different databases")
    source_conn, source_info = _legacy_source(source)
    scratch = None
    pre_backup = None
    if actual_target.exists():
        precheck = memory_check(actual_target)
        if not precheck["ok"]:
            source_conn.close()
            raise ValueError("target memory integrity failed: " + "; ".join(precheck["errors"]))
    if apply and actual_target.exists():
        pre_backup = create_backup(destination=backup_dir or actual_target.parent / "backups", data_dir=actual_target.parent)
    if not apply:
        scratch = tempfile.TemporaryDirectory(prefix="seven-migration-plan-")
        target = Path(scratch.name) / "seven.db"
        if actual_target.exists():
            with closing(sqlite3.connect(actual_target)) as source_target, closing(sqlite3.connect(target)) as planned_target:
                source_target.backup(planned_target)
    Memory(target)  # migrate only the scratch copy during dry-run
    target_check = memory_check(target)
    if not target_check["ok"]:
        source_conn.close()
        raise ValueError("target memory integrity failed: " + "; ".join(target_check["errors"]))
    report: dict[str, Any] = {
        "ok": True, "applied": False, "source": source_info, "target": str(actual_target),
        "already_imported": False, "conversations": 0, "utterances": 0,
        "new_messages": 0, "duplicate_messages": 0, "new_summaries": 0,
        "duplicate_summaries": 0, "new_actions": 0, "duplicate_actions": 0,
        "malformed_action_lists": 0, "backup": None,
    }
    try:
        with closing(sqlite3.connect(target)) as target_conn:
            target_conn.row_factory = sqlite3.Row
            imported = target_conn.execute("SELECT 1 FROM legacy_imports WHERE source_sha256=?", (source_info["sha256"],)).fetchone()
            if imported:
                report["already_imported"] = True
                return report
            conversations = source_conn.execute("SELECT * FROM conversations ORDER BY id").fetchall()
            utterances = source_conn.execute("SELECT * FROM utterances ORDER BY timestamp,id").fetchall()
            report["conversations"], report["utterances"] = len(conversations), len(utterances)
            conversation_map = {row["id"]: row for row in conversations}

            planned_messages = []
            for row in utterances:
                conversation = conversation_map.get(row["conversation_id"])
                speaker = (row["speaker"] or "unknown").strip().casefold()
                role = "assistant" if speaker in {"seven", "assistant", "bot"} else "user"
                meta = {
                    "migration": "v3-conversation-memory", "legacy_utterance_id": row["id"],
                    "legacy_conversation_id": row["conversation_id"], "legacy_speaker": row["speaker"],
                }
                if conversation is not None:
                    meta["legacy_source"] = conversation["source"] if "source" in conversation.keys() else None
                    meta["legacy_session_id"] = conversation["session_id"] if "session_id" in conversation.keys() else None
                duplicate = target_conn.execute(
                    "SELECT 1 FROM messages WHERE role=? AND content=? AND created_at=? LIMIT 1",
                    (role, row["text"], row["timestamp"]),
                ).fetchone()
                if duplicate:
                    report["duplicate_messages"] += 1
                else:
                    report["new_messages"] += 1
                    planned_messages.append((role, row["text"], json.dumps(meta), row["timestamp"]))

            planned_summaries, planned_actions = [], []
            for row in conversations:
                key = f"legacy.conversation.{source_info['sha256'][:12]}.{row['id']}"
                summary = (row["summary"] or "").strip()
                if summary:
                    duplicate = target_conn.execute("SELECT 1 FROM facts WHERE key=? LIMIT 1", (key,)).fetchone()
                    if duplicate:
                        report["duplicate_summaries"] += 1
                    else:
                        report["new_summaries"] += 1
                        details = {name: row[name] for name in ("summary", "topics", "sentiment", "mood", "source", "started_at", "ended_at") if name in row.keys()}
                        planned_summaries.append((key, json.dumps(details, ensure_ascii=False), row["started_at"] or _utcnow()))
                actions, malformed = _parse_actions(row["action_items"])
                report["malformed_action_lists"] += int(malformed)
                for text in actions:
                    fingerprint = Memory.action_fingerprint(text)
                    duplicate = target_conn.execute("SELECT 1 FROM action_items WHERE fingerprint=?", (fingerprint,)).fetchone()
                    if duplicate or any(item[0] == fingerprint for item in planned_actions):
                        report["duplicate_actions"] += 1
                    else:
                        report["new_actions"] += 1
                        planned_actions.append((fingerprint, text, f"{source_info['sha256']}:{row['id']}"))

            if not apply:
                return report
            backup = pre_backup or create_backup(destination=backup_dir or target.parent / "backups", data_dir=target.parent)
            report["backup"] = backup["path"]
            now = _utcnow()
            target_conn.execute("BEGIN IMMEDIATE")
            target_conn.executemany("INSERT INTO messages(role,content,meta,created_at) VALUES (?,?,?,?)", planned_messages)
            for key, value, created in planned_summaries:
                cursor = target_conn.execute(
                    "INSERT INTO facts(key,value,source,confidence,created_at,updated_at) VALUES (?,?,?,?,?,?)",
                    (key, value, "legacy-conversation", 0.8, created, now),
                )
                try:
                    target_conn.execute("INSERT INTO facts_fts(rowid,value,key) VALUES (?,?,?)", (cursor.lastrowid, value, key))
                except sqlite3.OperationalError:
                    pass
            target_conn.executemany(
                "INSERT INTO action_items(fingerprint,text,status,created_at,updated_at,source_kind,source_ref) VALUES (?,?,'pending',?,?, 'legacy-conversation',?)",
                [(fingerprint, text, now, now, source_ref) for fingerprint, text, source_ref in planned_actions],
            )
            final_report = {k: v for k, v in report.items() if k != "backup"}
            final_report["applied"] = True
            target_conn.execute(
                "INSERT INTO legacy_imports(source_sha256,source_path,imported_at,report_json) VALUES (?,?,?,?)",
                (source_info["sha256"], source_info["path"], now, json.dumps(final_report)),
            )
            target_conn.commit()
            report["applied"] = True
            return report
    finally:
        source_conn.close()
        if scratch is not None:
            scratch.cleanup()


def apply_retention(days: int, scopes: tuple[str, ...] = DEFAULT_RETENTION_SCOPE, target_db: Path | None = None, apply: bool = False, backup_dir: Path | None = None) -> dict[str, Any]:
    days = int(days)
    if days < 1:
        raise ValueError("retention days must be at least 1")
    unknown = sorted(set(scopes) - set(RETENTION_SCOPES))
    if unknown:
        raise ValueError(f"unknown retention scope(s): {', '.join(unknown)}")
    target = Path(target_db or config.DB_PATH).expanduser().resolve()
    actual_target = target
    if not actual_target.is_file():
        raise ValueError(f"target memory database not found: {actual_target}")
    precheck = memory_check(actual_target)
    if not precheck["ok"]:
        raise ValueError("target memory integrity failed: " + "; ".join(precheck["errors"]))
    scratch = None
    pre_backup = None
    if not apply:
        scratch = tempfile.TemporaryDirectory(prefix="seven-retention-plan-")
        target = Path(scratch.name) / "seven.db"
        with closing(sqlite3.connect(actual_target)) as source_target, closing(sqlite3.connect(target)) as planned_target:
            source_target.backup(planned_target)
    else:
        pre_backup = create_backup(destination=backup_dir or actual_target.parent / "backups", data_dir=actual_target.parent)
    Memory(target)  # migrate only scratch for dry-run; current DB after backup for apply
    check = memory_check(target)
    if not check["ok"]:
        raise ValueError("target memory integrity failed: " + "; ".join(check["errors"]))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    report = {"ok": True, "applied": False, "target": str(actual_target), "days": days, "cutoff": cutoff, "scopes": list(scopes), "counts": {}, "backup": None}
    try:
        with closing(sqlite3.connect(target)) as connection:
            for scope in scopes:
                table, predicate = RETENTION_SCOPES[scope]
                report["counts"][scope] = int(connection.execute(f'SELECT COUNT(*) FROM "{table}" WHERE {predicate}', (cutoff,)).fetchone()[0])
            if not apply:
                return report
            report["backup"] = pre_backup["path"]
            connection.execute("BEGIN IMMEDIATE")
            for scope in scopes:
                table, predicate = RETENTION_SCOPES[scope]
                connection.execute(f'DELETE FROM "{table}" WHERE {predicate}', (cutoff,))
            connection.commit()
        report["applied"] = True
        return report
    finally:
        if scratch is not None:
            scratch.cleanup()
