import json

from seven.memory.store import Memory
from seven.runtime.memory_ops import export_memory, memory_check


def test_integrity_stats_and_schema_version(tmp_path):
    db = tmp_path / "seven.db"
    memory = Memory(db)
    memory.remember("truth", key="value")
    memory.add_task("do work")
    result = memory_check(db)
    assert result["ok"] is True
    assert result["schema_version"] == 4
    assert memory.schema_version() == 4
    assert result["tables"]["facts"] == 1
    assert result["tables"]["tasks"] == 1


def test_portable_export_excludes_audit_by_default(tmp_path):
    db = tmp_path / "seven.db"
    memory = Memory(db)
    memory.remember("export me", key="proof")
    memory.add_action_item("export this candidate")
    memory.audit("run_shell", {"command": "echo ok"}, "ok", True)
    destination = tmp_path / "memory.json"
    result = export_memory(destination, db)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert result["records"] >= 1
    assert payload["format"] == "seven-memory-export"
    assert payload["tables"]["facts"][0]["value"] == "export me"
    assert payload["tables"]["action_items"][0]["text"] == "export this candidate"
    assert "audit" not in payload["tables"]
    assert len(payload["source_database_sha256"]) == 64


def test_export_can_include_redacted_audit(tmp_path):
    db = tmp_path / "seven.db"
    memory = Memory(db)
    memory.audit("web", {"api_key": "secret-value"}, "token=secret-value", True)
    destination = tmp_path / "memory-with-audit.json"
    export_memory(destination, db, include_audit=True)
    text = destination.read_text(encoding="utf-8")
    assert "secret-value" not in text
    assert "[REDACTED]" in text


def test_invalid_database_is_reported(tmp_path):
    db = tmp_path / "bad.db"
    db.write_text("not sqlite", encoding="utf-8")
    result = memory_check(db)
    assert result["ok"] is False
    assert result["errors"]
