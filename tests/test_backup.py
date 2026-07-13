from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from seven import config
from seven.memory.store import Memory
from seven.runtime.backup import create_backup, restore_backup, verify_backup


def test_backup_verify_and_restore(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    monkeypatch.setattr(config, "DATA_DIR", source)
    monkeypatch.setattr(config, "DB_PATH", source / "seven.db")
    memory = Memory(source / "seven.db")
    memory.remember("backup survives", key="proof")
    (source / "living_state.json").write_text('{"awake": true}', encoding="utf-8")

    result = create_backup(destination=tmp_path / "backups", data_dir=source)
    archive = Path(result["path"])
    assert result["ok"] is True
    assert verify_backup(archive)["ok"] is True

    restored = tmp_path / "restored"
    restored.mkdir()
    monkeypatch.setattr(config, "DATA_DIR", restored)
    monkeypatch.setattr(config, "DB_PATH", restored / "seven.db")
    outcome = restore_backup(archive, data_dir=restored)
    assert outcome["ok"] is True
    assert Memory(restored / "seven.db").search_facts("backup survives")
    assert json.loads((restored / "living_state.json").read_text())["awake"] is True


def test_verify_detects_tampered_member(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("original", encoding="utf-8")
    result = create_backup(destination=tmp_path / "backups", data_dir=source)
    archive = type(source)(result["path"])
    rewritten = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive, "r") as source_zip, zipfile.ZipFile(rewritten, "w") as target_zip:
        for info in source_zip.infolist():
            data = source_zip.read(info.filename)
            target_zip.writestr(info, b"tampered" if info.filename == "data/a.txt" else data)
    archive = rewritten
    check = verify_backup(archive)
    assert check["ok"] is False
    assert any("mismatch" in error for error in check["errors"])


def test_restore_rejects_invalid_archive(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    with pytest.raises(ValueError, match="verification failed"):
        restore_backup(bad, data_dir=tmp_path / "restore")
