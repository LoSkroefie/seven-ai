"""Consistent, verifiable backup and offline restore for Seven data."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from seven import __version__, config


MANIFEST_NAME = "manifest.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return not p.is_absolute() and ".." not in p.parts


def create_backup(
    destination: Path | None = None,
    data_dir: Path | None = None,
    keep: int = 7,
) -> dict[str, Any]:
    data_dir = Path(data_dir or config.DATA_DIR).resolve()
    destination = Path(destination or (data_dir / "backups")).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = destination / f"seven-backup-{timestamp}.zip"

    with tempfile.TemporaryDirectory(prefix="seven-backup-") as temp_name:
        temp = Path(temp_name)
        stage = temp / "data"
        stage.mkdir()
        source_db = data_dir / config.DB_PATH.name
        if source_db.exists():
            target_db = stage / source_db.name
            with closing(sqlite3.connect(str(source_db))) as src:
                with closing(sqlite3.connect(str(target_db))) as dst:
                    src.backup(dst)
                    dst.commit()

        skipped_roots = {destination, data_dir / "backups"}
        for source in sorted(data_dir.rglob("*")):
            if not source.is_file() or source == source_db:
                continue
            resolved = source.resolve()
            if any(root == resolved or root in resolved.parents for root in skipped_roots):
                continue
            relative = source.relative_to(data_dir)
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        files = []
        for path in sorted(p for p in stage.rglob("*") if p.is_file()):
            relative = path.relative_to(stage).as_posix()
            files.append({"path": relative, "bytes": path.stat().st_size, "sha256": _sha256(path)})
        manifest = {
            "format": 1,
            "seven_version": __version__,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": files,
        }
        (temp / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            zf.write(temp / MANIFEST_NAME, MANIFEST_NAME)
            for item in files:
                zf.write(stage / item["path"], f"data/{item['path']}")

    verified = verify_backup(archive)
    if not verified["ok"]:
        archive.unlink(missing_ok=True)
        raise RuntimeError("created backup failed verification: " + "; ".join(verified["errors"]))
    backups = sorted(destination.glob("seven-backup-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[max(1, int(keep)):]:
        old.unlink(missing_ok=True)
    return {"ok": True, "path": str(archive), "files": len(files), "bytes": archive.stat().st_size}


def verify_backup(archive: Path) -> dict[str, Any]:
    archive = Path(archive).resolve()
    errors: list[str] = []
    try:
        with zipfile.ZipFile(archive, "r") as zf:
            bad = zf.testzip()
            if bad:
                errors.append(f"ZIP CRC failed: {bad}")
            names = set(zf.namelist())
            if MANIFEST_NAME not in names:
                return {"ok": False, "path": str(archive), "errors": ["manifest missing"]}
            manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
            for item in manifest.get("files", []):
                relative = item.get("path", "")
                member = f"data/{relative}"
                if not _safe_member(member) or member not in names:
                    errors.append(f"missing or unsafe member: {member}")
                    continue
                data = zf.read(member)
                if len(data) != item.get("bytes"):
                    errors.append(f"size mismatch: {relative}")
                if hashlib.sha256(data).hexdigest() != item.get("sha256"):
                    errors.append(f"hash mismatch: {relative}")
            return {"ok": not errors, "path": str(archive), "errors": errors, "manifest": manifest}
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        return {"ok": False, "path": str(archive), "errors": [str(exc)]}


def restore_backup(archive: Path, data_dir: Path | None = None) -> dict[str, Any]:
    """Restore a verified archive. Caller must ensure Seven is stopped."""
    archive = Path(archive).resolve()
    data_dir = Path(data_dir or config.DATA_DIR).resolve()
    check = verify_backup(archive)
    if not check["ok"]:
        raise ValueError("backup verification failed: " + "; ".join(check["errors"]))
    from seven.runtime.daemon import read_pid, is_pid_running
    pid = read_pid()
    if pid and is_pid_running(pid):
        raise RuntimeError(f"Seven daemon is running (pid={pid}); stop it before restore")
    safety = create_backup(destination=data_dir.parent / "seven-pre-restore-backups", data_dir=data_dir, keep=3)
    with tempfile.TemporaryDirectory(prefix="seven-restore-") as temp_name:
        temp = Path(temp_name)
        with zipfile.ZipFile(archive, "r") as zf:
            for name in zf.namelist():
                if not _safe_member(name):
                    raise ValueError(f"unsafe archive member: {name}")
            zf.extractall(temp)
        staged = temp / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(staged.rglob("*")):
            if source.is_file():
                target = data_dir / source.relative_to(staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    return {"ok": True, "restored_from": str(archive), "safety_backup": safety["path"]}
