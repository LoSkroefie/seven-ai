"""Integrity, statistics and portable export for Seven's SQLite memory."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from seven import __version__, config


EXPORT_TABLES = (
    "messages", "facts", "goals", "tasks", "notes", "beliefs",
    "working_memory", "skills", "plans", "embeddings", "digests", "preferences",
)


def memory_check(db_path: Path | None = None) -> dict[str, Any]:
    path = Path(db_path or config.DB_PATH).resolve()
    if not path.exists():
        return {"ok": False, "path": str(path), "errors": ["database not found"]}
    try:
        with closing(sqlite3.connect(str(path))) as conn:
            integrity = [row[0] for row in conn.execute("PRAGMA integrity_check").fetchall()]
            foreign_keys = [list(row) for row in conn.execute("PRAGMA foreign_key_check").fetchall()]
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            tables = {
                row[0]: int(conn.execute(f'SELECT COUNT(*) FROM "{row[0]}"').fetchone()[0])
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%_fts%' ORDER BY name")
            }
        errors = []
        if integrity != ["ok"]:
            errors.extend(integrity)
        if foreign_keys:
            errors.append(f"foreign key violations: {len(foreign_keys)}")
        return {
            "ok": not errors,
            "path": str(path),
            "bytes": path.stat().st_size,
            "schema_version": version,
            "integrity": integrity,
            "foreign_key_violations": foreign_keys,
            "tables": tables,
            "errors": errors,
        }
    except sqlite3.Error as exc:
        return {"ok": False, "path": str(path), "errors": [str(exc)]}


def export_memory(
    destination: Path,
    db_path: Path | None = None,
    include_audit: bool = False,
) -> dict[str, Any]:
    path = Path(db_path or config.DB_PATH).resolve()
    check = memory_check(path)
    if not check["ok"]:
        raise ValueError("memory integrity check failed: " + "; ".join(check["errors"]))
    tables = list(EXPORT_TABLES) + (["audit"] if include_audit else [])
    data: dict[str, list[dict[str, Any]]] = {}
    with closing(sqlite3.connect(str(path))) as conn:
        conn.row_factory = sqlite3.Row
        existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in tables:
            data[table] = [dict(row) for row in conn.execute(f'SELECT * FROM "{table}" ORDER BY rowid')] if table in existing else []
    payload = {
        "format": "seven-memory-export",
        "format_version": 1,
        "seven_version": __version__,
        "schema_version": check["schema_version"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_database_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "audit_included": include_audit,
        "tables": data,
    }
    destination = Path(destination).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "path": str(destination),
        "bytes": destination.stat().st_size,
        "records": sum(len(rows) for rows in data.values()),
        "audit_included": include_audit,
    }
