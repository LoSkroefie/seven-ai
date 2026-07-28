from __future__ import annotations

import json
import sqlite3

from scripts.import_legacy_messages import import_messages


def test_imports_74_as_history_with_provenance_and_is_idempotent(tmp_path):
    source = tmp_path / "legacy.json"
    source.write_text(
        json.dumps(
            {
                "messages": [
                    {
                        "role": "human" if index % 2 == 0 else "seven",
                        "content": f"legacy message {index}",
                        "timestamp": f"2024-01-01T00:{index:02d}:00Z",
                    }
                    for index in range(74)
                ]
            }
        ),
        encoding="utf-8",
    )
    target = tmp_path / "seven.sqlite3"

    dry = import_messages(source, target, apply=False)
    assert dry["message_count"] == 74
    assert dry["classification"] == "history_only_not_facts"
    assert not target.exists()

    applied = import_messages(source, target, apply=True)
    assert applied["imported"] == 74
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 74
        assert db.execute("SELECT count(*) FROM facts").fetchone()[0] == 0
        meta = json.loads(db.execute("SELECT meta FROM messages LIMIT 1").fetchone()[0])
        assert meta["source"] == "legacy_history"
        assert meta["provenance"]["classification"] == "history_not_fact"

    repeated = import_messages(source, target, apply=True)
    assert repeated["already_imported"] is True
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT count(*) FROM messages").fetchone()[0] == 74


def test_import_rejects_wrong_count_without_touching_target(tmp_path):
    source = tmp_path / "legacy.json"
    source.write_text(
        json.dumps([{"role": "user", "content": "only one"}]), encoding="utf-8"
    )
    target = tmp_path / "seven.sqlite3"
    try:
        import_messages(source, target, apply=True)
    except ValueError as exc:
        assert "expected 74" in str(exc)
    else:
        raise AssertionError("wrong count was accepted")
    assert not target.exists()

