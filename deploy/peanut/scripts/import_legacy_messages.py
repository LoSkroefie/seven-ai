#!/usr/bin/env python3
"""Import legacy chat as provenance-tagged history, never as facts."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize(item: dict[str, Any], index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"invalid legacy message at position {index}")
    raw_role = str(
        item.get("role") or item.get("speaker") or item.get("sender") or ""
    ).strip().lower()
    roles = {
        "human": "user",
        "owner": "user",
        "user": "user",
        "seven": "assistant",
        "ai": "assistant",
        "bot": "assistant",
        "assistant": "assistant",
        "system": "system",
    }
    role = roles.get(raw_role)
    content = item.get("content")
    if content is None:
        content = item.get("message", item.get("text"))
    if not role or not isinstance(content, str) or not content.strip():
        raise ValueError(f"invalid legacy message at position {index}")
    return {
        "role": role,
        "content": content.strip(),
        "legacy_created_at": str(
            item.get("created_at") or item.get("timestamp") or item.get("time") or ""
        ),
        "legacy_index": index,
    }


def _extract_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("messages", "conversation", "conversations", "history", "chat"):
            if isinstance(value.get(key), list):
                return [item for item in value[key] if isinstance(item, dict)]
    raise ValueError("JSON source does not contain a message list")


def _load_sqlite(path: Path) -> list[dict[str, Any]]:
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        tables = [
            row[0]
            for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            if not str(row[0]).startswith("sqlite_")
        ]
        preferred = ("messages", "conversation_history", "chat_history", "conversations")
        tables.sort(key=lambda name: (name not in preferred, preferred.index(name) if name in preferred else name))
        for table in tables:
            columns = {
                row[1]
                for row in db.execute(f'PRAGMA table_info("{table.replace(chr(34), chr(34) * 2)}")')
            }
            role = next((name for name in ("role", "speaker", "sender") if name in columns), None)
            content = next(
                (name for name in ("content", "message", "text") if name in columns), None
            )
            if not role or not content:
                continue
            created = next(
                (name for name in ("created_at", "timestamp", "time") if name in columns),
                None,
            )
            selected = [role, content] + ([created] if created else [])
            escaped = '","'.join(name.replace('"', '""') for name in selected)
            rows = db.execute(
                f'SELECT "{escaped}" FROM "{table.replace(chr(34), chr(34) * 2)}" ORDER BY rowid'
            ).fetchall()
            return [
                {
                    "role": row[role],
                    "content": row[content],
                    "created_at": row[created] if created else "",
                }
                for row in rows
            ]
    raise ValueError("SQLite source has no recognizable message table")


def load_messages(path: Path) -> list[dict[str, Any]]:
    with path.open("rb") as stream:
        header = stream.read(16)
    if header.startswith(b"SQLite format 3"):
        raw = _load_sqlite(path)
    elif path.suffix.lower() == ".jsonl":
        raw = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
    else:
        raw = _extract_json(json.loads(path.read_text(encoding="utf-8-sig")))
    return [_normalize(item, index) for index, item in enumerate(raw, start=1)]


def import_messages(
    source: Path, target: Path, *, expected_count: int = 74, apply: bool = False
) -> dict[str, Any]:
    source = source.resolve()
    target = target.resolve()
    if source == target:
        raise ValueError("source and target must differ")
    messages = load_messages(source)
    if len(messages) != expected_count:
        raise ValueError(f"expected {expected_count} messages, found {len(messages)}")
    sha256 = _source_hash(source)
    report: dict[str, Any] = {
        "ok": True,
        "apply": apply,
        "source": source.name,
        "source_sha256": sha256,
        "message_count": len(messages),
        "classification": "history_only_not_facts",
    }
    if not apply:
        return report

    if target.exists():
        try:
            with sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True) as db:
                table = db.execute(
                    """SELECT 1 FROM sqlite_master
                       WHERE type='table' AND name='legacy_imports'"""
                ).fetchone()
                if table and db.execute(
                    "SELECT 1 FROM legacy_imports WHERE source_sha256=?", (sha256,)
                ).fetchone():
                    report["already_imported"] = True
                    return report
        except sqlite3.Error as exc:
            raise ValueError("target is not a readable SQLite database") from exc

    backup = None
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = target.with_name(f"{target.name}.before-legacy-{stamp}.bak")
        shutil.copy2(target, backup)
        report["backup"] = str(backup)

    from seven.memory.store import Memory

    memory = Memory(db_path=target)
    imported_at = _utcnow()
    with sqlite3.connect(str(target)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        if db.execute(
            "SELECT 1 FROM legacy_imports WHERE source_sha256=?", (sha256,)
        ).fetchone():
            report["already_imported"] = True
            return report
        for message in messages:
            meta = {
                "source": "legacy_history",
                "provenance": {
                    "source_file": source.name,
                    "source_sha256": sha256,
                    "legacy_index": message["legacy_index"],
                    "legacy_created_at": message["legacy_created_at"],
                    "classification": "history_not_fact",
                },
            }
            cur = db.execute(
                "INSERT INTO messages(role,content,meta,created_at) VALUES (?,?,?,?)",
                (
                    message["role"],
                    message["content"],
                    json.dumps(meta, ensure_ascii=False),
                    imported_at,
                ),
            )
            db.execute(
                """INSERT INTO events(event_type,actor,source,content,meta,created_at)
                   VALUES ('legacy_message',?,?,?,?,?)""",
                (
                    message["role"],
                    "legacy_history",
                    message["content"],
                    json.dumps({"message_id": int(cur.lastrowid), **meta}, ensure_ascii=False),
                    imported_at,
                ),
            )
        db.execute(
            """INSERT INTO legacy_imports(source_sha256,source_path,imported_at,report_json)
               VALUES (?,?,?,?)""",
            (sha256, source.name, imported_at, json.dumps(report, ensure_ascii=False)),
        )
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("target database failed integrity check")
    report["imported"] = len(messages)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target_db", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-count", type=int, default=74)
    args = parser.parse_args()
    try:
        report = import_messages(
            args.source,
            args.target_db,
            expected_count=args.expected_count,
            apply=args.apply,
        )
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
