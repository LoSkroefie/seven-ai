import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from seven.memory.store import Memory
from seven.runtime.backup import create_backup, restore_backup, verify_backup
from seven.runtime.memory_maintenance import apply_retention, migrate_legacy_memory
from seven.runtime.memory_ops import memory_check


def _legacy_db(path: Path):
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE conversations (
            id INTEGER PRIMARY KEY, session_id TEXT, started_at TEXT NOT NULL, ended_at TEXT,
            source TEXT, summary TEXT, topics TEXT, action_items TEXT, sentiment TEXT, mood TEXT
        );
        CREATE TABLE utterances (
            id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL, timestamp TEXT NOT NULL,
            speaker TEXT, text TEXT NOT NULL, source TEXT, confidence REAL, emotion TEXT
        );
    """)
    connection.execute("INSERT INTO conversations VALUES (1,'session','2025-01-01T00:00:00+00:00','2025-01-01T01:00:00+00:00','direct','A useful old conversation','[\"seven\"]','[\"call Sam\",\"call Sam\"]','positive','focused')")
    connection.execute("INSERT INTO conversations VALUES (2,NULL,'2025-01-02T00:00:00+00:00',NULL,'ambient',NULL,'[]','not-json',NULL,NULL)")
    connection.execute("INSERT INTO utterances VALUES (1,1,'2025-01-01T00:00:01+00:00','user','hello old Seven','direct',1.0,NULL)")
    connection.execute("INSERT INTO utterances VALUES (2,1,'2025-01-01T00:00:02+00:00','seven','hello Jan','direct',1.0,NULL)")
    connection.commit(); connection.close()


def test_legacy_migration_dry_run_apply_provenance_and_idempotence(tmp_path):
    source_dir, target_dir = tmp_path / "legacy", tmp_path / "current"
    source_dir.mkdir(); target_dir.mkdir()
    source, target = source_dir / "conversation.db", target_dir / "seven.db"
    _legacy_db(source)
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    dry = migrate_legacy_memory(source, target)
    assert dry["applied"] is False
    assert dry["new_messages"] == 2 and dry["new_summaries"] == 1
    assert dry["new_actions"] == 1 and dry["duplicate_actions"] == 1
    assert dry["malformed_action_lists"] == 1
    assert target.exists() is False

    applied = migrate_legacy_memory(source, target, apply=True, backup_dir=tmp_path / "backups")
    assert applied["applied"] is True
    assert verify_backup(Path(applied["backup"]))["ok"] is True
    memory = Memory(target)
    messages = memory.recent_messages()
    assert [(m["role"], m["content"]) for m in messages] == [("user", "hello old Seven"), ("assistant", "hello Jan")]
    assert messages[0]["meta"]["legacy_conversation_id"] == 1
    assert memory.search_facts("useful old conversation")[0]["source"] == "legacy-conversation"
    action = memory.list_action_items()[0]
    assert action["text"] == "call Sam" and action["source_kind"] == "legacy-conversation"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash

    repeated = migrate_legacy_memory(source, target, apply=True)
    assert repeated["already_imported"] is True and repeated["applied"] is False
    assert Memory(target).message_count() == 2


def test_retention_is_dry_run_first_backup_gated_and_selective(tmp_path):
    data = tmp_path / "data"; data.mkdir()
    db = data / "seven.db"
    memory = Memory(db)
    old = (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
    recent = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db) as connection:
        connection.execute("INSERT INTO messages(role,content,meta,created_at) VALUES ('user','old','{}',?)", (old,))
        connection.execute("INSERT INTO messages(role,content,meta,created_at) VALUES ('user','recent','{}',?)", (recent,))
        connection.execute("INSERT INTO facts(key,value,source,confidence,created_at,updated_at) VALUES ('keep','long term','test',1,?,?)", (old, old))
        connection.execute("INSERT INTO audit(tool,arguments,result_preview,ok,created_at) VALUES ('x','{}','x',1,?)", (old,))
        connection.execute("INSERT INTO tasks(title,status,created_at,updated_at) VALUES ('done old','done',?,?)", (old, old))
        connection.execute("INSERT INTO tasks(title,status,created_at,updated_at) VALUES ('open old','open',?,?)", (old, old))
        connection.execute("INSERT INTO action_items(fingerprint,text,status,created_at,updated_at) VALUES ('dismissed','dismissed','dismissed',?,?)", (old, old))
        connection.commit()

    before_dry = hashlib.sha256(db.read_bytes()).hexdigest()
    dry = apply_retention(30, target_db=db)
    assert dry["applied"] is False and dry["counts"]["messages"] == 1
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before_dry
    assert Memory(db).message_count() == 2
    result = apply_retention(30, target_db=db, apply=True, backup_dir=tmp_path / "backups")
    assert result["applied"] is True and verify_backup(Path(result["backup"]))["ok"] is True
    reopened = Memory(db)
    assert [m["content"] for m in reopened.recent_messages()] == ["recent"]
    assert reopened.search_facts("long term")
    assert [task["title"] for task in reopened.open_tasks()] == ["open old"]
    assert reopened.list_action_items("dismissed") == []


def test_corrupt_database_can_be_forensically_preserved_then_restored(tmp_path):
    data = tmp_path / "data"; data.mkdir()
    db = data / "seven.db"
    memory = Memory(db); memory.remember("survives corruption", key="proof")
    backup = Path(create_backup(destination=tmp_path / "backups", data_dir=data)["path"])
    db.write_bytes(b"definitely not sqlite")
    assert memory_check(db)["ok"] is False
    restored = restore_backup(backup, data_dir=data)
    safety = Path(restored["safety_backup"])
    check = verify_backup(safety)
    assert check["ok"] is True and check["manifest"]["format"] == "forensic-raw-1"
    assert Memory(db).search_facts("survives corruption")
